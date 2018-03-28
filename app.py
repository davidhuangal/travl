'''

Travl is a travel plan storage website that I'm using to practice my web development skills.

It was built using the Flask framework, Boostrap and MySQL.

I used the example code from bradtraversy's myflaskapp for a lot of the format
It can be found here: https://github.com/bradtraversy/myflaskapp

'''



from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, SelectField, IntegerField, validators, widgets
from passlib.hash import sha256_crypt
from functools import wraps
import sys

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345'
app.config['MYSQL_DB'] = 'travl'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

#Home Page
@app.route('/')
def index():
    if session.get('logged_in', False) == True:
        return redirect((url_for('my_journies')))
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        # flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']
            userid = data['id']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                session['userid'] = userid

                flash('You are now logged in', 'success')
                return redirect(url_for('index'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    if session.get('logged_in', False) == True:
        session.clear()
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))



# User Journies
@app.route('/journies')
def my_journies():
    if session.get('logged_in', False) == True:
        # Create cursor
        cur = mysql.connection.cursor()

        # Get user Journies
        result = cur.execute("SELECT * FROM journies WHERE userid = %s" % (session['userid']))
        count = cur.rowcount
        print(count, file=sys.stderr)
        journies = cur.fetchall()

        if count > 0:
            msg = ""
            return render_template('journies.html', journies=journies,  username=session['username'])

        else:
            msg = "No journies found."
            return render_template('journies.html', msg=msg)

        cur.close()

    return redirect(url_for('login'))

# Looking at a single Journey
@app.route('/journey/<string:username>/<string:id>/')
def journey(username, id):
    if session.get('logged_in', False) == True and username == session['username']:

        # Create MySQL Cursor
        cur = mysql.connection.cursor()

        # Get the particular journey
        result = cur.execute("SELECT * FROM journies WHERE userid = %s AND id = %s" % (session['userid'], id))

        journey = cur.fetchone()

        return render_template('journey.html', journey=journey)

    return redirect(url_for('index'))


# Journey Form Class
class JourneyForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=255)])
    description = TextAreaField('Description', [validators.Length(max=255)])
    season = SelectField('Season', [validators.required()], choices=[('spring', 'Spring'), ('summer', 'Summer'), ('autumn', 'Autumn'), ('winter', 'Winter')])
    genre = SelectField('Genre', [validators.required()], choices=[('education', 'Educational'), ('party', 'Party'), ('culture', 'Culture'), ('relaxation', 'Relaxation'), ('any', 'Anything')])
    budget = IntegerField('Budget (USD)', [validators.required()], widget = widgets.Input(input_type="number"))
    location = StringField('Location', [validators.Length(min=1, max=255)])
    length = IntegerField('Length of trip (in days)', [validators.required()], widget = widgets.Input(input_type="number"))
    status = SelectField('Status', [validators.required()], choices=[('planning', 'Planning'), ('in progress', 'In-Progress'), ('completed', 'Completed')])



# Create a new journey
@app.route('/new-journey', methods=['GET', 'POST'])
def new_journey():
    if session.get('logged_in', False) == True:
        form = JourneyForm(request.form)
        if request.method == 'POST' and form.validate():
            title = form.title.data
            description = form.description.data
            season = form.season.data
            genre = form.genre.data
            budget = form.budget.data
            location = form.location.data
            length = form.length.data
            status = form.status.data

            # Create Cursor
            cur = mysql.connection.cursor()

            # Execute
            cur.execute("INSERT INTO journies (userid, title, description, season, genre, budget, location, length_in_days, completed_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);", (session['userid'], title, description, season, genre, budget, location, length, status))

            # Commit to DB
            mysql.connection.commit()

            # Close connection
            cur.close()

            return redirect(url_for('my_journies'))
        return render_template('new-journey.html', form=form)
    return redirect(url_for('login'))


# Edit Journey
@app.route('/edit-journey/<string:username>/<string:id>/', methods=['GET', 'POST'])
def edit_journey(id, username):

    if session.get('logged_in', False) == True and username == session['username']:
        # Create cursor
        cur = mysql.connection.cursor()

        # Get the particular journey to edit
        result = cur.execute("SELECT * FROM journies WHERE userid = %s AND id = %s" % (session['userid'], id))

        journey = cur.fetchone()
        cur.close()
        # Get form
        form = JourneyForm(request.form)

        # Populate journey form fields
        form.title.data = journey['title']
        form.description.data = journey['description']
        form.season.data = journey['season']
        form.genre.data = journey['genre']
        form.budget.data = journey['budget']
        form.location.data = journey['location']
        form.length.data = journey['length_in_days']
        form.status.data = journey['completed_status']

        if request.method == 'POST' and form.validate():
            title = request.form['title']
            description = request.form['description']
            season = request.form['season']
            genre = request.form['genre']
            budget = request.form['budget']
            location = request.form['location']
            length = request.form['length']
            status = request.form['status']

            # Create Cursor
            cur = mysql.connection.cursor()
            app.logger.info(title)
            # Execute
            cur.execute("UPDATE journies SET title=%s, description=%s, season=%s, genre=%s, budget=%s, location=%s, length_in_days=%s, completed_status=%s WHERE id=%s and userid=%s",(title, description, season, genre, budget, location, length, status, id, session['userid']))
            # Commit to DB
            mysql.connection.commit()

            #Close connection
            cur.close()

            return redirect(url_for('my_journies'))

        return render_template('edit_journey.html', form=form)
    return redirect(url_for('login'))


# Delete Journey
@app.route('/delete-journey/<string:username>/<string:id>/', methods=['POST'])
def delete_article(id, username):
    if session.get('logged_in', False) == True and username == session['username']:

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("DELETE FROM journies WHERE id = %s AND userid = %s", ([id], session['userid']))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        return redirect(url_for('my_journies'))

    return redirect(url_for('login'))



if __name__ == '__main__':
    app.secret_key='secret123'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True)
