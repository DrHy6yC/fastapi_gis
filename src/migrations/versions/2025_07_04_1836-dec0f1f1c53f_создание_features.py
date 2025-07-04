"""Создание features

Revision ID: dec0f1f1c53f
Revises: 
Create Date: 2025-07-04 18:36:15.216403

"""
from typing import Sequence, Union

import geoalchemy2
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dec0f1f1c53f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('features',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('feature', geoalchemy2.types.Geometry(srid=4326, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_features_feature', table_name='features', postgresql_using='gist')
    op.drop_table('features')
