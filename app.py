from flask import Flask, render_template, request, redirect
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter
from flask_bcrypt import Bcrypt
from flask.ext.admin.contrib import sqla
from wtforms.fields import PasswordField
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
app.config['USER_PASSWORD_HASH'] = 'bcrypt'

db = SQLAlchemy(app)
admin = Admin(app)
bcrypt = Bcrypt(app)

class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(50), nullable=False, unique=True)
        password = db.Column(db.String(255), nullable=False, server_default='')
        active = db.Column(db.Boolean(), nullable=False, server_default='0')
        admin = db.Column(db.Boolean(), nullable=False, server_default='0')

        def is_admin(self):
                return self.admin

        def __repr__(self):
                return self.username

class Movie(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False, unique=True)
        genre = db.Column(db.String(50), nullable=False)

        def __repr__(self):
                return self.name

class Reservation(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        name_user = db.Column(db.String(50), db.ForeignKey('user.username'), nullable=False)
        name_movie = db.Column(db.String(100), db.ForeignKey('movie.name'), nullable=False)
        user = db.relationship('User', backref='user')
        movie = db.relationship('Movie', backref='movie')

db_adapter = SQLAlchemyAdapter(db, User)
user_manager = UserManager(db_adapter, app)

class MyView(BaseView):
    @expose('/')
    def index(self):
        return redirect('/')

class UserView(sqla.ModelView):
        form_columns=['username', 'active', 'admin']

        # Don't include the standard password field when creating or editing a User (but see below)
        form_excluded_columns = ('password')

        # Automatically display human-readable names for the current and available Roles when creating or editing a User
        column_auto_select_related = True

        # On the form for creating or editing a User, don't display a field corresponding to the model's password field.
        # There are two reasons for this. First, we want to encrypt the password before storing in the database. Second,
        # we want to use a password field (with the input masked) rather than a regular text field.
        def scaffold_form(self):
            # Start with the standard form as provided by Flask-Admin. We've already told Flask-Admin to exclude the
            # password field from this form.
            form_class = super(UserView, self).scaffold_form()

            # Add a password field, naming it "password2" and labeling it "Password".
            form_class.password2 = PasswordField('Password')
            return form_class

        # This callback executes when the user saves changes to a newly-created or edited User -- before the changes are
        # committed to the database.
        def on_model_change(self, form, model, is_created):
            # If the password field isn't blank...
            if len(model.password2):
                # ... then encrypt the new password prior to storing it in the database. If the password field is blank,
                # the existing password in the database will be retained.
                model.password = bcrypt.generate_password_hash(model.password2)

class MovieView(ModelView):
        form_columns=['name', 'genre']

class ReservationView(ModelView):
        form_columns=['user', 'movie']

admin.add_view(MyView(name='Back'))
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
