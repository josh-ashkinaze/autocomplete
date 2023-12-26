from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange
class CharacterForm(FlaskForm):
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=120)], render_kw={"placeholder": "What is your age?"})
    occupation = StringField('Occupation', validators=[DataRequired(), Length(max=100)], render_kw={"placeholder": "What do you do for work?"})
    location = StringField('Location', validators=[DataRequired(), Length(max=100)],render_kw={"placeholder": "What region or city are you living in?"})
    hobbies = TextAreaField('Hobbies', validators=[DataRequired()], render_kw={"placeholder": "What do you like to do? List some activities"})
    personality = TextAreaField('Personality', validators=[DataRequired(), Length(max=200)], render_kw={"placeholder": "How would you describe yourself? For example, list three adjectives. "})

class EventForm(FlaskForm):
    event = StringField('Event', validators=[DataRequired(), Length(max=100)],render_kw={"placeholder": "What is the event that should happen? E.g.: Unchecked climate change, winning the lottery, etc."})
