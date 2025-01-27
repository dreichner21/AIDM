# admin.py (within configure_admin)
from aidm_server.models import (
    World, Campaign, Player, Session, Npc, PlayerAction,
    Map, SessionLogEntry, CampaignSegment, StoryEvent
)
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

class CampaignModelView(ModelView):
    pass

class PlayerModelView(ModelView):
    pass

class NpcModelView(ModelView):
    pass

class SessionLogEntryModelView(ModelView):
    pass

class StoryEventModelView(ModelView):
    pass

def configure_admin(app, db):
    admin = Admin(app, name="AI-DM Admin", template_mode="bootstrap3")
    admin.add_view(ModelView(World, db.session))
    admin.add_view(CampaignModelView(Campaign, db.session))
    admin.add_view(PlayerModelView(Player, db.session))
    admin.add_view(ModelView(Session, db.session))
    admin.add_view(NpcModelView(Npc, db.session))
    admin.add_view(ModelView(PlayerAction, db.session))
    admin.add_view(ModelView(Map, db.session))
    admin.add_view(SessionLogEntryModelView(SessionLogEntry, db.session))

    # NEW:
    admin.add_view(ModelView(CampaignSegment, db.session))
    admin.add_view(StoryEventModelView(StoryEvent, db.session))

    return admin
