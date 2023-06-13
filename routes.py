from flask import (
    Flask,
    render_template,
    redirect,
    flash,
    url_for,
    session
)

from datetime import timedelta
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError

from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

from main import create_app, db, login_manager, bcrypt
from models import User
from forms import login_form, register_form, import_form
import pandas


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


app = create_app()


@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)


@app.route("/", methods=("GET", "POST"), strict_slashes=False)
def index():
    return render_template("index.html", title="Home")


@app.route("/importar", methods=("GET", "POST"), strict_slashes=False)
def importar():
    form1 = import_form()

    if form1.validate_on_submit():
        try:
            filename = form1.file.data
            dados = pandas.read_excel("prd.xlsx", engine="openpyxl")
            dados.to_sql(name='produtos', con=db.engine, index=True,
                         index_label='id', if_exists='replace')
            db.session.commit()
            return redirect(url_for('produtos'))
        except Exception as e:
            print(e, "Perigo")
    return render_template("import.html", form1=form1,
                           text="Importar",
                           title="Importar",
                           btn_action="Importar")


@app.route("/produtos", methods=("GET", "POST"), strict_slashes=False)
def produtos():
    try:
        # prod = db.session.query(produtos).all()
        produtos = pandas.read_sql_table('produtos', con=db.engine)
        # print(produtos)
        table1 = produtos.to_html(index=False, justify='left', decimal=',',
                                  classes='table table-bordered table-sm small')
        # return redirect(url_for('produtos'))
        return render_template("produtos.html", table1=table1,
                               text="Produtos",
                               title="Produtos",
                               btn_action="Home")
    except Exception as e:
        print(e, "Erro")
    return render_template("index.html", title="Home")


@app.route("/login/", methods=("GET", "POST"), strict_slashes=False)
def login():
    form = login_form()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if check_password_hash(user.pwd, form.pwd.data):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash("Invalid Username or password!", "danger")
        except AttributeError:
            flash(f"Invalid username or password!", "danger")
        except Exception as e:
            flash(e, "danger")

    return render_template("auth.html",
                           form=form,
                           text="Login",
                           title="Login",
                           btn_action="Login"
                           )

# Register route


@app.route("/register/", methods=("GET", "POST"), strict_slashes=False)
def register():
    form = register_form()
    if form.validate_on_submit():
        try:
            email = form.email.data
            pwd = form.pwd.data
            username = form.username.data

            newuser = User(
                username=username,
                email=email,
                pwd=bcrypt.generate_password_hash(pwd),
            )

            db.session.add(newuser)
            db.session.commit()
            flash(f"Account Succesfully created", "success")
            return redirect(url_for("login"))

        except InvalidRequestError:
            db.session.rollback()
            flash(f"Something went wrong!", "danger")
        except IntegrityError:
            db.session.rollback()
            flash(f"User already exists!.", "warning")
        except DataError:
            db.session.rollback()
            flash(f"Invalid Entry", "warning")
        except InterfaceError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except DatabaseError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except BuildError:
            db.session.rollback()
            flash(f"An error occured !", "danger")
    return render_template("auth.html",
                           form=form,
                           text="Criar conta",
                           title="Register",
                           btn_action="Cadastrar conta"
                           )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
