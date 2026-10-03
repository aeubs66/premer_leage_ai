"""Initial portable schema. Definitions are frozen here, independent of live models."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("teams", sa.Column("name", sa.String(120), primary_key=True))
    op.create_table(
        "players",
        sa.Column("id", sa.String(120), primary_key=True),
        sa.Column("team", sa.String(120), sa.ForeignKey("teams.name")),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "matches",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("season", sa.String(16)),
        sa.Column("kickoff", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20)),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_matches_season", "matches", ["season"])
    op.create_index("ix_matches_kickoff", "matches", ["kickoff"])
    op.create_table(
        "fixtures",
        sa.Column("id", sa.String(64), sa.ForeignKey("matches.id"), primary_key=True),
        sa.Column("kickoff", sa.DateTime(timezone=True)),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_fixtures_kickoff", "fixtures", ["kickoff"])
    op.create_table(
        "team_match_stats",
        sa.Column("match_id", sa.String(64), sa.ForeignKey("matches.id"), primary_key=True),
        sa.Column("team", sa.String(120), sa.ForeignKey("teams.name"), primary_key=True),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "player_match_stats",
        sa.Column("match_id", sa.String(64), sa.ForeignKey("matches.id"), primary_key=True),
        sa.Column("player_id", sa.String(120), sa.ForeignKey("players.id"), primary_key=True),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "injuries",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("team", sa.String(120), sa.ForeignKey("teams.name")),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "observations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "elo_history",
        sa.Column("match_id", sa.String(64), sa.ForeignKey("matches.id"), primary_key=True),
        sa.Column("team", sa.String(120), sa.ForeignKey("teams.name"), primary_key=True),
        sa.Column("feature_version", sa.String(64), primary_key=True),
        sa.Column("rating", sa.Float(), nullable=False),
    )
    op.create_table(
        "features",
        sa.Column("match_id", sa.String(64), sa.ForeignKey("matches.id"), primary_key=True),
        sa.Column("dataset_version", sa.String(64), primary_key=True),
        sa.Column("feature_version", sa.String(64), primary_key=True),
        sa.Column("cutoff", sa.DateTime(timezone=True)),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "model_versions",
        sa.Column("version", sa.String(64), primary_key=True),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "experiments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "data_sources",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "predictions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("match_id", sa.String(64), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column(
            "model_version", sa.String(64), sa.ForeignKey("model_versions.version"), nullable=False
        ),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kickoff", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.CheckConstraint("generated_at < kickoff", name="ck_prediction_pre_kickoff"),
    )
    op.create_index("ix_predictions_match_id", "predictions", ["match_id"])
    op.create_table(
        "prediction_results",
        sa.Column(
            "prediction_id", sa.String(64), sa.ForeignKey("predictions.id"), primary_key=True
        ),
        sa.Column("actual", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )


def downgrade():
    for table in [
        "prediction_results",
        "predictions",
        "data_sources",
        "experiments",
        "model_versions",
        "features",
        "elo_history",
        "observations",
        "injuries",
        "player_match_stats",
        "team_match_stats",
        "fixtures",
        "matches",
        "players",
        "teams",
    ]:
        op.drop_table(table)
