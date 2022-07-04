from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from helpers import apology, login_required, usd

# Connect to RDS
import pymysql

conn = pymysql.connect(
        host= 'pokerlog.chaddfkmxw3n.us-east-1.rds.amazonaws.com', 
        port = 3306,
        user = 'masterUsername', 
        password = 'KgxVzgz&GKefK6Qk^W28',
        db = 'poker_log',
        )
db = conn.cursor()

# Configure application
app = Flask(__name__)

@app.route("/")
@login_required
def index():
    """Show overview of players"""
    
    return render_template("index.html", players = get_players())

#--------------Addtional Functions---------------------

# Returns the players in the appropriate poker group in a list of dictionaries sorted by No Limit Hold'em cumlative winnings.
def get_players():
    db.execute("SELECT * FROM players WHERE players_db = '%s'" % (get_db())) 
    players = toList(db.description, db.fetchall())
    return sorted(players, key = lambda i: i["nlh_cum"], reverse=True)

def toList(titles, data):
    listOfDictionaries= []
    for item in range(len(data)):
        pair = {}
        for column in range(len(data[item])):
            pair[titles[column][0]] = data[item][column]
        listOfDictionaries.append(pair)
    return listOfDictionaries

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)