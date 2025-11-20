"""Initial schema with all tables and pg_trgm extension

Revision ID: 001
Revises: 
Create Date: 2025-11-20 10:51:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pg_trgm extension for trigram-based full-text search
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('department', sa.String(100)),
        sa.Column('preferences', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_department', 'users', ['department'])
    op.create_index('idx_users_role', 'users', ['role'])
    
    # Create regulations table
    op.create_table(
        'regulations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.Text, nullable=False),
        sa.Column('jurisdiction', sa.String(50), nullable=False),
        sa.Column('authority', sa.String(255)),
        sa.Column('effective_date', sa.Date),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('full_text', sa.Text),
        sa.Column('content_hash', sa.String(64)),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('idx_regulations_jurisdiction', 'regulations', ['jurisdiction'])
    op.create_index('idx_regulations_effective_date', 'regulations', [sa.text('effective_date DESC')])
    op.create_index('idx_regulations_status', 'regulations', ['status'])
    # Create GIN index for trigram search on title
    op.execute('CREATE INDEX idx_regulations_title_search ON regulations USING gin (title gin_trgm_ops)')
    
    # Create sections table
    op.create_table(
        'sections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('regulation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('section_number', sa.String(50)),
        sa.Column('title', sa.Text),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['regulation_id'], ['regulations.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_sections_regulation', 'sections', ['regulation_id'])
    op.create_index('idx_sections_number', 'sections', ['section_number'])
    # Create GIN index for trigram search on content
    op.execute('CREATE INDEX idx_sections_content_search ON sections USING gin (content gin_trgm_ops)')
    
    # Create citations table
    op.create_table(
        'citations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cited_section_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('citation_text', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cited_section_id'], ['sections.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_citations_section', 'citations', ['section_id'])
    op.create_index('idx_citations_cited', 'citations', ['cited_section_id'])
    
    # Create amendments table
    op.create_table(
        'amendments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('regulation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amendment_type', sa.String(50), nullable=False),
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['regulation_id'], ['regulations.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_amendments_regulation', 'amendments', ['regulation_id'])
    op.create_index('idx_amendments_effective_date', 'amendments', [sa.text('effective_date DESC')])
    
    # Create query_history table
    op.create_table(
        'query_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query', sa.Text, nullable=False),
        sa.Column('entities', postgresql.JSONB),
        sa.Column('intent', sa.String(50)),
        sa.Column('results', postgresql.JSONB),
        sa.Column('rating', sa.Integer),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )
    op.create_index('idx_query_history_user_date', 'query_history', ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_query_history_intent', 'query_history', ['intent'])
    op.create_index('idx_query_history_created_at', 'query_history', ['created_at'])
    
    # Create workflow_sessions table
    op.create_table(
        'workflow_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('workflow_type', sa.String(100), nullable=False),
        sa.Column('state', postgresql.JSONB, server_default='{}'),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_workflow_sessions_user_date', 'workflow_sessions', ['user_id', sa.text('started_at DESC')])
    op.create_index('idx_workflow_sessions_status', 'workflow_sessions', ['status'])
    op.create_index('idx_workflow_sessions_started_at', 'workflow_sessions', ['started_at'])
    
    # Create workflow_steps table
    op.create_table(
        'workflow_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_number', sa.Integer, nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('input_data', postgresql.JSONB),
        sa.Column('validation_result', postgresql.JSONB),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['session_id'], ['workflow_sessions.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_workflow_steps_session', 'workflow_steps', ['session_id', 'step_number'])
    
    # Create alert_subscriptions table
    op.create_table(
        'alert_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('jurisdiction', sa.String(50)),
        sa.Column('topics', postgresql.JSONB, server_default='[]'),
        sa.Column('frequency', sa.String(20), server_default='daily'),
        sa.Column('active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_alert_subscriptions_user', 'alert_subscriptions', ['user_id'])
    op.create_index('idx_alert_subscriptions_active', 'alert_subscriptions', ['active'])
    op.create_index('idx_alert_subscriptions_jurisdiction', 'alert_subscriptions', ['jurisdiction'])
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('change_type', sa.String(50), nullable=False),
        sa.Column('regulation_id', postgresql.UUID(as_uuid=True)),
        sa.Column('summary', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('read', sa.Boolean, server_default='false'),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.ForeignKeyConstraint(['subscription_id'], ['alert_subscriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['regulation_id'], ['regulations.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_alerts_subscription_read_date', 'alerts', ['subscription_id', 'read', sa.text('created_at DESC')])
    op.create_index('idx_alerts_created_at', 'alerts', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('alerts')
    op.drop_table('alert_subscriptions')
    op.drop_table('workflow_steps')
    op.drop_table('workflow_sessions')
    op.drop_table('query_history')
    op.drop_table('amendments')
    op.drop_table('citations')
    op.drop_table('sections')
    op.drop_table('regulations')
    op.drop_table('users')
    
    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS pg_trgm')
