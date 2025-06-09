"""delete fk to project from chats table

Revision ID: 123ff54f1956
Revises: 300cabfe1bb4
Create Date: 2025-06-09 20:00:26.966680

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "123ff54f1956"
down_revision: Union[str, None] = "300cabfe1bb4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("chats_project_id_fkey", "chats", type_="foreignkey")


def downgrade() -> None:
    op.create_foreign_key(
        "chats_project_id_fkey", "chats", "projects", ["project_id"], ["uuid"]
    )
