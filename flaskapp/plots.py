import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates
from matplotlib.dates import MO, TU, WE, TH, FR, SA, SU
import dateutil.parser
from datetime import datetime, timedelta
import numpy as np
import io
import base64
from scipy.interpolate import interp1d
import sqlite3


windowSize = 5
plt.rcParams.update({"font.size": 12})


def moving_average(x, w):
    if len(x) < w:
        return []
    return np.convolve(x, np.ones(w), 'valid') / w


def fetch_data(db_c, game_nwords, username):
    db_c.execute("SELECT date, num_correct FROM games"
        " WHERE user=? AND num_total=?"
        " ORDER BY date ASC",
        [username, game_nwords])
    rows = db_c.fetchall()
    dates, scores = [], []
    for date, num_correct in rows:
        date_o = dateutil.parser.isoparse(date)
        date_p = matplotlib.dates.date2num(date_o)
        dates.append(date_p)
        scores.append(num_correct)
    data_x = np.array(dates, dtype=np.float64)
    data_y = np.array(scores, dtype=np.float64)
    return data_x, data_y


def plot_data_all(dates, scores, game_nwords):
    dates_ma = dates[(windowSize-1):]
    scores_ma = moving_average(scores, windowSize)
    plt.scatter(dates, scores, color="blue", label="Spiel")
    plt.plot(dates_ma, scores_ma, color="orange", label="Mittel letzte {} Spiele".format(windowSize))
    plt.yticks(np.arange(0, game_nwords + 1))
    # ensure reasonable plot limits if we have fewer than 2 data points
    if len(dates) == 0:
        xmin = matplotlib.dates.date2num(datetime.now() - timedelta(days=1))
        xmax = matplotlib.dates.date2num(datetime.now() + timedelta(hours=1))
        plt.xlim(xmin, xmax)
    if len(dates) == 1:
        single_date = matplotlib.dates.num2date(dates[0])
        xmin = matplotlib.dates.date2num(single_date - timedelta(days=1))
        xmax = matplotlib.dates.date2num(single_date + timedelta(hours=1))
        plt.xlim(xmin, xmax)
    plt.ylim(-0.1, game_nwords + 0.1)
    plt.grid()
    plt.legend()
    plt.gca().xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b %Y %H:%M"))
    for label in plt.gca().get_xticklabels():
        label.set_rotation(45)
    plt.gcf().set_size_inches(10, 5)
    plt.xlabel("Zeitpunkt")
    plt.ylabel("Richtige Wörter")
    plt.legend()
    plt.tight_layout()


def format_weekday(mpldate, pos=None):
    date = matplotlib.dates.num2date(mpldate)
    days_names = ["Mon", "Die", "Mit", "Don", "Fre", "Sam", "Son"]
    return days_names[date.weekday()]


def plot_data_week(dates, scores, game_nwords):
    dates_ma = dates[(windowSize-1):]
    scores_ma = moving_average(scores, windowSize)
    xmin = matplotlib.dates.date2num(datetime.now() - timedelta(days=7))
    xmax = matplotlib.dates.date2num(datetime.now() + timedelta(hours=1))
    plt.xlim(xmin, xmax)
    plt.ylim(-0.1, game_nwords + 0.1)
    plt.yticks(np.arange(0, game_nwords + 1))
    plt.scatter(dates, scores, color="blue", label="Spiel")
    plt.plot(dates_ma, scores_ma, color="orange", label="Mittel letzte {} Spiele".format(windowSize))
    plt.grid()
    plt.legend()
    plt.gca().xaxis.set_major_locator(matplotlib.dates.WeekdayLocator(byweekday=(MO, TU, WE, TH, FR, SA, SU)))
    plt.gca().xaxis.set_major_formatter(format_weekday)
    for label in plt.gca().get_xticklabels():
        label.set_rotation(90)
    plt.gcf().set_size_inches(10, 4)
    plt.xlabel("Wochentag")
    plt.ylabel("Richtige Wörter")
    plt.legend()
    plt.tight_layout()


def plot_data_month(dates, scores, game_nwords):
    dates_ma = dates[(windowSize-1):]
    scores_ma = moving_average(scores, windowSize)
    xmin = matplotlib.dates.date2num(datetime.now() - timedelta(days=30))
    xmax = matplotlib.dates.date2num(datetime.now() + timedelta(hours=8))
    plt.xlim(xmin, xmax)
    plt.ylim(-0.1, game_nwords + 0.1)
    plt.yticks(np.arange(0, game_nwords + 1))
    plt.scatter(dates, scores, color="blue", label="Spiel")
    plt.plot(dates_ma, scores_ma, color="orange", label="Mittel letzte {} Spiele".format(windowSize))
    plt.grid()
    plt.legend()
    plt.gca().xaxis.set_major_locator(matplotlib.dates.DayLocator(bymonthday=range(1, 32)))
    plt.gca().xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d"))
    for label in plt.gca().get_xticklabels():
        label.set_rotation(90)
    plt.gcf().set_size_inches(10, 4)
    plt.xlabel("Tag")
    plt.ylabel("Richtige Wörter")
    plt.legend()
    plt.tight_layout()


def plot_as_base64():
    img = io.BytesIO()
    plt.savefig(img, format="png", dpi=150)
    img.seek(0)
    img_b64 = base64.b64encode(img.read()).decode("ascii")
    img_html = '<img class="img-fluid" src="data:image/png;base64, ' + img_b64 + '" />'
    return img_html


def get_plot_all(db_c, game_nwords, username):
    plt.clf()
    data = fetch_data(db_c, game_nwords, username)
    plot_data_all(*data, game_nwords)
    return plot_as_base64()


def get_plot_week(db_c, game_nwords, username):
    plt.clf()
    data = fetch_data(db_c, game_nwords, username)
    plot_data_week(*data, game_nwords)
    return plot_as_base64()


def get_plot_month(db_c, game_nwords, username):
    plt.clf()
    data = fetch_data(db_c, game_nwords, username)
    plot_data_month(*data, game_nwords)
    return plot_as_base64()


# run test code if not imported
if __name__ == "__main__":
    db = sqlite3.connect("main.db")
    db_c = db.cursor()
    game_nwords = 3
    # ~ data = fetch_data_all(db_c, 3, "test")
    # ~ print(data)
    print(get_plot_all(db_c, game_nwords, "test"))
