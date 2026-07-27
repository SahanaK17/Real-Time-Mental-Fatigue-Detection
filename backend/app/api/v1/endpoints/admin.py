"""Admin API — User management, reports, high risk monitoring."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
import io
import csv
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta, timezone

from app.core.dependencies import get_current_user, require_admin
from app.db.models import User, FatiguePrediction, TrackerSession
from app.db.session import get_db

router = APIRouter()


@router.get("/users", summary="[Admin] List all users")
async def list_all_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar()

    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role.value,
                "department": u.department,
                "is_active": u.is_active,
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
    }


@router.get("/high-risk", summary="[Admin] Get users with high recent fatigue scores")
async def get_high_risk_users(
    threshold: float = Query(default=0.75, ge=0, le=1),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    result = await db.execute(
        select(
            FatiguePrediction.user_id,
            func.avg(FatiguePrediction.fatigue_score).label("avg_score"),
            func.max(FatiguePrediction.fatigue_score).label("max_score"),
            func.count(FatiguePrediction.id).label("count"),
        )
        .where(FatiguePrediction.predicted_at >= cutoff)
        .group_by(FatiguePrediction.user_id)
        .having(func.avg(FatiguePrediction.fatigue_score) >= threshold)
        .order_by(desc("avg_score"))
    )
    rows = result.all()

    # Get user details
    high_risk = []
    for row in rows:
        user_result = await db.execute(select(User).where(User.id == row.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            high_risk.append(
                {
                    "user_id": str(row.user_id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "department": user.department,
                    "avg_fatigue_score": round(float(row.avg_score), 3),
                    "max_fatigue_score": round(float(row.max_score), 3),
                    "prediction_count": int(row.count),
                }
            )

    return {"threshold": threshold, "high_risk_users": high_risk}


@router.get("/stats", summary="[Admin] Platform-wide statistics")
async def get_admin_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    today = now - timedelta(hours=24)

    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    active_sessions = (
        await db.execute(
            select(func.count(TrackerSession.id)).where(TrackerSession.status == "active")
        )
    ).scalar()
    predictions_today = (
        await db.execute(
            select(func.count(FatiguePrediction.id)).where(FatiguePrediction.predicted_at >= today)
        )
    ).scalar()
    avg_score_today = (
        await db.execute(
            select(func.avg(FatiguePrediction.fatigue_score)).where(
                FatiguePrediction.predicted_at >= today
            )
        )
    ).scalar()

    return {
        "total_users": total_users,
        "active_sessions": active_sessions,
        "predictions_last_24h": predictions_today,
        "avg_fatigue_score_last_24h": round(float(avg_score_today or 0), 3),
    }


@router.get("/export/csv", summary="[Admin] Export recent predictions as CSV")
async def export_csv(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # Fetch last 1000 predictions for the export
    result = await db.execute(
        select(FatiguePrediction, User.email)
        .join(User, User.id == FatiguePrediction.user_id)
        .order_by(FatiguePrediction.predicted_at.desc())
        .limit(1000)
    )
    rows = result.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "User Email", "Fatigue Score", "Fatigue Level"])

    for row in rows:
        pred = row.FatiguePrediction
        writer.writerow(
            [
                pred.predicted_at.isoformat(),
                row.email,
                round(pred.fatigue_score, 4),
                pred.fatigue_level.value,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=fatigue_export_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
        },
    )


@router.get("/export/pdf", summary="[Admin] Export admin stats as PDF")
async def export_pdf(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    # Get stats
    now = datetime.now(timezone.utc)
    today = now - timedelta(hours=24)
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    predictions_today = (
        await db.execute(
            select(func.count(FatiguePrediction.id)).where(FatiguePrediction.predicted_at >= today)
        )
    ).scalar()
    avg_score_today = (
        await db.execute(
            select(func.avg(FatiguePrediction.fatigue_score)).where(
                FatiguePrediction.predicted_at >= today
            )
        )
    ).scalar()

    output = io.BytesIO()
    p = canvas.Canvas(output, pagesize=letter)
    width, height = letter

    # Title
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, "MindGuard - Admin Report")

    # Date
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 70, f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # Stats
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 110, "Platform Overview (Last 24 Hours)")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 130, f"Total Users: {total_users}")
    p.drawString(50, height - 150, f"Predictions Made: {predictions_today}")
    p.drawString(
        50, height - 170, f"Average Fatigue Score: {round(float(avg_score_today or 0), 3)}"
    )

    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, 50, "This report was auto-generated by the MindGuard system.")

    p.showPage()
    p.save()
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=admin_report_{now.strftime('%Y%m%d')}.pdf"
        },
    )
