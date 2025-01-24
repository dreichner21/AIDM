# admin.py

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms import validators
from wtforms.validators import DataRequired, Optional
from flask_admin.form import Select2Field

from aidm_server.database import db
from aidm_server.models import World, Campaign, Player, Session, Npc, PlayerAction

class PlayerModelView(ModelView):
    form_columns = (
        'campaign_id', 'name', 'character_name', 'race', 'class_',
        'level', 'stats', 'inventory', 'character_sheet'
    )
    column_list = (
        'campaign_id', 'name', 'character_name', 'race', 'class_',
        'level'
    )

    def create_form(self):
        form = super(PlayerModelView, self).create_form()
        form.race = Select2Field('Race', choices=[
            ('', 'Select Race'),
            ('Human', 'Human'),
            ('Elf', 'Elf'),
            ('Dwarf', 'Dwarf'),
            ('Halfling', 'Halfling'),
            ('Dragonborn', 'Dragonborn'),
            ('Tiefling', 'Tiefling'),
            ('Half-Elf', 'Half-Elf'),
            ('Half-Orc', 'Half-Orc'),
            ('Gnome', 'Gnome')
        ], validators=[DataRequired()])

        form.class_ = Select2Field('Class', choices=[
            ('', 'Select Class'),
            ('Fighter', 'Fighter'),
            ('Wizard', 'Wizard'),
            ('Cleric', 'Cleric'),
            ('Rogue', 'Rogue'),
            ('Ranger', 'Ranger'),
            ('Paladin', 'Paladin'),
            ('Barbarian', 'Barbarian'),
            ('Bard', 'Bard'),
            ('Druid', 'Druid'),
            ('Monk', 'Monk'),
            ('Sorcerer', 'Sorcerer'),
            ('Warlock', 'Warlock')
        ], validators=[DataRequired()])
        return form

    form_args = {
        'campaign_id': {
            'label': 'Campaign',
            'validators': [DataRequired()]
        },
        'name': {
            'label': 'Player Name',
            'validators': [DataRequired()]
        },
        'character_name': {
            'label': 'Character Name',
            'validators': [DataRequired()]
        },
        'level': {
            'default': 1,
            'validators': [Optional()]
        }
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            if not model.stats:
                model.stats = '{}'
            if not model.inventory:
                model.inventory = '[]'
            if not model.character_sheet:
                model.character_sheet = '{}'
            if not model.level:
                model.level = 1

class NpcModelView(ModelView):
    form_columns = ('world_id', 'name', 'role', 'backstory')
    column_list = ('world_id', 'name', 'role')
    
    def create_form(self):
        form = super(NpcModelView, self).create_form()
        form.role = Select2Field('Role', choices=[
            ('', 'Select Role'),
            ('Merchant', 'Merchant'),
            ('Guard', 'Guard'),
            ('Noble', 'Noble'),
            ('Innkeeper', 'Innkeeper'),
            ('Wizard', 'Wizard'),
            ('Priest', 'Priest'),
            ('Blacksmith', 'Blacksmith'),
            ('Farmer', 'Farmer'),
            ('Soldier', 'Soldier'),
            ('Other', 'Other')
        ], validators=[Optional()])
        return form
    
    form_args = {
        'world_id': {
            'label': 'World',
            'validators': [DataRequired()]
        },
        'name': {
            'label': 'NPC Name',
            'validators': [DataRequired()]
        },
        'backstory': {
            'label': 'Backstory',
            'validators': [Optional()]
        }
    }

    def on_model_change(self, form, model, is_created):
        if is_created and not model.backstory:
            model.backstory = ''

class CampaignModelView(ModelView):
    form_columns = (
        'title', 'description', 'world_id', 'current_quest',
        'location', 'plot_points', 'active_npcs'
    )
    column_list = ('title', 'world_id', 'current_quest', 'location')
    
    def on_model_change(self, form, model, is_created):
        if is_created:
            if not model.plot_points:
                model.plot_points = '[]'
            if not model.active_npcs:
                model.active_npcs = '[]'
            if not model.current_quest:
                model.current_quest = ''
            if not model.location:
                model.location = ''

def configure_admin(app, db):
    admin = Admin(app, name="AI-DM Admin", template_mode="bootstrap3")
    admin.add_view(ModelView(World, db.session))
    admin.add_view(CampaignModelView(Campaign, db.session))
    admin.add_view(PlayerModelView(Player, db.session))
    admin.add_view(ModelView(Session, db.session))
    admin.add_view(NpcModelView(Npc, db.session))
    admin.add_view(ModelView(PlayerAction, db.session))
    return admin