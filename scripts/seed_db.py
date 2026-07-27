"""
Database Seed Script
====================
Creates default admin + demo employee users.
Run ONCE after first docker-compose up:

    python scripts/seed_db.py

Or from inside Docker:
    docker exec -it mf_backend_dev python /app/scripts/seed_db.py
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SEED_USERS = [
    {
        "email": "admin@mindguard.io",
        "username": "admin",
        "full_name": "Platform Admin",
        "password": "Admin@123!",
        "role": "admin",
        "department": "IT",
        "job_title": "System Administrator",
        "is_verified": True,
    },
    {
        "email": "alice@mindguard.io",
        "username": "alice",
        "full_name": "Alice Johnson",
        "password": "Employee@123!",
        "role": "employee",
        "department": "Engineering",
        "job_title": "Senior Software Engineer",
        "is_verified": True,
    },
    {
        "email": "bob@mindguard.io",
        "username": "bob",
        "full_name": "Bob Smith",
        "password": "Employee@123!",
        "role": "employee",
        "department": "Product",
        "job_title": "Product Manager",
        "is_verified": True,
    },
    {
        "email": "researcher@mindguard.io",
        "username": "researcher",
        "full_name": "Dr. Research",
        "password": "Research@123!",
        "role": "researcher",
        "department": "R&D",
        "job_title": "Research Scientist",
        "is_verified": True,
    },
]


async def seed():
    """Seed the database with default users."""
    import asyncpg
    from dotenv import load_dotenv

    load_dotenv(".env")

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://mf_user:mf_dev_password@localhost:5432/mental_fatigue_db_dev",
    )

    # Convert async URL format
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    try:
        conn = await asyncpg.connect(db_url)
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print(
            "   Make sure Docker containers are running: docker-compose -f docker-compose.dev.yml up -d"
        )
        return

    print("\n🌱 Seeding database...\n")

    for user_data in SEED_USERS:
        hashed_pw = pwd_context.hash(user_data["password"])
        try:
            await conn.execute(
                """
                INSERT INTO users (id, email, username, full_name, hashed_password,
                                   role, department, job_title, is_active, is_verified,
                                   notification_preferences, fatigue_threshold, timezone,
                                   created_at, updated_at)
                VALUES (
                    gen_random_uuid(), $1, $2, $3, $4,
                    $5, $6, $7, TRUE, $8,
                    '{}'::jsonb, 0.7, 'UTC',
                    NOW(), NOW()
                )
                ON CONFLICT (email) DO UPDATE SET
                    hashed_password = EXCLUDED.hashed_password,
                    is_active = TRUE
                """,
                user_data["email"],
                user_data["username"],
                user_data["full_name"],
                hashed_pw,
                user_data["role"],
                user_data.get("department"),
                user_data.get("job_title"),
                user_data.get("is_verified", False),
            )
            print(
                f"  ✅ {user_data['role'].upper():12} {user_data['email']} / {user_data['password']}"
            )
        except Exception as e:
            print(f"  ❌ Failed to insert {user_data['email']}: {e}")

    await conn.close()

    print("\n🎉 Seeding complete!\n")
    print("Login credentials:")
    print("─" * 50)
    for u in SEED_USERS:
        print(f"  {u['role'].upper():12} {u['email']}")
        print(f"  {'':12} password: {u['password']}\n")


if __name__ == "__main__":
    asyncio.run(seed())
