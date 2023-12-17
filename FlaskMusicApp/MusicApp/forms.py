from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, IntegerField, FileField, \
    SelectMultipleField, widgets, FieldList, FormField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length, URL, InputRequired
from MusicApp.models import User

class SignupForm(FlaskForm):

    def validate_username(self, username_to_check):
        user = User.query.filter_by(username=username_to_check.data).first()
        if user:
            raise ValidationError('User already exists! Please try a different Username')

    username = StringField('Username', validators = [Length(min=3, max=30), DataRequired()])
    role = SelectField('Role', choices=[('creator', 'Creator'), ('user', 'User')], validators=[DataRequired()])
    pwd1 = PasswordField('Password', validators= [Length(min=6, max = 60), DataRequired()])
    pwd2 = PasswordField('Confirm Password',
                         validators=[DataRequired(), EqualTo('pwd1', message='Passwords must match')])
    submit = SubmitField(label='Create Account')

class LoginForm(FlaskForm):
    username = StringField(label='User Name:', validators=[DataRequired()])
    password = PasswordField(label='Password:', validators=[DataRequired()])
    submit = SubmitField(label='Login')

class SongForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    lyrics = TextAreaField('Lyrics', validators=[DataRequired()])
    duration = IntegerField('Duration (seconds)', validators=[DataRequired()])
    genre = SelectField('Genre', choices=[
        ('Rock', 'rock'),
        ('Pop', 'pop'),
        ('Hip Hop', 'hip hop'),
        ('Electronic/Dance', 'electronic dance'),
        ('Jazz', 'jazz'),
    ], validators=[DataRequired()])
    artist_name = StringField('Artist Name', validators=[DataRequired(), Length(min=3, max=100)])
    audio_link = FileField('Audio Link', validators=[FileAllowed(['mp3'], 'MP3 Files only!')])
    poster = StringField('Poster', validators=[URL(), Length(max=5000)])

    submit = SubmitField('Add Song')

class PlaylistForm(FlaskForm):
    name = StringField('Playlist Name', validators=[DataRequired()])
    songs = SelectMultipleField('Songs', choices=[], coerce=int, widget=widgets.ListWidget(prefix_label=False), option_widget=widgets.CheckboxInput())
    submit = SubmitField('Create Playlist')


class AlbumForm(FlaskForm):
    title = StringField('Album Title', validators=[InputRequired()])
    description = TextAreaField('Description')
    genre = SelectField('Genre', choices=[
        ('Rock', 'rock'),
        ('Pop', 'pop'),
        ('Hip Hop', 'hip hop'),
        ('Electronic/Dance', 'electronic/dance'),
        ('Jazz', 'jazz'),
        ('Mixed', 'mixed')
    ], validators=[InputRequired()])
    poster = StringField('Poster', validators=[URL(), Length(max=5000)])
    songs = SelectMultipleField('Select Songs', coerce=int, widget=widgets.ListWidget(prefix_label=False), option_widget=widgets.CheckboxInput())

class RatingForm(FlaskForm):
    rating = SelectField('Rating', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')],
                         validators=[InputRequired()])
    submit = SubmitField('Submit Rating')


class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')