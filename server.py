#!/usr/bin/env python

from flask import Flask, render_template, request, redirect, url_for, g
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, DateField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
import time, datetime
from datetime import date
from flask_datepicker import datepicker


app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
file_path = os.path.abspath(os.getcwd())+"/database.db"
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+file_path
bootstrap = Bootstrap(app)
datepicker(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def dateDiffInSeconds(date1, date2):
  timedelta = date2 - date1
  return timedelta.days * 24 * 3600 + timedelta.seconds

def daysHoursMinutesSecondsFromSeconds(seconds):
	minutes, seconds = divmod(seconds, 60)
	hours, minutes = divmod(minutes, 60)
	days, hours = divmod(hours, 24)
	return (days, hours, minutes, seconds)

# Formato en Mes/Dia/Año
class DateForm(FlaskForm):
    dt = DateField('Pick a Date', format="%m/%d/%Y")

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    limited_date = db.Column(db.String(120))
    admin_privilege = db.Column(db.Integer)

#class User(UserMixin, db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    userid = db.Column(db.Integer)
#    urlaccess = db.Column(db.String(50))
#    reason = db.Column(db.String(150))
#    limited_date = db.Column(db.String(120))
#CREATE TABLE access(
#            id INTEGER PRIMARY KEY AUTOINCREMENT, userid INTEGER NOT NULL, urlaccess TEXT NOT NULL,
#            reason TEXT NOT NULL, limited_date TEXT NOT NULL);
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
##########/

DATABASE = "database.db"

# Gestión de la base de datos.

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def change_db(query,args=()):
    cur = get_db().execute(query, args)
    get_db().commit()
    cur.close()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# URL de enrutamiento y procesamientos.
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/adminpanel')
@login_required
def adminpanel():
    if current_user.admin_privilege == 1:
        user_list=query_db("SELECT * FROM user")
        #limited_date_object = datetime.datetime.strptime(current_user.limited_date, '%Y-%m-%d %H:%M:%S')
        return render_template("adminpanel.html",current_user=current_user,user_list=user_list, actualdate = datetime.datetime.now(), datetime = datetime)
    else:
        return('<h1>Su actual usuario no es administrador.</h1>')

@app.route('/accesslist')
@login_required
def accesslist():
    if current_user.admin_privilege == 1:
        access_list=query_db("SELECT * FROM access")
        #limited_date_object = datetime.datetime.strptime(current_user.limited_date, '%Y-%m-%d %H:%M:%S')
        return render_template("accesslist.html",current_user=current_user,access_list=access_list, actualdate = datetime.datetime.now(), datetime = datetime, len=len)
    else:
        return('<h1>Su actual usuario no es administrador.</h1>')

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == "GET":
        return render_template("create.html",access=None)

    if request.method == "POST":
        access=request.form.to_dict()
        values=[current_user.username,access["urlaccess"],access["limited_date"],access["reason"], access["from_date"], access["end_date"]]
        change_db("INSERT INTO access (userid, urlaccess, limited_date, reason, from_date, end_date) VALUES (?,?,?,?,?,?)",values)
        if current_user.admin_privilege == 1:
            return redirect(url_for("accesslist"))
        else:
            return redirect(url_for("requestdone"))

@app.route('/requestdone', methods=['GET', 'POST'])
@login_required
def requestdone():
    return render_template("requestdone.html")

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def udpate(id):

    if request.method == "GET":
        access_list=query_db("SELECT * FROM access WHERE id=?",[id],one=True)
        return render_template("update.html",access=access_list)

    if request.method == "POST":

        print(request.form)
        access=request.form.to_dict()
        values=[access["urlaccess"],access["limited_date"],access["reason"],id]
        change_db("UPDATE access SET urlaccess=?, limited_date=?, reason=? WHERE ID=?",values)
        return redirect(url_for("accesslist"))

@app.route('/userupdate/<int:id>', methods=['GET', 'POST'])
@login_required
def userudpate(id):

    if request.method == "GET":
        user=query_db("SELECT * FROM user WHERE id=?",[id],one=True)
        return render_template("userupdate.html",user=user)

    if request.method == "POST":

        print(request.form)
        user=request.form.to_dict()
        print(user)
        values=[user["username"],user["email"],user["limited_date"],user["admin_privilege"],id]
        change_db("UPDATE user SET username=?, email=?, limited_date=?, admin_privilege=? WHERE ID=?",values)
        return redirect(url_for("adminpanel"))

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):

    if request.method == "GET":
        user=query_db("SELECT * FROM user WHERE id=?",[id],one=True)
        return render_template("delete.html",user=user)

    if request.method == "POST":
        change_db("DELETE FROM user WHERE id = ?",[id])
        return redirect(url_for("adminpanel"))

