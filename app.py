from flask import Flask, render_template, request, redirect
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter
import sqlite3 as sql

import os

app = Flask(__name__)
#path not fixed
db_path = os.path.join(os.path.dirname(__file__), 'database.db')
db_uri = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SECRET_KEY'] = 'thisisasecret'
app.config['CSRF_ENABLED'] = True 
app.config['USER_ENABLE_EMAIL'] = False 
app.config['USER_APP_NAME'] = 'DVD Club'
app.config['USER_AFTER_LOGOUT_ENDPOINT'] = 'index'

db = SQLAlchemy(app)
admin = Admin(app)

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(50), nullable=False, unique=True)
	password = db.Column(db.String(255), nullable=False, server_default='')
	active = db.Column(db.Boolean(), nullable=False, server_default='0')

	def __repr__(self):
                return(self.username)

class Movie(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False, unique=True)
        genre = db.Column(db.String(50), nullable=False)

        def __repr__(self):
                return (self.name)

class Reservation(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name_user = db.Column(db.String(50), db.ForeignKey('user.username'), nullable=False)
    name_movie = db.Column(db.String(100), db.ForeignKey('movie.name'), nullable=False)
    user = db.relationship('User', backref='user')
    movie = db.relationship('Movie', backref='movie')

db_adapter = SQLAlchemyAdapter(db, User)
user_manager = UserManager(db_adapter, app)

class UserView(ModelView):
	form_columns=['username', 'password', 'active']

class MovieView(ModelView):
	form_columns=['name', 'genre']

class ReservationView(ModelView):
	form_columns=['user', 'movie']

admin.add_view(UserView(User, db.session))
admin.add_view(MovieView(Movie, db.session))
admin.add_view(ReservationView(Reservation, db.session))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('flask_user/user_profile.html')

@app.route('/reservation', methods=['POST'])
@login_required
def reservation():
	if request.method=='POST':
		user = request.form['name']
		movie = request.form['movie']
		con = sql.connect("database.db")
		cur = con.cursor()
		cur.execute("INSERT INTO reservation (name_user,name_movie) VALUES (?,?)", (user,movie))
		con.commit()
		con.close()
		return redirect('/')

if __name__ == '__main__':
    app.run(debug=True) 
