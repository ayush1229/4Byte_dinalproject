# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, validators
from wtforms.validators import DataRequired

class VoterForm(FlaskForm):
    voter_id = StringField('Voter ID', [
        validators.DataRequired(),
        validators.Length(min=6, max=20)
    ])
    session_id = IntegerField('Session ID', [
        validators.DataRequired()
    ])
    option = StringField('Option', [
        validators.DataRequired()
    ])