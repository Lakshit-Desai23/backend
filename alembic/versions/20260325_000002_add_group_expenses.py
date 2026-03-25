"""add group expenses and settlements"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_000002"
down_revision = "20260325_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index("ix_groups_id", "groups", ["id"])

    op.create_table(
        "group_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_member"),
    )
    op.create_index("ix_group_members_id", "group_members", ["id"])

    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("paid_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("split_type", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_expenses_id", "expenses", ["id"])

    op.create_table(
        "expense_splits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("expense_id", sa.Integer(), sa.ForeignKey("expenses.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("share_amount", sa.Numeric(12, 2), nullable=False),
        sa.UniqueConstraint("expense_id", "user_id", name="uq_expense_split"),
    )
    op.create_index("ix_expense_splits_id", "expense_splits", ["id"])

    op.create_table(
        "settlement_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("from_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("to_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_settlement_payments_id", "settlement_payments", ["id"])


def downgrade() -> None:
    op.drop_index("ix_settlement_payments_id", table_name="settlement_payments")
    op.drop_table("settlement_payments")
    op.drop_index("ix_expense_splits_id", table_name="expense_splits")
    op.drop_table("expense_splits")
    op.drop_index("ix_expenses_id", table_name="expenses")
    op.drop_table("expenses")
    op.drop_index("ix_group_members_id", table_name="group_members")
    op.drop_table("group_members")
    op.drop_index("ix_groups_id", table_name="groups")
    op.drop_table("groups")
