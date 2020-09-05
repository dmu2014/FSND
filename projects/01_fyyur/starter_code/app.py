#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import literal_column, and_
from forms import *
from datetime import datetime
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO-Done: connect to a local postgresql database


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
  __tablename__ = 'Show'
  
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', ondelete="CASCADE"), primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
  start_time = db.Column(db.String(120), nullable=False, primary_key=True)  

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)    
    facebook_link = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=True)
    seeking_talent = db.Column(db.Boolean(), nullable=True)
    seeking_description = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(120), nullable=True)    

    # TODO-DONE: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False )
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(500), nullable=True)
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=False)
    seeking_venue = db.Column(db.Boolean(), nullable=True)
    seeking_description = db.Column(db.String(120), nullable=True)

    # TODO-DONE: implement any missing fields, as a database migration using Flask-Migrate

# TODO-DONE Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO-DONE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[]
  state_cities=Venue.query.distinct(Venue.state, Venue.city).all()
   
  for state_city in state_cities:
    venues_in_state_city=Venue.query.filter(Venue.state == state_city.state and Venue.city == state_city.city).order_by(Venue.state, Venue.city).all()
    dataobj = {}
    dataobj['city'] = state_city.city
    dataobj['state'] = state_city.state  
    dataobj['venues'] = []
    
    for venue in venues_in_state_city:
      venuesobj={}
      venuesobj['id'] = venue.id
      venuesobj['name'] = venue.name
      venuesobj['num_upcoming_shows'] = Show.query.filter(Show.venue_id == venue.id, Show.start_time > datetime.now().strftime("%Y/%m/%d %H:%M:%S")).count() # TODO: calculate
      dataobj['venues'].append(venuesobj)

    data.append(dataobj)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO-DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  searchTerm = request.form.get('search_term', '')
  response = {}
  matchedVenues = db.session.query(Venue.id.label('q_venue_id'), Venue.name.label('q_venue_name')).filter(Venue.name.ilike('%' + searchTerm + '%')).subquery()
  matchedVenueswithNonZeroUpcomingShows = db.session.query(Venue.id.label('id'), Venue.name.label('name'), db.func.count(Venue.id).label('num_upcoming_shows')).join(Show).filter(Venue.name.ilike('%' + searchTerm + '%'), Show.start_time > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).group_by(Venue.id, Venue.name)
  matchedVenuesIdwithNonZeroUpcomingShows = db.session.query(Venue.id.label('id')).join(Show).filter(Venue.name.ilike('%' + searchTerm + '%'), Show.start_time > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).group_by(Venue.id, Venue.name)
  matchedVenueswithZeroUpcomingShows = db.session.query(matchedVenues.c.q_venue_id.label('id'), matchedVenues.c.q_venue_name.label('name'), literal_column("0").label('num_upcoming_shows')).filter(~matchedVenues.c.q_venue_id.in_(matchedVenuesIdwithNonZeroUpcomingShows)) 
  
  filteredVenues = matchedVenueswithNonZeroUpcomingShows.union(matchedVenueswithZeroUpcomingShows).all() 
  
  response['data'] = filteredVenues
  response['count'] = len(filteredVenues)

  return render_template('pages/search_venues.html', results=response, search_term=searchTerm)