@app.route('/deleterequest/<int:id>', methods=['GET', 'POST'])
@login_required
def deleterequest(id):

    if request.method == "GET":
        access=query_db("SELECT * FROM access WHERE id=?",[id],one=True)
        return render_template("deleteaccess.html")

    if request.method == "POST":
        change_db("DELETE FROM access WHERE id = ?",[id])
        return redirect(url_for("accesslist"))

@app.route('/activate/<int:id>')
def activate(id):
        change_db("UPDATE user SET Activated=1 WHERE ID=?",[id])
        return redirect(url_for("adminpanel"))

@app.route('/deactivate/<int:id>')
def deactivate(id):
        change_db("UPDATE user SET Activated=0 WHERE ID=?",[id])
        return redirect(url_for("adminpanel"))

@app.route('/approverequest/<int:id>')
def approverequest(id):
        change_db("UPDATE access SET approve=1 WHERE ID=?",[id])
        return redirect(url_for("accesslist"))

@app.route('/rejectrequest/<int:id>')
def rejectrequest(id):
        change_db("UPDATE access SET approve=0 WHERE ID=?",[id])
        return redirect(url_for("accesslist"))

@app.route('/addtime/<int:id>')
def addtime(id):
        now = datetime.datetime.now()
        finalDate = now + datetime.timedelta(seconds=320)
        finalDate = "'"+ finalDate.strftime('%Y-%m-%d %H:%M:%S') +"'"
        change_db("UPDATE user SET limited_date="+ finalDate +" WHERE ID=?",[id])
        return redirect(url_for("adminpanel"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated == True:
        return redirect(url_for("userpanel"))
    else:
        form = LoginForm()

        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user:
                if check_password_hash(user.password, form.password.data):
                    login_user(user, remember=form.remember.data)
                    return redirect(url_for('userpanel'))
                else:
                    return render_template('login.html', form=form, error=True)
                    #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'
        return render_template('login.html', form=form, error=False)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        #aqui hay que tener la fecha del instante de creacion , intente con esto
        #pero la libreria date no quiere cargar correctamente "2010-01-01 01:00:00"
        default_limited_date = datetime.datetime.now()
        print (default_limited_date)
        print (default_limited_date.strftime("%Y-%m-%d %H:%M:%S"))
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password, limited_date = default_limited_date.strftime("%Y-%m-%d %H:%M:%S"), admin_privilege = 0 )
        db.session.add(new_user)
        db.session.commit()

        return '<h1>New user has been created! ' + form.username.data + ' ' + form.email.data + ' ' + default_limited_date.strftime("%Y-%m-%d") + ' </h1>'
        #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

    return render_template('signup.html', form=form)

@app.route('/userpanel')
@login_required
def userpanel():
    if current_user.admin_privilege == 0: 
        return render_template('userpanel.html', user=current_user)
    else:
        return redirect(url_for('adminpanel'))

@app.route('/switch_1')
@login_required
def switch_1():
    access_to_switch = False
    if current_user.admin_privilege == 0: 
    # '0' meaning a normal user. '1' would be an admin user. '2' is an admin user with total admin privilege that can't be erased or modified.
    # a '2' level admin privilege user would sometimes be refered as 'the system'. 
        user_access_list = query_db("SELECT * FROM access WHERE userid=?",[current_user.username])
        for accessrequest in user_access_list:
            if "switch" in accessrequest["urlaccess"] and accessrequest["approve"] == 1:
               access_to_switch = True
               access_date = accessrequest["limited_date"]
               break
    else:
        return redirect(url_for('adminpanel'))

    if access_to_switch == True:
        leaving_date = datetime.datetime.strptime(access_date, '%Y-%m-%d %H:%M:%S')
        now = datetime.datetime.now()
        dt = daysHoursMinutesSecondsFromSeconds(dateDiffInSeconds(now, leaving_date))

        if int(dt[0]) < 0 or int(dt[1]) < 0 or int(dt[2]) < 0:
            logout_user()
            return render_template('no_access.html', error=2, user=current_user)
        else:
            return render_template('switch_1.html', user=current_user)
    else:
        return render_template('no_access.html', error=1, user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
