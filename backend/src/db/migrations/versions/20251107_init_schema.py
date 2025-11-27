"""init_schema

Revision ID: 20251107_init_schema
Revises:
Create Date: 2025-11-07 21:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251107_init_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("email", sa.String(120), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- simulations ---
    op.create_table(
        "simulations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("command", sa.String(500), nullable=False),
        sa.Column("tickers", sa.JSON(), nullable=False),
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column("sides", sa.JSON(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("cagr", sa.Float(), nullable=True),
        sa.Column("sharpe", sa.Float(), nullable=True),
        sa.Column("max_drawdown", sa.Float(), nullable=True),
        sa.Column("portfolio_value", sa.JSON(), nullable=False),
        sa.Column("daily_returns", sa.JSON(), nullable=False),
        sa.Column("cumulative_returns", sa.JSON(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- refresh_tokens ---
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(256), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- asset ---
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ticker", sa.String(16), nullable=False, index=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.Float(), nullable=True),
        sa.Column("high", sa.Float(), nullable=True),
        sa.Column("low", sa.Float(), nullable=True),
        sa.Column("close", sa.Float(), nullable=True),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("inserted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("ticker", "date", name="uq_assets_ticker_date"),
    )

    # Indexes
    op.create_index("ix_assets_ticker_date", "assets", ["ticker", "date"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_simulations_user_id", "simulations", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_assets_ticker_date", table_name="assets")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_simulations_user_id", table_name="simulations")

    op.drop_table("assets")
    op.drop_table("refresh_tokens")
    op.drop_table("simulations")
    op.drop_table("users")
