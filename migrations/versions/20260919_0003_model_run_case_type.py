"""Allow the official Case 2 evaluation identifier in model runs.

Revision ID: 20260919_0003
Revises: 20260919_0002
"""

import sqlalchemy as sa
from alembic import op

revision = "20260919_0003"
down_revision = "20260919_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_model_runs_case_executed", table_name="model_runs")
    with op.batch_alter_table("model_runs") as batch:
        batch.alter_column(
            "case_type", existing_type=sa.String(24), type_=sa.String(32),
            existing_nullable=False,
        )
    op.create_index(
        "ix_model_runs_case_executed", "model_runs", ["case_type", "executed_at"]
    )


def downgrade() -> None:
    raise RuntimeError("Downgrade no automatizado; verificar longitud de case_type")
