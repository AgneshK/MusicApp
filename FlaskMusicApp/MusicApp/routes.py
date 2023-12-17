from werkzeug.utils import secure_filename
from MusicApp import app
from flask import render_template, redirect, url_for, flash, request
from MusicApp.forms import SignupForm, LoginForm, SongForm, PlaylistForm, AlbumForm, RatingForm, AdminLoginForm
from MusicApp.models import User, Song, Playlist, Album, Rating
from MusicApp import db
from flask_login import login_user, logout_user, login_required, current_user
from os.path import basename, join

@app.route('/music')
@login_required
def music_page():
    songs = Song.query.all()
    albums = Album.query.all()
    rating_form = RatingForm()
    return render_template('music.html', songs=songs, albums=albums, form=rating_form)


@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    form = SignupForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              role = form.role.data,
                              password = form.pwd1.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f'Account created successfully! You are logged in as: {user_to_create.username}', category='success')
        return redirect(url_for('music_page'))
    if form.errors != {}:
        for error in form.errors.values():
            flash(error, category='danger')
    return render_template('signup.html', form = form)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username = form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(attempted_password=form.password.data):
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.username}', category='success')
            return redirect(url_for('music_page'))
        else:
            flash('Username and Password do not match! Please try again', category='danger')
    return render_template('login.html', form = form)

@app.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category = 'info')
    return redirect(url_for("landing_page"))

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    return render_template('user_dashboard.html')

@app.route('/creator_dashboard')
@login_required
def creator_dashboard():
    songs = Song.query.filter_by(creator_id=current_user.id).all()
    albums = Album.query.filter_by(creator_id=current_user.id).all()
    return render_template('creator_dashboard.html', songs=songs, albums=albums)


@app.route('/add_song', methods=['GET', 'POST'])
@login_required
def add_song():
    form = SongForm()
    if form.validate_on_submit():
        audio_file = form.audio_link.data

        if audio_file:
            filename = secure_filename(audio_file.filename)

            file_path = join(app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(file_path)

            relative_path = 'Songs/' + basename(file_path)
        else:
            relative_path = None

        new_song = Song(
            title=form.title.data,
            lyrics=form.lyrics.data,
            duration=form.duration.data,
            genre=form.genre.data,
            artist_name=form.artist_name.data,
            audio_link=relative_path,
            poster=form.poster.data,
            creator=current_user
        )

        db.session.add(new_song)
        db.session.commit()

        flash('Song added successfully!', 'success')
        return redirect(url_for('creator_dashboard'))

    return render_template('add_song.html', form=form)


@app.route('/delete_song/<int:song_id>', methods=['POST'])
@login_required
def delete_song(song_id):
    song = Song.query.get_or_404(song_id)

    if current_user.role == 'admin' or current_user == song.creator:
            # Optionally, you can remove the file here if needed
            # file_path = join(app.config['UPLOAD_FOLDER'], basename(song.audio_link))
            # if os.path.exists(file_path):
            #     os.remove(file_path)

        db.session.delete(song)
        db.session.commit()

        flash('Song deleted successfully!', 'success')

        if current_user.role == 'admin':
            return redirect(url_for('view_all_songs'))
        else:
            return redirect(url_for('creator_dashboard'))
    else:
        flash('Song not found or you do not have permission to delete it.', 'danger')


@app.route('/edit_song/<int:song_id>', methods=['GET', 'POST'])
@login_required
def edit_song(song_id):
    song = Song.query.get_or_404(song_id)
    form = SongForm(obj=song)

    if form.validate_on_submit():
        song.title = form.title.data
        song.lyrics = form.lyrics.data
        song.duration = form.duration.data
        song.genre = form.genre.data
        song.artist_name = form.artist_name.data
        audio_file = form.audio_link.data
        if audio_file:
            filename = secure_filename(audio_file.filename)
            file_path = join(app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(file_path)
            song.audio_link = 'Songs/' + basename(file_path)

        db.session.commit()

        flash('Song updated successfully!', 'success')
        return redirect(url_for('creator_dashboard'))

    return render_template('edit_song.html', form=form, song=song)


@app.route('/playlists', methods=['GET'])
@login_required
def playlists_page():
    playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    return render_template('playlists.html', playlists=playlists)

@app.route('/create_playlist', methods=['GET', 'POST'])
@login_required
def create_playlist():
    form = PlaylistForm()

    form.songs.choices = [(song.id, f'{song.title} by {song.artist_name}') for song in Song.query.all()]

    if form.validate_on_submit():
        new_playlist = Playlist(name=form.name.data, user=current_user)
        db.session.add(new_playlist)
        db.session.commit()

        selected_songs = Song.query.filter(Song.id.in_(form.songs.data)).all()
        for song in selected_songs:
            new_playlist.add_song(song)

        flash('Playlist created successfully!', 'success')
        return redirect(url_for('playlists_page'))

    return render_template('create_playlist.html', form=form)

@app.route('/delete_playlist/<int:playlist_id>', methods=['POST'])
@login_required
def delete_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)

    if playlist.user != current_user:
        flash("You don't have permission to delete this playlist.", 'danger')
        return redirect(url_for('playlists_page'))

    db.session.delete(playlist)
    db.session.commit()

    flash('Playlist deleted successfully!', 'success')
    return redirect(url_for('playlists_page'))


@app.route('/edit_playlist/<int:playlist_id>', methods=['GET', 'POST'])
@login_required
def edit_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)

    if playlist.user != current_user:
        flash('You do not have permission to edit this playlist.', 'danger')
        return redirect(url_for('playlists_page'))

    available_songs = Song.query.all()

    form = PlaylistForm(obj=playlist)
    form.songs.choices = [(song.id, song.title) for song in available_songs]

    if form.validate_on_submit():
        playlist.name = form.name.data

        playlist.songs.clear()
        selected_song_ids = form.songs.data
        selected_songs = Song.query.filter(Song.id.in_(selected_song_ids)).all()
        playlist.songs.extend(selected_songs)

        db.session.commit()
        flash('Playlist updated successfully!', 'success')
        return redirect(url_for('playlists_page'))

    return render_template('edit_playlist.html', form=form, playlist=playlist, available_songs=available_songs)


