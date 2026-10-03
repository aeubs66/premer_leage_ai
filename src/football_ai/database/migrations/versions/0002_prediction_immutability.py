"""Enforce saved-forecast immutability even for direct SQL updates/deletes."""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        for action in ["UPDATE", "DELETE"]:
            op.execute(
                f"CREATE TRIGGER predictions_no_{action.lower()} BEFORE {action} ON predictions BEGIN SELECT RAISE(ABORT, 'Saved predictions are immutable'); END"
            )
    elif dialect == "postgresql":
        op.execute(
            "CREATE FUNCTION protect_predictions() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Saved predictions are immutable'; END; $$"
        )
        op.execute(
            "CREATE TRIGGER predictions_immutable BEFORE UPDATE OR DELETE ON predictions FOR EACH ROW EXECUTE FUNCTION protect_predictions()"
        )


def downgrade():
    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        op.execute("DROP TRIGGER predictions_no_update")
        op.execute("DROP TRIGGER predictions_no_delete")
    elif dialect == "postgresql":
        op.execute("DROP TRIGGER predictions_immutable ON predictions")
        op.execute("DROP FUNCTION protect_predictions()")
