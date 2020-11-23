from flask import Flask, jsonify, redirect, send_from_directory
from random import choice

app = Flask(__name__)

wordlist_file = "res/wordlist.txt"
words = [l.split() for l in open(wordlist_file).readlines()]

@app.route("/")
def main_page():
    return redirect("/game")

@app.route("/game")
def game_page():
    return send_from_directory("static", "game.html")

@app.route("/word")
def get_random_word():
    article, noun = choice(words)
    return jsonify({"article" : article, "noun" : noun})
