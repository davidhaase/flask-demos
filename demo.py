import os
from datetime import datetime

from flask import Flask, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy

from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired

basedir = os.path.abspath(os.path.dirname(__file__))

###########################
# APP, CONFIGS & EXTENTSIONS
# Initialize Flask and the Flask extensions at the app-level
app = Flask(__name__)

# Flask app.config
# The app.config dictionary is a general-purpose place to store configuration
# variables used by used by Flask, extensions, or the application itself.
# Configuration values can be added to the app.config object using standard
# dictionary syntax. The configuration object also has methods to import
# configuration values from files or the environment.

# wtf configs
# Unlike most other extensions, Flask-WTF does not need to be initialized at the
# application level, but it expects the application to have a secret key configured.
app.config['SECRET_KEY'] = 'my super secret string'

#  db configs
#  The URL of the application database must be configured as the
#  key SQLALCHEMY_DATABASE_URI in the Flask configuration object.
#  The Flask-SQLAlchemy documentation also suggests setting key
#  SQLALCHEMY_TRACK_MODIFICATIONS to False to use less memory unless
#  signals for object changes are needed.
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask Extensions
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
# END app, configs & extensions
###########################

###########################
# DB CLASSES
#  The __tablename__ class variable defines the name of the table in the
#  database. Flask-SQLAlchemy assigns a default table name if __tablename__
#  is omitted, but those default names do not follow the popular convention
#  of using plurals for table names, so it is best to name tables explicitly.
#  The remaining class variables are the attributes of the model, defined as
#  instances of the db.Column class.
#
#  The first argument given to the db.Column constructor is the type of the
#  database column and model attribute

# NOTE: SQLite databases do not have a server, so hostname, and password
# are omitted and database is the filename on disk for the database.
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # users = db.relationship('User', backref='role')
    users = db.relationship('User', backref='role', lazy='dynamic')

    # Add a string-representation for debugging
    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    # Add a string-representation for debugging
    def __repr__(self):
        return '<User %r>' % self.username

# END DB CLASSES
###########################

###########################
# HTML FORM CLASSES
# With WTF, each web form is represented in the server by a class that
# inherits from the class FlaskForm. The class defines the list of fields
# in the form, each represented by an object. Each field object can have
# one or more validators attached. A validator is a function that checks
# whether the data submitted by the user is valid.
class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')

# END FORM CLASSES
###########################

###########################
# PYTHON SHELL
# Having to import the database instance and the models each time a shell
# session is started is tedious work. To avoid having to constantly repeat
# these steps, the flask shell command can be configured to automatically
# import these objects.
# To add objects to the import list, a shell context processor must be
# created and registered with the app.shell_context_processor decorator

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)
# END python shell
###########################

###########################
# ERROR HANDLING
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# END error handling
###########################

###########################
# ROUTES -- now define a route for each page
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()

        # If the entered name doesn't exist, add it to the db
        # ...and send the known-flag back to the form
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
        else:
            session['known'] = True

        #  Add a session variable and redirect to avoid
        #  the ugly repost warning from the browser
        session['name'] = form.name.data
        return redirect(url_for('index'))

    return render_template('index.html', form=form,
                            name=session.get('name'),
                            known=session.get('known', False),
                            current_time=datetime.utcnow())



@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)

# END routes
###########################

if __name__ == '__main__':
    app.run(debug=True)
