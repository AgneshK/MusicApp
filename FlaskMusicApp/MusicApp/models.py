from MusicApp import bcrypt
from MusicApp import db, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=128), nullable=False)
    role = db.Column(db.String(length=15), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_flagged = db.Column(db.Boolean(), default=False)
    flag_reason = db.Column(db.String(length=255), nullable=True)

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)


class Song(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    lyrics = db.Column(db.Text, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String(20), nullable=False)
    artist_name = db.Column(db.String(100), nullable=False)
    audio_link = db.Column(db.String(255), nullable=True)
    poster = db.Column(db.String(255), nullable=True)
    average_rating = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    ratings = db.relationship('Rating', backref='song', cascade='all, delete-orphan')
    creator = db.relationship('User', backref='songs')

    def calculate_average_rating(self):
        ratings = Rating.query.filter_by(song_id=self.id).all()
        total_ratings = sum(r.value for r in ratings)
        num_ratings = len(ratings)
        if num_ratings > 0:
            self.average_rating = round(total_ratings / num_ratings, 2)
        else:
            self.average_rating = 0


    def __repr__(self):
        return f"Song('{self.title}', '{self.genre}', '{self.creator.username}', '{self.artist_name}')"


songs_playlists = db.Table('songs_playlists',
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True),
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True)
)

class Playlist(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='playlists')

    songs = db.relationship('Song', secondary=songs_playlists, backref=db.backref('playlists', lazy='dynamic'))

    def __repr__(self):
        return f"Playlist('{self.name}', '{self.user.username}')"

    def add_song(self, song):
        if song not in self.songs:
            self.songs.append(song)
            db.session.commit()

    def remove_song(self, song):
        if song in self.songs:
            self.songs.remove(song)
            db.session.commit()


class Album(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    genre = db.Column(db.String(20), nullable=False)
    poster = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref='albums')

    songs = db.relationship('Song', secondary='album_songs', backref=db.backref('albums', lazy='dynamic'))

    def __repr__(self):
        return f"Album('{self.title}', '{self.creator.username}')"

    def add_song(self, song):
        if song not in self.songs:
            self.songs.append(song)
            db.session.commit()

    def disassociate_deleted_song(self, deleted_song_id):
        self.songs = [song for song in self.songs if song.id != deleted_song_id]
        db.session.commit()


album_songs = db.Table('album_songs',
    db.Column('album_id', db.Integer, db.ForeignKey('album.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True)
)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Rating('{self.value}', '{self.song.title}', '{self.user.username}')"