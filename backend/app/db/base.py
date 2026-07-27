"""
SQLAlchemy Declarative Base
============================
All models must import from here to share the same metadata.
"""

from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """
    Shared declarative base for all SQLAlchemy models.
    Automatically derives __tablename__ from class name.
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Auto-generate lowercase table names from class names."""
        import re

        # Convert CamelCase to snake_case
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return name
