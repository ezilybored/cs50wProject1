import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

""" Function to import the CSV data """
def main():
    b = open("books.csv")
    b_reader = csv.reader(b)
    for isbn, title, author, year in b_reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Added book with {isbn} and {title} written by {author} in the year {year}.")
    db.commit()

if __name__ == "__main__":
    main()
