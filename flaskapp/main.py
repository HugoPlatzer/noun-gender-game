from flask import Flask, jsonify, request, redirect, send_from_directory, render_template
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from random import choice
from pyphen import Pyphen
import sqlite3
from datetime import datetime
import json
import os
import dateutil.parser
import logging

import plots


def db_init():
    db = sqlite3.connect("main.db")
    db_c = db.cursor()
    return db, db_c


def hyphenate(word):
    return hyphen_dic.inserted(word, hyphen="&shy;")


def load_config(prop):
    db_c.execute("SELECT value FROM config WHERE property=?", [prop])
    data = db_c.fetchone()
    return data[0]


def find_story_filenames():
    fns = []
    for fn in os.listdir("templates/stories"):
        name, ext = os.path.splitext(fn)
        if ext == ".html":
            fns.append("stories/" + fn)
    return fns


def load_story_users():
    users = load_config("story_users")
    return users.split(",")


def data_lastgames():
    db_c.execute("SELECT date, num_correct, num_total FROM games"
        " WHERE user=?"
        " ORDER BY date DESC"
        " LIMIT 3",
        [current_user.get_id()])
    rows = db_c.fetchall()
    games = []
    for date, num_correct, num_total in rows:
        date_p = dateutil.parser.isoparse(date)
        date_h = date_p.strftime("%d %b %Y %H:%M")
        perfect = (num_correct == num_total and num_total == game_nwords)
        result_s = "{}/{}".format(num_correct, num_total)
        games.append({"date": date_h, "perfect": perfect, "result": result_s})
    return games


class User:
    def __init__(self, username, displayname, pwd_hash):
        self.username = username
        self.displayname = displayname
        self.pwd_hash = pwd_hash
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def check_password(self, password):
        return check_password_hash(self.pwd_hash, password)
    
    def get_id(self):
        return self.username


import logging
logging.basicConfig(filename="log.txt",
    level=logging.INFO,
    format="%(asctime)s %(message)s")

db, db_c = db_init()
app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
app.secret_key = load_config("secret_key")
login_manager = LoginManager(app)

game_nwords = int(load_config("nwords"))
wordlist_file = "res/wordlists/de.txt"
words = [l.split() for l in open(wordlist_file).readlines()]
article_choices = ["der", "die", "das"]
hyphen_dic = Pyphen(lang="de_DE")
story_users = load_story_users()
story_filenames = find_story_filenames()


@login_manager.user_loader
def load_user(username):
    db_c.execute("SELECT username,displayname,hash from users WHERE username=?", [username])
    data = db_c.fetchone()
    if data is None:
        return None
    return User(data[0], data[1], data[2])


@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def page_login():
    logging.info("LOGIN " + str(request.remote_addr))
    if current_user.is_authenticated:
        logging.info("isauth")
        return redirect("/")
    if request.method == "GET":
        logging.info("get")
        return send_from_directory("static", "login.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        user = load_user(username)
        if user is not None and user.check_password(password):
            login_user(user, remember=True)
            logging.info("successful for user " + str(user.get_id()))
            return redirect("/")
        else:
            logging.info("unsuccessful")
            return redirect("/login")


@app.route("/logout")
@login_required
def page_logout():
    logging.info("LOGOUT " + str(request.remote_addr))
    logout_user()
    return redirect("/login")


@app.route("/")
@login_required
def page_root():
    return redirect("/main")


@app.route("/main")
@login_required
def page_main():
    logging.info("MAIN " + str(request.remote_addr))
    return render_template("main.html",
    lastgames=data_lastgames(),
    plotAll=plots.get_plot_all(db_c, game_nwords, current_user.get_id()),
    plotWeek=plots.get_plot_week(db_c, game_nwords, current_user.get_id()),
    plotMonth=plots.get_plot_month(db_c, game_nwords, current_user.get_id())
    )


@app.route("/game")
@login_required
def page_game():
    logging.info("GAME " + str(request.remote_addr))
    return render_template("game.html", nwords=game_nwords)


@app.route("/word")
@login_required
def service_word():
    article, noun = choice(words)
    logging.info("WORD " + str(request.remote_addr) + " " + article + " " + noun)
    return jsonify({"article_choices" : article_choices,
                    "article" : article, 
                    "noun" : noun,
                    "noun_hyphen" : hyphenate(noun)
                    })


@app.route("/word-result", methods=["POST"])
@login_required
def service_word_result():
    game_id = request.json["gameId"]
    is_correct = request.json["correct"]
    logging.info("WORDRESULT " + str(request.remote_addr) + " " + game_id + " " + str(is_correct))
    db_c.execute("SELECT num_correct, num_total from games WHERE game_id=?", [game_id])
    data = db_c.fetchone()
    if data is None:
        old_correct = 0
        old_total =  0
        date = datetime.now().isoformat()
        db_c.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?)",
            [game_id, current_user.get_id(), date, 0, 0])
    else:
        old_correct = data[0]
        old_total = data[1]
    if is_correct:
        new_correct = old_correct + 1
    else:
        new_correct = old_correct
    new_total = old_total + 1
    db_c.execute("UPDATE games SET num_correct=?,num_total=? WHERE game_id=?", [new_correct, new_total, game_id])
    db.commit()
    return jsonify(success=True)


@app.route("/report/<game_id>", methods=["POST"])
@login_required
def service_report(game_id):
    answers = json.loads(request.form.get("data"))
    
    logging.info("REPORT " + str(request.remote_addr) + " " + str(game_id))
    logging.info("answers: " + str(answers))
    
    db_c.execute("SELECT num_correct, num_total from games WHERE game_id=?", [game_id])
    data = db_c.fetchone()
    if data is None:
        num_correct, num_total = 0, 0
    else:
        num_correct, num_total = data[0], data[1]
    message = "{}/{} Artikel richtig".format(num_correct, num_total)
    if num_correct != num_total:
        submessage = "Fehler:"
    elif num_total < game_nwords:
        submessage = "Spiel abgebrochen"
    else:
        submessage = "Gut gemacht!"
    
    mistakes = []
    for answer in answers:
        if answer["guessedArticle"] != answer["correctArticle"]:
            mistakes.append({"article": answer["correctArticle"], "word": answer["noun_hyphen"]})
    
    if (    current_user.get_id() in story_users
            and num_correct == num_total
            and num_total == game_nwords
            and len(story_filenames) >= 1):
        story_file = story_filenames[hash(game_id) % len(story_filenames)]
    else:
        story_file = ""
    
    is_flawless = (num_correct == num_total and num_total == game_nwords)
    logging.info("flawless: " + str(is_flawless) + ", story file: " + story_file)
    
    return render_template("report.html",
        message=message,
        submessage=submessage,
        has_mistakes=(len(mistakes) > 0),
        flawless=is_flawless,
        mistakes=mistakes,
        story_file=story_file)
    
