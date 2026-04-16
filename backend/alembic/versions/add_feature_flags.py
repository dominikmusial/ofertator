"""add feature flags

Revision ID: add_feature_flags
Revises: m1_marketplace_specific_prompts
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_feature_flags'
down_revision = 'm1_marketplace_specific_prompts'
branch_labels = None
depends_on = None


def upgrade():
    # Insert default feature flags into system_config
    # All flags default to 'true' to maintain current behavior
    op.execute("""
        INSERT INTO system_config (config_key, config_value, description)
        VALUES 
            ('feature.marketplace.allegro.enabled', 'true', 'Enable/disable Allegro marketplace'),
            ('feature.marketplace.decathlon.enabled', 'true', 'Enable/disable Decathlon marketplace'),
            ('feature.marketplace.castorama.enabled', 'true', 'Enable/disable Castorama marketplace'),
            ('feature.marketplace.leroymerlin.enabled', 'true', 'Enable/disable Leroy Merlin marketplace'),
            ('feature.auth.registration.enabled', 'true', 'Enable/disable public registration'),
            ('feature.auth.google_sso.enabled', 'true', 'Enable/disable Google SSO login'),
            ('feature.admin.ai_config.enabled', 'true', 'Enable/disable AI Configuration admin page'),
            ('feature.admin.team_analytics.enabled', 'true', 'Enable/disable Team Analytics page'),
            ('feature.modules.ai_usage.enabled', 'true', 'Enable/disable AI Usage tracking module'),
            ('feature.user.ai_config.enabled', 'true', 'Enable/disable user AI Configuration in profile')
        ON CONFLICT (config_key) DO NOTHING
    """)


def downgrade():
    # Remove feature flags
    op.execute("""
        DELETE FROM system_config 
        WHERE config_key IN (
            'feature.marketplace.allegro.enabled',
            'feature.marketplace.decathlon.enabled',
            'feature.marketplace.castorama.enabled',
            'feature.marketplace.leroymerlin.enabled',
            'feature.auth.registration.enabled',
            'feature.auth.google_sso.enabled',
            'feature.admin.ai_config.enabled',
            'feature.admin.team_analytics.enabled',
            'feature.modules.ai_usage.enabled',
            'feature.user.ai_config.enabled'
        )
    """)