@app.route("/profile")
@login_required
def profile_page():
    return render_template('profile.html', current_user=current_user)

@app.route('/upgrade_to_creator', methods=['POST'])
@login_required
def upgrade_to_creator():
    if current_user.role == 'user':
        current_user.role = 'creator'
        db.session.commit()
    return redirect(url_for('profile_page'))


@app.route('/get_lyrics/<int:song_id>')
def get_lyrics(song_id):
    song = Song.query.get_or_404(song_id)
    return render_template('lyrics_modal.html', song=song)



@app.route('/create_album', methods=['GET', 'POST'])
@login_required
def create_album():
    form = AlbumForm()

    form.songs.choices = [(song.id, f"{song.title} - {song.artist_name}") for song in current_user.songs]

    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        genre = form.genre.data
        poster = form.poster.data
        selected_song_ids = form.songs.data

        album = Album(title=title, description=description, genre=genre, creator=current_user)

        for song_id in selected_song_ids:
            song = Song.query.get(song_id)
            if song:
                album.songs.append(song)

        db.session.add(album)
        db.session.commit()

        flash('Album created successfully!', 'success')
        return redirect(url_for('creator_dashboard'))

    return render_template('create_album.html', form=form)



@app.route('/edit_album/<int:album_id>', methods=['GET', 'POST'])
@login_required
def edit_album(album_id):
    album = Album.query.get_or_404(album_id)

    if album.creator != current_user:
        flash('You do not have permission to edit this album.', 'danger')
        return redirect(url_for('creator_dashboard'))

    available_songs = current_user.songs

    form = AlbumForm(obj=album)
    form.songs.choices = [(song.id, song.title) for song in available_songs]

    if form.validate_on_submit():
        album.title = form.title.data
        album.description = form.description.data
        album.genre = form.genre.data
        album.poster = form.poster.data

        album.songs.clear()
        selected_song_ids = form.songs.data
        selected_songs = Song.query.filter(Song.id.in_(selected_song_ids)).all()
        album.songs.extend(selected_songs)

        db.session.commit()
        flash('Album updated successfully!', 'success')
        return redirect(url_for('creator_dashboard'))

    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Error in {field}: {error}', 'danger')

    return render_template('edit_album.html', form=form, album=album, available_songs=available_songs)


@app.route('/delete_album/<int:album_id>', methods=['POST'])
@login_required
def delete_album(album_id):
    album = Album.query.get(album_id)

    if album:
        if current_user.role == 'admin' or current_user == album.creator:
            db.session.delete(album)
            db.session.commit()

            flash('Album deleted successfully!', 'success')

            if current_user.role == 'admin':
                return redirect(url_for('view_all_albums'))
            else:
                return redirect(url_for('creator_dashboard'))
        else:
            flash('You do not have permission to delete this album.', 'danger')
    else:
        flash('Album not found.', 'danger')


@app.route('/view_songs/<int:album_id>')
@login_required
def view_songs(album_id):
    album = Album.query.get_or_404(album_id)
    form = RatingForm()
    return render_template('view_songs.html', album=album, form=form)

@app.route('/rate_song/<int:song_id>', methods=['POST'])
@login_required
def rate_song(song_id):
    form = RatingForm(request.form)

    if form.validate():
        existing_rating = Rating.query.filter_by(song_id=song_id, user_id=current_user.id).first()

        if existing_rating:
            existing_rating.value = form.rating.data
        else:
            new_rating = Rating(song_id=song_id, user_id=current_user.id, value=form.rating.data)
            db.session.add(new_rating)

        db.session.commit()

        song = Song.query.get(song_id)
        song.calculate_average_rating()
        db.session.commit()

        flash('Rating submitted successfully!', 'success')

    return redirect(url_for('music_page'))


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()

    if form.validate_on_submit():
        admin_user = User.query.filter_by(username=form.username.data, role='admin').first()

        if admin_user and admin_user.check_password_correction(attempted_password=form.password.data):
            login_user(admin_user)
            flash(f'Success! You are logged in as an admin: {admin_user.username}', category='success')
            return redirect(url_for('admin_dashboard'))

        else:
            flash('Admin credentials are incorrect. Please try again.', category='danger')

    return render_template('admin_login.html', form=form)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    total_users = User.query.count() - 1

    total_regular_users = User.query.filter_by(role='user').count()
    total_creator_users = User.query.filter_by(role='creator').count()

    total_albums = Album.query.count()
    total_songs = Song.query.count()

    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           total_regular_users=total_regular_users,
                           total_creator_users=total_creator_users,
                           total_albums=total_albums,
                           total_songs=total_songs)

