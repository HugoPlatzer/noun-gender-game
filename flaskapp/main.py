from flask import Flask, jsonify, redirect, send_from_directory
from random import choice
from pyphen import Pyphen

app = Flask(__name__,
    static_url_path="/static",
    static_folder="static")
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

wordlist_file = "res/wordlist.txt"
words = [l.split() for l in open(wordlist_file).readlines()]
article_choices = ["der", "die", "das"]
hyphen_dic = Pyphen(lang="de_DE")

def hyphenate(word):
    return hyphen_dic.inserted(word, hyphen="&shy;")

@app.route("/")
def page_main():
    return redirect("/static/game.html")

@app.route("/word")
def service_word():
    article, noun = choice(words)
    return jsonify({"article_choices" : article_choices,
                    "article" : article, 
                    "noun" : noun,
                    "noun_hyphen" : hyphenate(noun)
                    })
