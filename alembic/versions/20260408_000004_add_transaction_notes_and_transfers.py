"""add transaction notes and transfers"""

from alembic import op
import sqlalchemy as sa


revision = "20260408_000004"
down_revision = "20260408_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("destination_wallet_id", sa.Integer(), nullable=True))
    op.add_column("transactions", sa.Column("note", sa.String(length=255), nullable=True))
    op.create_foreign_key(
        "fk_transactions_destination_wallet_id_wallets",
        "transactions",
        "wallets",
        ["destination_wallet_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_transactions_destination_wallet_id_wallets", "transactions", type_="foreignkey")
    op.drop_column("transactions", "note")
    op.drop_column("transactions", "destination_wallet_id")
