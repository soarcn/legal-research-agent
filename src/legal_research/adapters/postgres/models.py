from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative metadata registry.

    P1 verifies database connectivity and Alembic operation only. Domain tables
    are introduced in P2 after their identity and provenance contracts are accepted.
    """

    pass
