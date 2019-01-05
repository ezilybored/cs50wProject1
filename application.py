import os
import re

from flask import Flask, session, redirect, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://zknipddgcabidt:bf8fd27a6ffbb8766fb69776c0b72fbff3b7ebe42f015763640fc78e6ae986a4@ec2-54-247-74-131.eu-west-1.compute.amazonaws.com:5432/d82fdubfunhhd3'
db = SQLAlchemy(app)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
key = 'hn6qthr2yr3Wjug8GZjaIQ'
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


"""Register user"""
@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()

    if request.method == "POST":

        get_password = request.form.get("password")
        get_newuser = request.form.get("username")
        get_email = request.form.get("email")

        # Checks to see if the username already exists
        check = db.execute("SELECT * FROM users WHERE username = :username", {"username": get_newuser}).fetchall()

        if check:
            return render_template("error.html", error = "Username already exists")

        insert = db.execute("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)",
                            {"username": get_newuser, "email": get_email, "password": generate_password_hash(get_password)})
        db.commit()

        return render_template("registered.html")

    else:
        return render_template("register.html")


"""User Log in"""
@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()
    get_password = request.form.get("password")
    get_newuser = request.form.get("username")

    if request.method == "POST":
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", {"username": get_newuser}).fetchall()

        # Ensure username exists and password is correct using check_password_hash from werkzeug.security
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], get_password):
            return render_template("error.html", error = "Incorrect password")

        session["user_id"] = rows[0]["userid"]

        return render_template("index.html")

    else:
        return render_template("login.html")


"""Log user out"""
@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


""" The user home page """
@app.route("/", methods=["GET", "POST"])
def index():
    if not session:
        # Requires a search function to look up books
        return render_template("register.html")
    else:
         return render_template("index.html")


""" The search function """
@app.route("/search", methods=["GET", "POST"])
def search():
    isbn = request.form.get("isbn")
    title = request.form.get("title")
    author = request.form.get("author")

    if isbn:
        # Search books database using isbn
        result = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn", {"isbn": ('%' + isbn + '%')}).fetchall()
        print(result)
        return render_template("index.html", books=result)

    elif title:
        # Search books database using title
        result = db.execute("SELECT * FROM books WHERE title LIKE :title", {"title": ('%' + title + '%')}).fetchall()
        print(result)
        return render_template("index.html", books=result)

    elif author:
        # Search books database using author
        result = db.execute("SELECT * FROM books WHERE author LIKE :author", {"author": ('%' + author + '%')}).fetchall()
        print(result)
        return render_template("index.html", books=result)

    else:
        return render_template("index.html")


""" Shows information about each individual book and also shows any previous user reviews and ratings """
@app.route("/bookinfo", methods=["GET", "POST"])
def bookinfo():

    isbn = request.form.get("submit")
    get_user = session["user_id"]
    print("input data is", isbn)
    gread = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
    book = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn", {"isbn": ('%' + isbn + '%')}).fetchone()
    print(gread)
    rating_count = gread.json()["books"][0]["work_ratings_count"]
    rating = gread.json()["books"][0]["average_rating"]

    user_reviews = db.execute("SELECT * FROM comments WHERE isbn = :isbn", {"isbn": isbn}).fetchall()

    return render_template("bookinfo.html", book=book, ratings=rating_count, rating=rating, reviews=user_reviews, isbn=isbn)

""" Recieve and store the users review and rating """
@app.route("/review", methods=["GET", "POST"])
def review():

    # Retrieve the comment
    review = request.form.get("review")
    rating = request.form.get("rating")
    isbn = request.form.get("submit")

    # Store the comment in the table if they have not already commented
    commented = db.execute("SELECT * FROM comments WHERE userid = :userid AND isbn = :isbn", {"userid": session["user_id"], "isbn": isbn}).fetchall()
    if not commented:
        users = db.execute("SELECT * FROM users WHERE userid = :userid", {"userid": session["user_id"]}).fetchall()
        user = users[0]["username"]
        db.execute("INSERT INTO comments (isbn, userid, comment, rating, username) VALUES (:isbn, :userid, :comment, :rating, :username)",
                            {"isbn": isbn, "userid": session["user_id"], "comment": review, "rating": rating, "username": user })
        db.commit()
    else:
        return render_template("error.html", error = "You have already reviewed this book")

    isbn = request.form.get("submit")
    get_user = session["user_id"]
    print("input data is", isbn)
    gread = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
    book = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn", {"isbn": ('%' + isbn + '%')}).fetchone()
    print("book is ", book)
    print("goodread response is ", gread)
    rating_count = gread.json()["books"][0]["work_ratings_count"]
    rating = gread.json()["books"][0]["average_rating"]

    user_reviews = db.execute("SELECT * FROM comments WHERE isbn = :isbn", {"isbn": isbn}).fetchall()

    return render_template("bookinfo.html", book=book, ratings=rating_count, rating=rating, reviews=user_reviews, isbn=isbn)