@app.route('/venues/<int:venue_id>', methods=['GET'])
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO-DONE: replace with real venue data from the venues table, using venue_id

  venue = Venue.query.get(venue_id)  
  dataobj={}
  dataobj['id']=venue.id
  dataobj['name']=venue.name
  dataobj['genres']=venue.genres.split(',')
  dataobj['address']=venue.address
  dataobj['city']=venue.city
  dataobj['state']=venue.state
  dataobj['phone']=venue.phone
  dataobj['website']=venue.website
  dataobj['facebook_link']=venue.facebook_link
  dataobj['seeking_talent']=venue.seeking_talent
  dataobj['seeking_description']=venue.seeking_description 
  dataobj['image_link']=venue.image_link  
  pastShows = db.session.query(Artist.id.label('artist_id'), Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), Show.start_time.label('start_time')).join(Show).filter(Show.venue_id == venue_id, Show.start_time < datetime.now().strftime("%Y-%m-%d %H:%M:%S")).all()
  pastShowsCount = len(pastShows)  
  dataobj['past_shows'] = pastShows
  dataobj['past_shows_count'] = pastShowsCount
  upcomingShows = db.session.query(Artist.id.label('artist_id'), Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), Show.start_time.label('start_time')).join(Show).filter(Show.venue_id == venue_id, Show.start_time > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).all()
  upcomingShowsCount = len(upcomingShows)
  dataobj['upcoming_shows']=upcomingShows
  dataobj['upcoming_shows_count']=upcomingShowsCount

  return render_template('pages/show_venue.html', venue=dataobj)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO-DONE: insert form data as a new Venue record in the db, instead
  # TODO-DONE: modify data to be the data object returned from db insertion
  error=False
  body={}
  name = ''
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genresList = request.form.getlist('genres')
    genres=""
    for genre in genresList:
      genres = genres + genre + ","
    genres = genres.rstrip(',')
    facebook_link = request.form['facebook_link']
    venue = Venue(name=name,city=city, state=state, address=address,phone=phone,genres=genres,facebook_link=facebook_link)
    db.session.add(venue)
    db.session.commit()    
    body['id']=venue.id
    body['name']=venue.name
    body['city']=venue.city
    body['state']=venue.state
    body['address']=venue.address
    body['phone']=venue.phone
    body['genres']=venue.genres
    body['facebook_link']=venue.facebook_link
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + name + ' could not be listed.')    
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    
  return render_template('pages/home.html')

  # TODO-DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  

