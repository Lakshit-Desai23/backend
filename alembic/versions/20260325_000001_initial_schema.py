"""initial schema"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("mobile", sa.String(length=20), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_mobile", "users", ["mobile"], unique=True)

    op.create_table(
        "families",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index("ix_families_id", "families", ["id"])

    op.create_table(
        "family_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("family_id", sa.Integer(), sa.ForeignKey("families.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.UniqueConstraint("family_id", "user_id", name="uq_family_member"),
    )
    op.create_index("ix_family_members_id", "family_members", ["id"])

    op.create_table(
        "wallets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("family_id", sa.Integer(), sa.ForeignKey("families.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("balance", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.create_index("ix_wallets_id", "wallets", ["id"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("wallet_id", sa.Integer(), sa.ForeignKey("wallets.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_transactions_id", "transactions", ["id"])

    op.create_table(
        "limits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("daily_limit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("monthly_limit", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.create_index("ix_limits_id", "limits", ["id"])


def downgrade() -> None:
    op.drop_index("ix_limits_id", table_name="limits")
    op.drop_table("limits")
    op.drop_index("ix_transactions_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_wallets_id", table_name="wallets")
    op.drop_table("wallets")
    op.drop_index("ix_family_members_id", table_name="family_members")
    op.drop_table("family_members")
    op.drop_index("ix_families_id", table_name="families")
    op.drop_table("families")
    op.drop_index("ix_users_mobile", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