@app.route('/admin/view_all_users')
@login_required
def view_all_users():
    all_users = User.query.all()
    return render_template('view_all_users.html', all_users=all_users)

@app.route('/admin/view_all_regular_users')
@login_required
def view_all_regular_users():
    all_regular_users = User.query.filter_by(role='user').all()
    return render_template('view_all_regular_users.html', all_regular_users=all_regular_users)

@app.route('/admin/view_all_creator_users')
@login_required
def view_all_creator_users():
    all_creator_users = User.query.filter_by(role='creator').all()
    return render_template('view_all_creator_users.html', all_creator_users=all_creator_users)

@app.route('/admin/view_all_albums')
@login_required
def view_all_albums():
    all_albums = Album.query.all()
    return render_template('view_all_albums.html', all_albums=all_albums)

@app.route('/admin/view_all_songs')
@login_required
def view_all_songs():
    all_songs = Song.query.all()
    return render_template('view_all_songs.html', all_songs=all_songs)

@app.route('/flag_creator/<int:user_id>', methods=['GET', 'POST'])
@login_required
def flag_creator(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        reason = request.form.get('reason')

        user.is_flagged = True
        user.flag_reason = reason
        db.session.commit()

        flash(f'{user.username} has been flagged.', 'success')
        return redirect(url_for('view_all_creator_users'))

    return render_template('flag_creator.html', user=user)

@app.route('/unflag_creator/<int:user_id>', methods=['POST'])
def unflag_creator(user_id):
    user = User.query.get(user_id)

    if user:
        user.is_flagged = False
        user.flag_reason = None
        db.session.commit()

        return redirect(url_for('view_all_creator_users'))
    else:
        return f'User with ID {user_id} not found'


from flask import render_template, request
from sqlalchemy import or_, desc


@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.form.get('query')

    if query:
        songs_query = or_(
            Song.title.ilike(f"%{query}%"),
            Song.genre.ilike(f"%{query}%"),
            Song.artist_name.ilike(f"%{query}%")
        )
        results_songs = Song.query.filter(songs_query).all()

        results_albums = Album.query.filter(or_(
            Album.title.ilike(f"%{query}%"),
            Album.genre.ilike(f"%{query}%")
        )).all()

        results_genres = [song for song in results_songs if song not in results_albums]

        results_artists = [song for song in results_songs if song not in results_albums and song not in results_genres]

    else:
        results_songs = []
        results_genres = []
        results_artists = []
        results_albums = []

    return render_template('search_results.html', results_songs=results_songs, results_genres=results_genres,
                           results_artists=results_artists, results_albums=results_albums)

from flask import render_template
from MusicApp.models import Song

@app.route('/')
def landing_page():
    highest_rated_songs = Song.query.order_by(Song.average_rating.desc()).limit(5).all()

    genres = [('rock', 'Rock'), ('pop', 'Pop'), ('hip_hop', 'Hip Hop'), ('electronic_dance', 'Electronic/Dance'), ('jazz', 'Jazz')]
    highest_rated_songs_by_genre = {}

    for genre_code, genre_name in genres:
        songs_by_genre = (
            Song.query
            .filter_by(genre=genre_name)
            .order_by(Song.average_rating.desc())
            .limit(5)
            .all()
        )
        highest_rated_songs_by_genre[genre_code] = songs_by_genre

    return render_template('landingPage.html', highest_rated_songs=highest_rated_songs, highest_rated_songs_by_genre=highest_rated_songs_by_genre)

@app.route('/currently_playing/<int:song_id>', methods=['GET'])
def currently_playing(song_id):
    song = Song.query.get_or_404(song_id)

    return render_template('currently_playing.html', song=song)

@app.route('/song_trends')
def top_songs_by_genre():
    genres = [
        ('Rock', 'rock'),
        ('Pop', 'pop'),
        ('Hip Hop', 'hip hop'),
        ('Electronic/Dance', 'electronic dance'),
        ('Jazz', 'jazz'),
    ]

    top_songs_by_genre = {}
    for genre, genre_slug in genres:
        top_songs = Song.query.filter(Song.genre == genre).order_by(desc(Song.average_rating)).limit(3).all()
        top_songs_by_genre[genre_slug] = top_songs

    return render_template('song_trends.html', top_songs_by_genre=top_songs_by_genre)