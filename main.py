from flask import Flask, redirect, request, render_template, flash
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from url_secrets import *
from flask_login import UserMixin, current_user, login_user, logout_user, LoginManager, login_required
from forms import RegisterForm
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
    user_name = db.Column(db.Integer)


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
    show_sign_up_modal, show_login_modal = False, False

    if "show_login_modal" in request.args:
        show_login_modal = str(request.args["show_login_modal"])

    if "show_sign_up_modal" in request.args:
        show_sign_up_modal = str(request.args["show_sign_up_modal"])

    print(current_user)

    return render_template("index.html",
                           user=current_user,
                           show_login_modal=show_login_modal,
                           show_sign_up_modal=show_sign_up_modal)


@app.route('/delete/<int:page_id>')
@login_required
def delete_record(page_id):
    webpage = Websites.query.filter_by(id=page_id).first()
    if webpage.user_name == current_user.id:
        db.session.delete(webpage)
        db.session.commit()
    return redirect(url_for("user_account"))


@app.route('/login', methods=["POST", "GET"])
def login_func():
    if request.method == "POST":
        user = Users.query.filter_by(email=request.form.get("email")).first()
        if not user:
            flash("User does not exist, please sign up.")
            return redirect(url_for("index", show_sign_up_modal=True))
        elif not check_password_hash(user.password, request.form.get("password")):
            flash("Incorrect password, please try again")
            return redirect(url_for("index", show_login_modal=True))
        else:
            login_user(user)
            return redirect(url_for("index"))
    return redirect(url_for("index"))


@app.route('/register', methods=["POST", "GET"])
def register_func():
    form = RegisterForm()
    if form.validate_on_submit():
        user_email = form.email.data
        if Users.query.filter_by(email=user_email).first():
            flash("User already exist!")
            return redirect(url_for("index", show_login_modal=True))
        new_user = Users(
            email=user_email,
            password=generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8),
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("index"))
    return render_template("register.html", form=form, user=current_user)


@app.route("/logout")
def logout_func():
    logout_user()
    return redirect(url_for("index"))


@app.route("/settings")
@login_required
def user_account():
    websites = Websites.query.filter_by(user_name=current_user.id).all()
    return render_template("settings.html", websites_list=websites, user=current_user)


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
        user_name=current_user.id,
    )
    db.session.add(new_website)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/<name>')
def reroute(name):
    webpage = Websites.query.filter_by(name=name).first()
    if webpage:
        return redirect(Websites.query.filter_by(name=name).first().website_address)
    else:
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
    app.run()
