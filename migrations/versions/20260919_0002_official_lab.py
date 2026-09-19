"""Contratos oficiales del laboratorio simulado.

Revision ID: 20260919_0002
Revises: 20260918_0001
"""

import sqlalchemy as sa
from alembic import op

revision = "20260919_0002"
down_revision = "20260918_0001"
branch_labels = None
depends_on = None

CHECKS = {
    "processing_batches": [
        ("ck_batches_case_official", "case_type IN ('CASE1_OFFICIAL', 'CASE2')"),
        ("ck_batches_status", "status IN ('RUNNING', 'COMPLETED', 'FAILED')"),
    ],
    "financial_assessments": [
        ("ck_assessments_risk", "risk_level IN ('BAJO', 'MEDIO', 'ALTO')"),
        ("ck_assessments_recommendation", "recommendation IN ('APROBAR', 'EVALUAR', 'RECHAZAR')"),
        ("ck_assessments_review_official", "review_status IN ('PENDIENTE', 'REVISADA')"),
    ],
    "complaints": [(
        "ck_complaints_golden_official", "golden_label IN ('FRAUDE', 'SERVICIO', 'PRODUCTO')"
    )],
    "complaint_predictions": [
        ("ck_predictions_category_official", "category IN ('FRAUDE', 'SERVICIO', 'PRODUCTO')"),
        ("ck_predictions_review_official", "review_status IN ('PENDIENTE', 'REVISADA')"),
    ],
}


def _replace_checks() -> None:
    dialect = op.get_bind().dialect.name
    for table, checks in CHECKS.items():
        if dialect == "mssql":
            # La revisión inicial creó checks sin nombre explícito.
            op.execute(sa.text(f"""
                DECLARE @sql nvarchar(max) = N'';
                SELECT @sql += N'ALTER TABLE dbo.{table} DROP CONSTRAINT [' + cc.name + N'];'
                FROM sys.check_constraints cc
                WHERE cc.parent_object_id = OBJECT_ID(N'dbo.{table}');
                EXEC sp_executesql @sql;
            """))
            for name, condition in checks:
                op.create_check_constraint(name, table, condition)
        elif dialect == "sqlite":
            # Batch mode recrea la tabla; los checks anónimos de 0001 no se copian.
            with op.batch_alter_table(table, recreate="always",
                                      table_args=[sa.CheckConstraint(condition, name=name)
                                                  for name, condition in checks]):
                pass
        else:
            raise RuntimeError(f"Migración no preparada para dialecto: {dialect}")


def upgrade() -> None:
    for name in ("prompt_versions", "kyc_result", "scoring_result", "xai_result"):
        op.add_column("financial_assessments", sa.Column(name, sa.JSON(), nullable=False,
                                                         server_default="{}"))
    op.add_column("financial_assessments", sa.Column("reference_score", sa.Integer()))
    op.add_column("financial_assessments", sa.Column("scoring_discrepancy", sa.Boolean(),
                                                     nullable=False, server_default=sa.false()))
    op.add_column("financial_assessments", sa.Column("kyc_reference", sa.String(16)))
    op.add_column("financial_assessments", sa.Column("kyc_discrepancy", sa.Boolean(),
                                                     nullable=False, server_default=sa.false()))
    op.add_column("complaints", sa.Column("difficulty", sa.String(16), nullable=False,
                                         server_default="FACIL"))
    op.add_column("complaint_predictions", sa.Column("case_id", sa.String(64), nullable=False,
                                                      server_default=""))
    for name, column in (
        ("priority", sa.String(8)), ("summary", sa.Text()),
        ("secondary_category", sa.String(16)),
    ):
        default = "MEDIA" if name == "priority" else "NINGUNA" if name == "secondary_category" else ""
        op.add_column("complaint_predictions", sa.Column(name, column, nullable=False,
                                                          server_default=default))
    for name in ("ambiguity_detected", "requires_human_review"):
        op.add_column("complaint_predictions", sa.Column(name, sa.Boolean(), nullable=False,
                                                          server_default=sa.false()))
    op.add_column("complaint_predictions", sa.Column("response_prompt_version", sa.String(32)))
    op.add_column("complaint_predictions", sa.Column("human_category_correction", sa.String(16)))
    _replace_checks()


def downgrade() -> None:
    raise RuntimeError("Downgrade de datos oficiales no automatizado; restaurar respaldo")
