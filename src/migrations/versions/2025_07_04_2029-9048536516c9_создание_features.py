"""Создание features

Revision ID: 9048536516c9
Revises: 
Create Date: 2025-07-04 20:29:13.105381

"""
from typing import Sequence, Union

import geoalchemy2
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9048536516c9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('features',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_index(
        'idx_features_geometry',
        table_name='features',
        postgresql_using='gist'
    )
    op.create_index('idx_features_geometry', 'features', ['geometry'], unique=False, postgresql_using='gist')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_features_geometry', table_name='features', postgresql_using='gist')
    op.drop_table('features')
