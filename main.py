from flask import Flask, redirect, request, render_template, flash
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from url_secrets import *
from flask_login import UserMixin, current_user, login_user, logout_user, LoginManager, login_required
from forms import RegisterForm, LoginForm, AddWebsite
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap


app = Flask(__name__)

app.config['SECRET_KEY'] = APP_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{POSTGRESQL_LOGIN}:' \
                                        f'{POSTGRESQL_PASS}@{POSTGRESQL_SERVER}/' \
                                        f'{POSTGRESQL_DB}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)


class Websites(db.Model):
    __tablename__ = "url_websites"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    website_address = db.Column(db.String(100))


class Users(UserMixin, db.Model):
    __tablename__ = "url_users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)


@app.route('/')
def index():
    return render_template("index.html", user=current_user)


@app.route('/login', methods=["POST", "GET"])
def login_func():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if not user:
            flash("User does not exist!")
            return redirect(url_for("register_func"))
        elif not check_password_hash(user.password, form.password.data):
            flash("Incorrect password, please try again")
            return redirect(url_for("login_func"))
        else:
            login_user(user)
            return redirect(url_for("index"))
    return render_template("login.html", form=form)


@app.route('/register', methods=["POST", "GET"])
def register_func():
    form = RegisterForm()
    if form.validate_on_submit():
        user_email = form.email.data
        if Users.query.filter_by(email=user_email).first():
            flash("User already exist!")
            return redirect(url_for("login_func"))
        new_user = Users(
            email=user_email,
            password=generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8),
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("index"))
    return render_template("register.html", form=form)


@app.route("/logout")
def logout_func():
    logout_user()
    return redirect(url_for("index"))


@app.route('/contact')
def contact_func():
    return "ContactPage"


@app.route('/data', methods=["POST"])
@login_required
def data():
    form_data = request.form
    new_website = Websites(
        name=form_data["Website"],
        website_address=form_data["Address"],
    )
    db.session.add(new_website)
    db.session.commit()
    print(form_data)
    return redirect(url_for('index'))


@app.route('/show')
def print_value():
    websites = Websites.query.all()
    for website in websites:
        print(f"{website.name}/{website.website_address}")
    return redirect(url_for('index'))


@app.route('/<name>')
def reroute(name):
    return redirect(Websites.query.filter_by(name=name).first().website_address)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
    app.run()
