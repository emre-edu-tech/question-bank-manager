"""rename level 5 badge to Efsane

Revision ID: b7d21c4a9f03
Revises: c49bc6f1871a
Create Date: 2026-10-27 10:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b7d21c4a9f03'
down_revision = 'c49bc6f1871a'
branch_labels = None
depends_on = None


def upgrade():
    # Students already see level 5 as "Efsane"; the badge name follows it.
    # The code stays "seviye-5" because it describes the trigger, not the name.
    op.execute(
        "UPDATE badge SET "
        "name = 'Efsane', "
        "description = '500 deneyim puanı toplayarak en üst seviyeye ulaştın' "
        "WHERE code = 'seviye-5'"
    )


def downgrade():
    op.execute(
        "UPDATE badge SET "
        "name = 'Seviye 5', "
        "description = 'Efsane seviyesine ulaştın' "
        "WHERE code = 'seviye-5'"
    )
