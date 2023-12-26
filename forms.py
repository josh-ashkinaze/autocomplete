from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
class CharacterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=120)])
    gender = StringField('Gender', validators=[DataRequired(), Length(max=50)])
    occupation = StringField('Occupation', validators=[DataRequired(), Length(max=100)])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    hobbies = StringField('Hobbies', validators=[DataRequired()])
    personality = StringField('Personality', validators=[DataRequired(), Length(max=200)])

class EventForm(FlaskForm):
    event_name = StringField('Event Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Create Event')