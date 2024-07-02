from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange


class CharacterForm(FlaskForm):
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=120)],
                       render_kw={"placeholder": "What is your age?"})
    occupation = StringField('Occupation', validators=[DataRequired(), Length(max=100)],
                             render_kw={"placeholder": "What do you do for work? Ex: Late-stage mafia boss"})
    location = StringField('Location', validators=[DataRequired(), Length(max=100)],
                           render_kw={"placeholder": "What region or city are you living in? Ex: the fun part of Iowa"})
    hobbies = TextAreaField('Interests or Hobbies', validators=[DataRequired()],
                            render_kw={
                                "placeholder": "What do you like or like to do? List some interests or activities. Ex: hiking, painting, reading, yoga, cooking, traveling, photography, playing guitar, gardening, running, baking, watching movies"})
    personality = TextAreaField('Personality', validators=[DataRequired(), Length(max=200)], render_kw={
        "placeholder": "What are you like as a person? Think of how your friends would describe you or some adjectives you identify with. Possible adjectives: introverted/extroverted, organized/disorganized, anxious/calm, open-minded/closed-minded, agreeable/disagreeable"
    })


class EventForm(FlaskForm):
    event = TextAreaField('Event', validators=[DataRequired(), Length(max=100)], render_kw={
        "placeholder": "What is the event that should happen? Ex: winning the lottery, crippling medical debt"})

