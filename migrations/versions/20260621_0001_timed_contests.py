"""Add timed contests, difficulty, and execution metadata.

Revision ID: 20260621_0001
Revises:
Create Date: 2026-06-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from backend.database import Base
from backend import model  # noqa: F401

revision: str = "20260621_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(inspector, table: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)
    inspector = sa.inspect(bind)

    difficulty_enum = sa.Enum("EASY", "MEDIUM", "HARD", name="difficulty")
    submission_kind_enum = sa.Enum("RUN", "SUBMIT", name="submissionkind")
    difficulty_enum.create(bind, checkfirst=True)
    submission_kind_enum.create(bind, checkfirst=True)

    if "difficulty" not in _columns(inspector, "questions"):
        with op.batch_alter_table("questions") as batch:
            batch.add_column(
                sa.Column(
                    "difficulty",
                    difficulty_enum,
                    nullable=False,
                    server_default="EASY",
                )
            )

    inspector = sa.inspect(bind)
    if "expires_at" not in _columns(inspector, "attempts"):
        with op.batch_alter_table("attempts") as batch:
            batch.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        if bind.dialect.name == "postgresql":
            op.execute(
                """
                UPDATE attempts
                SET expires_at = attempts.started_at
                    + (tests.duration || ' minutes')::interval
                FROM tests
                WHERE tests.id = attempts.test_id
                """
            )
        else:
            op.execute(
                """
                UPDATE attempts
                SET expires_at = datetime(
                    started_at,
                    '+' || (
                        SELECT duration FROM tests WHERE tests.id = attempts.test_id
                    ) || ' minutes'
                )
                """
            )
        with op.batch_alter_table("attempts") as batch:
            batch.alter_column("expires_at", existing_type=sa.DateTime(timezone=True), nullable=False)

    inspector = sa.inspect(bind)
    attempt_constraints = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("attempts")
    }
    if "uq_attempt_user_test" not in attempt_constraints:
        with op.batch_alter_table("attempts") as batch:
            batch.create_unique_constraint(
                "uq_attempt_user_test",
                ["user_id", "test_id"],
            )

    inspector = sa.inspect(bind)
    submission_columns = _columns(inspector, "submissions")
    with op.batch_alter_table("submissions") as batch:
        if "kind" not in submission_columns:
            batch.add_column(
                sa.Column(
                    "kind",
                    submission_kind_enum,
                    nullable=False,
                    server_default="SUBMIT",
                )
            )
        if "attempt_id" not in submission_columns:
            batch.add_column(sa.Column("attempt_id", sa.Integer(), nullable=True))

    inspector = sa.inspect(bind)
    foreign_keys = {
        fk["name"]
        for fk in inspector.get_foreign_keys("submissions")
        if fk["name"]
    }
    if "fk_submissions_attempt_id_attempts" not in foreign_keys:
        with op.batch_alter_table("submissions") as batch:
            batch.create_foreign_key(
                "fk_submissions_attempt_id_attempts",
                "attempts",
                ["attempt_id"],
                ["id"],
                ondelete="SET NULL",
            )


def downgrade() -> None:
    with op.batch_alter_table("submissions") as batch:
        batch.drop_constraint(
            "fk_submissions_attempt_id_attempts",
            type_="foreignkey",
        )
        batch.drop_column("attempt_id")
        batch.drop_column("kind")
    with op.batch_alter_table("attempts") as batch:
        batch.drop_constraint("uq_attempt_user_test", type_="unique")
        batch.drop_column("expires_at")
    with op.batch_alter_table("questions") as batch:
        batch.drop_column("difficulty")
