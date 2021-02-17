import sqlite3
import secrets
from werkzeug.security import generate_password_hash


db = sqlite3.connect("main.db")
db_c = db.cursor()

db_c.execute("CREATE TABLE games ("
            "game_id TEXT PRIMARY KEY,"
            "date TEXT NOT NULL,"
            "num_correct INTEGER NOT NULL,"
            "num_total INTEGER NOT NULL"
            ");")
db_c.execute("CREATE TABLE users ("
            "username TEXT NOT NULL,"
            "displayname TEXT NOT NULL,"
            "hash TEXT NOT NULL"
            ");")
db_c.execute("CREATE TABLE config ("
            "property TEXT NOT NULL,"
            "value TEXT NOT NULL"
            ");")

secret_key = secrets.token_urlsafe(16)
db_c.execute("INSERT INTO config VALUES (?, ?)", ["secret_key", secret_key])
db.commit()

while True:
    username = input("Username (type exit to exit):")
    if username == "exit":
        break
    displayname = input("Displayed name:")
    password = input("Password:")
    pwd_hash = generate_password_hash(password)
    db_c.execute("INSERT INTO users VALUES (?, ?, ?)", [username, displayname, pwd_hash])
    db.commit()
    print("User {} added.".format(username))