@app.route('/venues/delete/<venue_id>')
# DELETE method giving a 405 Error so using GET  
def delete_venue(venue_id):
  # TODO-DONE: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  error=False  
  venue = Venue.query.get(venue_id)
  name = venue.name
  try:
    showsForVenue = db.session.query(Show).filter(Show.venue_id == venue_id).all()
    for show in showsForVenue:
      db.session.delete(show)
      db.session.commit()    
    db.session.delete(venue)
    db.session.commit()   
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + name + ' could not be deleted.')    
  else:
    flash('Venue ' + name + ' was successfully deleted!')
    
  return render_template('pages/home.html')

  # BONUS CHALLENGE-DONE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO-DONE: replace with real data returned from querying the database

  data=db.session.query(Artist.id.label('id'), Artist.name.label('name')).all()
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO-DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  
  searchTerm = request.form.get('search_term', '')
  response = {}
  matchedArtists = db.session.query(Artist.id.label('q_artist_id'), Artist.name.label('q_artist_name')).filter(Artist.name.ilike('%' + searchTerm + '%')).subquery()
  matchedArtistswithNonZeroUpcomingShows = db.session.query(Artist.id.label('id'), Artist.name.label('name'), db.func.count(Artist.id).label('num_upcoming_shows')).join(Show).filter(Artist.name.ilike('%' + searchTerm + '%'), Show.start_time > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).group_by(Artist.id, Artist.name)
  matchedArtistIdwithNonZeroUpcomingShows = db.session.query(Artist.id.label('id')).join(Show).filter(Artist.name.ilike('%' + searchTerm + '%'), Show.start_time > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).group_by(Artist.id, Artist.name)
  matchedArtistswithZeroUpcomingShows = db.session.query(matchedArtists.c.q_artist_id.label('id'), matchedArtists.c.q_artist_name.label('name'), literal_column("0").label('num_upcoming_shows')).filter(~matchedArtists.c.q_artist_id.in_(matchedArtistIdwithNonZeroUpcomingShows)) 
  
  filteredArtists = matchedArtistswithNonZeroUpcomingShows.union(matchedArtistswithZeroUpcomingShows).all()
  response['data'] = filteredArtists
  response['count'] = len(filteredArtists)

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO-DONE: replace with real venue data from the venues table, using venue_id

  artist = Artist.query.get(artist_id)  
  dataobj={}
  dataobj['id']=artist.id
  dataobj['name']=artist.name
  dataobj['genres']=artist.genres.split(',')  
  dataobj['city']=artist.city
  dataobj['state']=artist.state
  dataobj['phone']=artist.phone
  dataobj['website']=artist.website
  dataobj['facebook_link']=artist.facebook_link
  dataobj['seeking_venue']=artist.seeking_venue
  dataobj['seeking_description']=artist.seeking_description 
  dataobj['image_link']=artist.image_link  
  pastShows = db.session.query(Venue.id.label('venue_id'), Venue.name.label('venue_name'), Venue.image_link.label('venue_image_link'), Show.start_time.label('start_time')).join(Show).filter(Show.artist_id == artist_id, Show.start_time < datetime.now().strftime("%Y-%m-%d %H:%M:%S")).all()
  pastShowsCount = len(pastShows)  
  dataobj['past_shows'] = pastShows
  dataobj['past_shows_count'] = pastShowsCount
  upcomingShows = db.session.query(Venue.id.label('venue_id'), Venue.name.label('venue_name'), Venue.image_link.label('venue_image_link'), Show.start_time.label('start_time')).join(Show).filter(Show.artist_id == artist_id, Show.start_time > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).all()
  upcomingShowsCount = len(upcomingShows)
  dataobj['upcoming_shows']=upcomingShows
  dataobj['upcoming_shows_count']=upcomingShowsCount

  return render_template('pages/show_artist.html', artist=dataobj)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):  
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  
  # TODO-Done: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO-Done: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  error=False
  name = ''
  artist = Artist.query.get(artist_id)
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genresList = request.form.getlist('genres')
    genres=""
    for genre in genresList:
      genres = genres + genre + ","
    genres = genres.rstrip(',')
    facebook_link = request.form['facebook_link']
    artist.name = name
    artist.city = city
    artist.state = state
    artist.phone = phone
    artist.genres = genres
    artist.facebook_link = facebook_link
    db.session.commit()  
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + name + ' could not be edited.')    
  else:
    flash('Artist ' + request.form['name'] + ' was successfully edited!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)

  # TODO-Done: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO-Done: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes

  error=False  
  name = ''
  venue = Venue.query.get(venue_id)
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genresList = request.form.getlist('genres')
    genres=""
    for genre in genresList:
      genres = genres + genre + ","
    genres = genres.rstrip(',')
    facebook_link = request.form['facebook_link']
    venue.name = name
    venue.city = city
    venue.state = state
    venue.address = address
    venue.phone = phone
    venue.genres = genres
    venue.facebook_link = facebook_link    
    db.session.commit()    
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + name + ' could not be edited.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully edited!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO-Done: insert form data as a new Venue record in the db, instead
  # TODO-Done: modify data to be the data object returned from db insertion

  error=False
  body={}
  name = ''
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genresList = request.form.getlist('genres')
    genres=""
    for genre in genresList:
      genres = genres + genre + ","
    genres = genres.rstrip(',')
    facebook_link = request.form['facebook_link']
    artist = Artist(name=name,city=city, state=state, phone=phone,genres=genres,facebook_link=facebook_link)
    db.session.add(artist)
    db.session.commit()    
    body['id']=artist.id
    body['name']=artist.name
    body['city']=artist.city
    body['state']=artist.state
    body['phone']=artist.phone
    body['genres']=artist.genres
    body['facebook_link']=artist.facebook_link
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + name + ' could not be listed.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  # on successful db insert, flash success
  #flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO-Done: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO-Done: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  #Comment - Filter by upcoming shows order by venue
  data = db.session.query(Show.venue_id.label('venue_id'), Show.artist_id.label('artist_id'), Show.start_time.label('start_time'), Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), Venue.name.label('venue_name')).join(Artist).join(Venue).filter( Show.start_time > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).order_by(Venue.id).all()
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO-Done: insert form data as a new Show record in the db, instead

  error=False
  body={}
  name = ''
  try:
    artist_id = request.form['artist_id']    
    venue_id = request.form['venue_id']
    isValid = validate_show_submission(artist_id, venue_id)
    if(not isValid):
      flash('An error occurred. Show for artist ' + artist_id + ' and venue ' + venue_id + ' could not be listed. Invalid ArtistId and/or VenueId' )
      return render_template('pages/home.html')
    start_time = request.form['start_time']    
    show = Show(artist_id=artist_id,venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()    
    body['artist_id']=show.artist_id
    body['venue_id']=show.venue_id
    body['start_time']=show.start_time    
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Show for artist ' + request.form['artist_id'] + 'and venue ' + request.form['venue_id'] + ' could not be listed.')    
  else:
    flash('Show for artist ' + request.form['artist_id'] + 'and venue ' + request.form['venue_id'] + ' was successfully listed!')
  # on successful db insert, flash success
  #flash('Show was successfully listed!')
  # TODO-Done: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')


def validate_show_submission(artist_id, venue_id):
  if(Artist.query.get(artist_id) == None):
    return False
  if(Venue.query.get(venue_id) == None):
    return False

  return True


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug=true)


# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
