"""rename class_ to character_class

Revision ID: 4168f75087e2
Revises: 3617eb2511b0
Create Date: 2025-01-29 17:15:06.747022

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4168f75087e2'
down_revision = '3617eb2511b0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('player_actions')
    op.drop_table('maps')
    op.drop_table('campaigns')
    op.drop_table('players')
    op.drop_table('campaign_segments')
    op.drop_table('worlds')
    op.drop_table('story_events')
    op.drop_table('npcs')
    op.drop_table('sessions')
    op.drop_table('session_log_entries')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('session_log_entries',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('session_id', sa.INTEGER(), nullable=False),
    sa.Column('message', sa.TEXT(), nullable=False),
    sa.Column('entry_type', sa.VARCHAR(), nullable=False),
    sa.Column('timestamp', sa.DATETIME(), nullable=True),
    sa.Column('structured_output', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['sessions.session_id'], name='fk_session_log_entries_session_id_sessions'),
    sa.PrimaryKeyConstraint('id', name='pk_session_log_entries')
    )
    op.create_table('sessions',
    sa.Column('session_id', sa.INTEGER(), nullable=False),
    sa.Column('campaign_id', sa.INTEGER(), nullable=False),
    sa.Column('state_snapshot', sa.TEXT(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.campaign_id'], name='fk_sessions_campaign_id_campaigns'),
    sa.PrimaryKeyConstraint('session_id', name='pk_sessions')
    )
    op.create_table('npcs',
    sa.Column('npc_id', sa.INTEGER(), nullable=False),
    sa.Column('world_id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=False),
    sa.Column('role', sa.VARCHAR(), nullable=True),
    sa.Column('backstory', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['world_id'], ['worlds.world_id'], name='fk_npcs_world_id_worlds'),
    sa.PrimaryKeyConstraint('npc_id', name='pk_npcs')
    )
    op.create_table('story_events',
    sa.Column('event_id', sa.INTEGER(), nullable=False),
    sa.Column('campaign_id', sa.INTEGER(), nullable=True),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('importance', sa.INTEGER(), nullable=True),
    sa.Column('resolved', sa.BOOLEAN(), nullable=True),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.campaign_id'], name='fk_story_events_campaign_id_campaigns'),
    sa.PrimaryKeyConstraint('event_id', name='pk_story_events')
    )
    op.create_table('worlds',
    sa.Column('world_id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=False),
    sa.Column('description', sa.VARCHAR(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('world_id', name='pk_worlds')
    )
    op.create_table('campaign_segments',
    sa.Column('segment_id', sa.INTEGER(), nullable=False),
    sa.Column('campaign_id', sa.INTEGER(), nullable=False),
    sa.Column('title', sa.VARCHAR(), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('trigger_condition', sa.TEXT(), nullable=True),
    sa.Column('tags', sa.TEXT(), nullable=True),
    sa.Column('is_triggered', sa.BOOLEAN(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.campaign_id'], name='fk_campaign_segments_campaign_id_campaigns'),
    sa.PrimaryKeyConstraint('segment_id', name='pk_campaign_segments')
    )
    op.create_table('players',
    sa.Column('player_id', sa.INTEGER(), nullable=False),
    sa.Column('campaign_id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=False),
    sa.Column('character_name', sa.VARCHAR(), nullable=False),
    sa.Column('race', sa.VARCHAR(), nullable=True),
    sa.Column('class_', sa.VARCHAR(), nullable=True),
    sa.Column('level', sa.INTEGER(), nullable=True),
    sa.Column('stats', sa.TEXT(), nullable=True),
    sa.Column('inventory', sa.TEXT(), nullable=True),
    sa.Column('character_sheet', sa.TEXT(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.campaign_id'], name='fk_players_campaign_id_campaigns'),
    sa.PrimaryKeyConstraint('player_id', name='pk_players')
    )
    op.create_table('campaigns',
    sa.Column('campaign_id', sa.INTEGER(), nullable=False),
    sa.Column('title', sa.VARCHAR(), nullable=False),
    sa.Column('description', sa.VARCHAR(), nullable=True),
    sa.Column('world_id', sa.INTEGER(), nullable=False),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('current_quest', sa.VARCHAR(), nullable=True),
    sa.Column('plot_points', sa.TEXT(), nullable=True),
    sa.Column('active_npcs', sa.TEXT(), nullable=True),
    sa.Column('location', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['world_id'], ['worlds.world_id'], name='fk_campaigns_world_id_worlds'),
    sa.PrimaryKeyConstraint('campaign_id', name='pk_campaigns')
    )
    op.create_table('maps',
    sa.Column('map_id', sa.INTEGER(), nullable=False),
    sa.Column('world_id', sa.INTEGER(), nullable=True),
    sa.Column('campaign_id', sa.INTEGER(), nullable=True),
    sa.Column('title', sa.VARCHAR(), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('map_data', sa.TEXT(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.campaign_id'], name='fk_maps_campaign_id_campaigns'),
    sa.ForeignKeyConstraint(['world_id'], ['worlds.world_id'], name='fk_maps_world_id_worlds'),
    sa.PrimaryKeyConstraint('map_id', name='pk_maps')
    )
    op.create_table('player_actions',
    sa.Column('action_id', sa.INTEGER(), nullable=False),
    sa.Column('player_id', sa.INTEGER(), nullable=False),
    sa.Column('session_id', sa.INTEGER(), nullable=False),
    sa.Column('action_text', sa.TEXT(), nullable=False),
    sa.Column('timestamp', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['players.player_id'], name='fk_player_actions_player_id_players'),
    sa.ForeignKeyConstraint(['session_id'], ['sessions.session_id'], name='fk_player_actions_session_id_sessions'),
    sa.PrimaryKeyConstraint('action_id', name='pk_player_actions')
    )
    # ### end Alembic commands ###
