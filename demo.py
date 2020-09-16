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

#########
# Initialize Flask and the Flask extensions at the app-level
app = Flask(__name__)

#  - The app.config dictionary is a general-purpose place to
#  - store configuration variables used by Flask, extensions,
#  - or the application itself. Configuration values can be added
#  - to the app.config object using standard dictionary syntax.
#  - The configuration object also has methods to import configuration
#  - values from files or the environment.
app.config['SECRET_KEY'] = 'my super secret string'

#  - The URL of the application database must be configured as the
#  - key SQLALCHEMY_DATABASE_URI in the Flask configuration object.
#  - The Flask-SQLAlchemy documentation also suggests setting key
#  - SQLALCHEMY_TRACK_MODIFICATIONS to False to use less memory unless
#  - signals for object changes are needed.
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)

# END initializing app extensions and configurations
#########

#########
# DATABASES Define db classes
#  - The __tablename__ class variable defines the name of the table in the
#  - database. Flask-SQLAlchemy assigns a default table name if __tablename__
#  - is omitted, but those default names do not follow the popular convention
#  - of using plurals for table names, so it is best to name tables explicitly.
#  - The remaining class variables are the attributes of the model, defined as
#  - instances of the db.Column class.
#  - The first argument given to the db.Column constructor is the type of the
#  - database column and model attribute

# NOTE: SQLite databases do not have a server, so hostname, and password
#  - are omitted and database is the filename on disk for the database.
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
#########

#########
# HTML FORMS - Define the Form Classes
#  - With WTF, each web form is represented in the server by a class that
#  - inherits from the class FlaskForm. The class defines the list of fields
#  - in the form, each represented by an object. Each field object can have
#  - one or more validators attached. A validator is a function that checks
#  - whether the data submitted by the user is valid.
class SourceTxtForm(FlaskForm):
    source_txt = StringField('Enter text in English', validators=[DataRequired()])
    submit = SubmitField('Submit')

class LangSelectionForm(FlaskForm):
    target_lang = SelectField(['English', 'French'], validators=[DataRequired()])

# END FORM CLASSES
#########

#########
# Capture major errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# END error handling
#########

#########
# ROUTES -- now define a route for each page
@app.route('/', methods=['GET', 'POST'])
def index():
    form = SourceTxtForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
        else:
            session['known'] = True



        # Quick session-based persistence used for Flash messages at top of page
        # previous_txt = session.get('source_txt')
        # if previous_txt == form.source_txt.data:
        #     flash('Looks like you entered the same text!')

        #  Add a session variable and redirect to avoid
        #  the ugly repost warning from the browser
        session['source_txt'] = form.source_txt.data

        return redirect(url_for('index'))
    return render_template('index.html', form=form,
                            source_txt=session.get('source_txt'),
                            current_time=datetime.utcnow())



@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)

# END ROUTES
#########

if __name__ == '__main__':
    app.run(debug=True)
