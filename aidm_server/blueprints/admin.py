# aidm_server/blueprints/admin.py

from flask import request, flash, redirect, url_for, current_app
from flask_admin import Admin, BaseView, expose
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_admin.contrib.sqla import ModelView

from aidm_server.database import db, graph_db
from aidm_server.models import (
    World,
    Campaign,
    Player,
    Session,
    Npc,
    PlayerAction,
    Map,
    SessionLogEntry,
    CampaignSegment,
    StoryEvent
)

class CampaignModelView(ModelView):
    pass

class PlayerModelView(ModelView):
    pass

class NpcModelView(ModelView):
    form_columns = ['world', 'name', 'role', 'backstory']

    form_ajax_refs = {
        'world': {
            'fields': ['name'],  # which columns to search
        }
    }

    def after_model_change(self, form, model, is_created):
        """Handle changes to NPC models including graph database updates."""
        super().after_model_change(form, model, is_created)
        # Get graph_db from app context
        graph_db = current_app.graph_db
        if not graph_db:
            current_app.logger.error("Graph database not available")
            return

        try:
            graph_db.create_npc_node(
                npc_id=model.npc_id,
                name=model.name,
                role=model.role
            )
        except Exception as e:
            current_app.logger.error(f"Failed to create NPC node in graph: {str(e)}")
            # Optionally, you could raise the error if you want to prevent the SQL transaction
            # raise

class SessionLogEntryModelView(ModelView):
    pass

class StoryEventModelView(ModelView):
    pass

class GraphAdminView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/graph_index.html')

    @expose('/create_relationship', methods=['GET', 'POST'])
    def create_relationship_view(self):
        if request.method == 'POST':
            start_npc_id = request.form.get('start_npc_id')
            end_npc_id = request.form.get('end_npc_id')
            rel_type = request.form.get('rel_type', 'ALLY_OF')
            try:
                start_npc_id = int(start_npc_id)
                end_npc_id = int(end_npc_id)
                graph_db.create_relationship(
                    start_label='NPC',
                    start_key=start_npc_id,
                    end_label='NPC',
                    end_key=end_npc_id,
                    rel_type=rel_type
                )
                flash(
                    f"Created '{rel_type}' relationship between NPC {start_npc_id} and NPC {end_npc_id}.",
                    'success'
                )
                return redirect(url_for('.index'))
            except Exception as e:
                flash(f"Error: {str(e)}", 'error')

        return self.render('admin/create_relationship.html')

def configure_admin(app, db):
    # Initialize graph_db reference in app
    if not hasattr(app, 'graph_db'):
        from aidm_server.database import init_graph_db
        app.graph_db = init_graph_db(app)

    admin = Admin(app, name="AI-DM Admin", template_mode="bootstrap3")

    admin.add_view(ModelView(World, db.session))
    admin.add_view(CampaignModelView(Campaign, db.session))
    admin.add_view(PlayerModelView(Player, db.session))
    admin.add_view(ModelView(Session, db.session))

    # Use our custom NpcModelView
    admin.add_view(NpcModelView(Npc, db.session))

    admin.add_view(ModelView(PlayerAction, db.session))
    admin.add_view(ModelView(Map, db.session))
    admin.add_view(SessionLogEntryModelView(SessionLogEntry, db.session))
    admin.add_view(ModelView(CampaignSegment, db.session))
    admin.add_view(StoryEventModelView(StoryEvent, db.session))
    admin.add_view(GraphAdminView(name="Graph Admin", endpoint="graphadmin"))

    return admin
