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
    hobbies = TextAreaField('Hobbies or Interests', validators=[DataRequired()],
                            render_kw={"placeholder": "What do you like or like to do? List some activities or interests. Ex: new-wave music, origami, paint, meditate"})
    personality = TextAreaField('Personality', validators=[DataRequired(), Length(max=200)], render_kw={
        "placeholder": "What are you like as a person? List some adjectives, what you think would be on your tombstone, or how your friends would describe you."})


class EventForm(FlaskForm):
    event = TextAreaField('Event', validators=[DataRequired(), Length(max=100)], render_kw={
        "placeholder": "What is the event that should happen? Ex: winning the lottery, crippling medical debt"})

