"""add_unique_constraint_template_name_account_id

Revision ID: 61dcd652e3c9
Revises: 76a71b6596e4
Create Date: 2025-07-15 19:08:17.016246

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61dcd652e3c9'
down_revision: Union[str, None] = '76a71b6596e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # First, handle any existing duplicate template names per account
    connection = op.get_bind()
    
    # Find and rename duplicates before adding the constraint
    duplicates = connection.execute(sa.text("""
        SELECT name, account_id, COUNT(*) as count
        FROM templates 
        WHERE account_id IS NOT NULL
        GROUP BY name, account_id 
        HAVING COUNT(*) > 1
    """)).fetchall()
    
    # Rename duplicates by appending a number
    for row in duplicates:
        name, account_id, count = row
        # Get all templates with this name and account
        templates = connection.execute(sa.text("""
            SELECT id, name FROM templates 
            WHERE name = :name AND account_id = :account_id
            ORDER BY id
        """), {'name': name, 'account_id': account_id}).fetchall()
        
        # Rename all but the first one
        for i, template in enumerate(templates[1:], 2):
            new_name = f"{name} ({i})"
            connection.execute(sa.text("""
                UPDATE templates 
                SET name = :new_name 
                WHERE id = :template_id
            """), {'new_name': new_name, 'template_id': template[0]})
    
    # Now add the unique constraint
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_template_name_account_id', ['name', 'account_id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.drop_constraint('uq_template_name_account_id', type_='unique') 