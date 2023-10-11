from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import time

movies_api = "21295dc80030af721106a74df0cfbf47"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
db = SQLAlchemy()
db.init_app(app)
Bootstrap5(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True, default=None)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


class Edit(FlaskForm):
    rating = StringField("Your Rating out of 10", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    done = SubmitField("Done")


class Add(FlaskForm):
    title = StringField("Movie Title")
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars().all()
    for i in range(len(movies)):
        movies[i].ranking = len(movies) - i
    db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/add", methods=['GET', 'POST'])
def add():
    add_form = Add()
    if add_form.validate_on_submit():
        movie_title = add_form.title.data
        url = f"https://api.themoviedb.org/3/search/movie?query={movie_title}&include_adult=false&language=en-US&page=1"

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyMTI5NWRjODAwMzBhZjcyMTEwNmE3NGRmMGNmYmY0NyIsInN1YiI6IjY1MTNmYjcxYzUwYWQyMDBhZDdlODU2NyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.y-dFk1__hz59D_VYA9cy_aAdf3-D10Oc3kAduyNrNwY"
        }

        response = requests.get(url, headers=headers)
        movies_by_title = response.json()['results']
        return render_template("select.html", options=movies_by_title)
    return render_template("add.html", form=add_form)


@app.route("/selection")
def selection():
    url = f"https://api.themoviedb.org/3/movie/{request.args.get('movie_id')}?language=en-US"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyMTI5NWRjODAwMzBhZjcyMTEwNmE3NGRmMGNmYmY0NyIsInN1YiI6IjY1MTNmYjcxYzUwYWQyMDBhZDdlODU2NyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.y-dFk1__hz59D_VYA9cy_aAdf3-D10Oc3kAduyNrNwY"
    }

    response = requests.get(url, headers=headers)
    all_movie_details = response.json()
    print(all_movie_details)
    new_movie = Movie(title=all_movie_details["original_title"],
                      img_url=f"{MOVIE_DB_IMAGE_URL}{all_movie_details['poster_path']}",
                      year=all_movie_details["release_date"],
                      description=all_movie_details["overview"],
                      rating=0.0,
                      ranking=None,
                      review=None
                      )
    print(all_movie_details['poster_path'])
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("edit", id=new_movie.id))


@app.route("/edit", methods=['GET', "POST"])
def edit():
    edit_form = Edit()
    movie_id = request.args.get("id")
    if edit_form.validate_on_submit():
        selected_movie = db.get_or_404(Movie, movie_id)
        selected_movie.rating = float(edit_form.rating.data)
        selected_movie.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=edit_form)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    selected_movie = db.get_or_404(Movie, movie_id)
    db.session.delete(selected_movie)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
