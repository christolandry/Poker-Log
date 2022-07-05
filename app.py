from csv import reader
from io import TextIOWrapper
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

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

# Ensure responses aren't cached | Credit: Harvard's CS50 Finanace
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter | Credit: Harvard's CS50 Finanace
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies) | Credit: Harvard's CS50 Finanace
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
@login_required
def index():
    """Show overview of players"""
    
    return render_template("index.html", players = get_players())


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # -----Check username & password requirements------
        # Ensure username was submitted and that it's unique
        db.execute("SELECT * FROM users WHERE username = '%s'" % (username))
        duplicates = db.fetchall()
        if username == "" or len(duplicates) > 0:
            return apology("must provide a unique username", 400)

        # Ensure password was submitted and it matches the confirmation password
        if password == "" or password != confirmation:
            return apology("must provide password and have the password match the confirmation password", 400)

        # Require password to be at least 8 characters in length
        elif len(password) < 8:
            return apology("Password must be at least 8 characters in length", 400)

        # Require user's passwords to have some number of letters, numbers, and/or symbols.
        elif password.isalpha():
            return apology("Password must contain numbers and/or symbols")

        # Find the highest db number and add one to be this db number for the user table
        db.execute("SELECT db FROM users ORDER BY db DESC LIMIT 1")
        currentHighestDb = db.fetchone()

        newDb = 1 if currentHighestDb == None else int(currentHighestDb[0]) + 1

        # Add new user: insert username and hashed password, db, & invite string
        sql = """INSERT INTO users(username, hash, db) VALUES (%s, %s, %s)""" 
        db.execute(sql, (username, generate_password_hash(password), newDb))
        conn.commit()

        # Get user id number
        db.execute("SELECT id FROM users WHERE username = '%s'" % (username))
        rows = db.fetchone()
        
        # Log user in
        session["user_id"] = rows[0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        db.execute("SELECT id, hash FROM users WHERE username = '%s'" % request.form.get("username"))
        rows = db.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][1], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Log User In
        session["user_id"] = rows[0][0]

        # Redirect user to home page
        return render_template("index.html", players = get_players())

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/newplayer", methods=["GET", "POST"])
@login_required
def newplayer():
    """Enter player data"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        players_db = get_db()     

        sql = """INSERT INTO players (name, players_db, balance, nlh_cum, plo_cum, time_cum, venmo, cashapp, paypal, zelle, applepay, note) VALUES (%s, %s, 0, 0, 0, 0, %s, %s, %s, %s, %s, %s)"""
        db.execute(sql, (request.form.get("name"), players_db, request.form.get("venmo"), request.form.get("cashapp"), request.form.get("paypal"),
                         request.form.get("zelle"), request.form.get("applepay"), request.form.get("note")))
        conn.commit()

        return render_template("index.html", players = get_players())

    else:
        return render_template("newplayer.html")


@app.route("/addgame", methods=["GET", "POST"])
@login_required
def addgame():
    """Add a new game to the database"""
    poker_group = get_db()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        db.execute("SELECT player_id FROM players WHERE name = '%s'" % (request.form.get("bank")))
        bankID = db.fetchone()

        if bankID is None:
            return apology("must choose a player for bank", 400)

        #Insert the game into the games table
        sql = """INSERT INTO games (games_db, date, type, bigblind, table_number, bank, track_money) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        db.execute(sql, (poker_group, request.form.get("date"), request.form.get("type"), request.form.get("bigblind"),
                         request.form.get("table_num"), bankID[0], request.form.get("trackmoney")))
        conn.commit()

        # How to upload files: https://gist.github.com/dasdachs/69c42dfcfbf2107399323a4c86cdb791
        csv_file = request.files['fileupload']
        csv_file = TextIOWrapper(csv_file, encoding='utf-8')
        csv_reader = reader(csv_file, delimiter=',')

        db.execute("SELECT game_id FROM games WHERE games_db = '%s' ORDER BY game_id DESC LIMIT 1" % (poker_group))
        game_id = db.fetchone()
        game_id = game_id[0]
        counter = 0

        # Read the csv and insert each player into a sessions tab.
        for row in csv_reader:
            if counter:
                    buyin = round(float(row[4])/100,2)
                    buyout = round(float(row[5])/100,2) if row[5] else ""
                    stack = round(float(row[6])/100,2) if row[6] else ""
                    net = round(float(row[7])/100,2)
                    db.execute("SELECT aliases_player_id FROM aliases WHERE aliases_alias = '%s'" % (row[0]))
                    sessions_player_id = db.fetchone()

                    if sessions_player_id is None:
                        return apology("must enter all aliases before uploading a game", 400)                        

                    sql = """INSERT INTO sessions (sessions_game_id, sessions_player_id, alias, buyin, buyout, stack, net) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                    db.execute(sql, (game_id, sessions_player_id[0], row[0], buyin, buyout, stack, net))
                    conn.commit()
            counter += 1

        return redirect("/games")

    else:
        return render_template("addgame.html", players = get_players(), games = get_games())


@app.route("/games", methods=["GET", "POST"])
@login_required
def games():
    """Shows Games"""
    poker_group = get_db()

    # get the dates games happend so they can be selected in the drop down menu.
    db.execute("SELECT date FROM games WHERE games_db = '%s' GROUP BY date ORDER BY date DESC LIMIT 10" % (poker_group))
    gamedates = toList(db.description, db.fetchall())

    # date of game requested, default is the lastest date a game was played if a date wasn't requested
    request_date = request.form.get("date")
    db.execute("SELECT date FROM games WHERE games_db = '%s' ORDER BY date DESC LIMIT 1" % (poker_group))
    latest_date = db.fetchone()
    if latest_date is None:
        return render_template("games.html")
    date = request_date if request_date else latest_date[0]

    # get game ids from that date.
    db.execute("SELECT * FROM games WHERE (date = '%s' AND games_db = '%s') ORDER BY table_number" % (date, poker_group))
    games = toList(db.description, db.fetchall())

    # get all players who played on the date in question.
    players = []
    for row in games:
        db.execute("SELECT name FROM players JOIN sessions ON players.player_id = sessions.sessions_player_id WHERE (sessions_game_id = '%s' AND players_db = '%s')" % (row["game_id"], poker_group))
        players += toList(db.description, db.fetchall())

    # create a list of unique players by removing the duplicates from players
    seen = set()
    unique_players = []

    for row in players:
        if row["name"] not in seen:
            seen.add(row["name"])
            unique_players.append({"name": row["name"]})

    # add in a nested directory called "gamenet" that has the net result of each player for each table.  If they didn't play for a table it enters "".
    for unique_player in unique_players:
        net = 0
        for game in games:
            # Get the net result for the current player at the current table.
            db.execute("SELECT aliases_player_id FROM aliases WHERE aliases_alias = '%s'" % (unique_player["name"]))
            player_id = db.fetchone()
            db.execute("SELECT net FROM sessions WHERE sessions_player_id = '%s' AND sessions_game_id = '%s'" % (player_id[0], game["game_id"]))
            gamenet = db.fetchone()

            # Deal with the case that not all players play on all tables
            table_net = str(gamenet[0]) if gamenet[0] else ""

            # Add result to the nested dictionary of that player.
            unique_player.setdefault("game_nets", []).append(table_net)

            # Increase the day's net value for the result of that game
            net += gamenet[0] if gamenet[0] else 0

        # The net result for current player for the date in question.
        unique_player["net"] = net

    # Sort players by the total amount they made on the date in question
    unique_players = sorted(unique_players, key = lambda i: i["net"], reverse=True)

    return render_template("games.html", players = unique_players, gamedates = gamedates, games = games)

@app.route("/alias", methods=["GET", "POST"])
@login_required
def alias():
    """Enter new alias/name pairs"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        alias = request.form.get("alias")
        name = request.form.get("name")
        add_another = request.form.get("add_another")

        db.execute("SELECT player_id FROM players WHERE name = '%s'" % (name))
        playerID = db.fetchone()

        sql = """INSERT INTO aliases (aliases_player_id, aliases_alias) VALUES (%s,%s)"""
        db.execute(sql, (playerID[0], alias))
        conn.commit()

        if add_another == "1":
            return render_template("alias.html", players = get_players())
        else:
            return render_template("index.html", players = get_players())

    else:
        return render_template("alias.html", players = get_players())


@app.route("/player", methods=["GET", "POST"])
@login_required
def player():
    """Shows Games"""
    # get the names of all the players so they can be selected in the drop down menu.
    poker_group = get_db()
    db.execute("SELECT name FROM players WHERE players_db = '%s' ORDER BY name" % (poker_group))
    allPlayers = toList(db.description, db.fetchall())
    netTotal = 0

    if request.method == "POST":
        targetPlayer = request.form.get("player")
        
        # get the game info and results from all games played by selected person.
        db.execute("SELECT game_id, date, type, bigblind, table_number FROM games JOIN sessions ON games.game_id = sessions.sessions_game_id JOIN players ON sessions.sessions_player_id = players.player_id WHERE (name = '%s' AND games_db = '%s')" % (targetPlayer, poker_group))
        games = toList(db.description, db.fetchall())
        
        # add in the net to each game they played and add it to the player's total
        for game in games:
            db.execute("SELECT net FROM sessions WHERE sessions_game_id = '%s'" % (game["game_id"]))
            net = toList(db.description, db.fetchall())
            net = float(net[0]["net"])
            game["net"] = net
            netTotal += net

        return render_template("player.html", players = allPlayers, targetPlayer = targetPlayer, total = netTotal, games = games)

    else:

        return render_template("player.html", players = allPlayers, total = netTotal)

#--------------Addtional Functions---------------------

# Returns the players in the appropriate poker group in a list of dictionaries sorted by No Limit Hold'em cumlative winnings.
def get_players():
    db.execute("SELECT * FROM players WHERE players_db = '%s'" % (get_db())) 
    players = toList(db.description, db.fetchall())
    return sorted(players, key = lambda i: i["nlh_cum"], reverse=True)

# Returns the db of the current user
def get_db():
    db.execute("SELECT db FROM users WHERE id = '%s'" % (session["user_id"]))
    db_num = db.fetchone()
    return db_num[0]

# gets the last 10 games from current user's poker group
def get_games():
    db.execute("SELECT * FROM games WHERE games_db = '%s' ORDER BY (date) DESC LIMIT 10" % (get_db()))
    return toList(db.description, db.fetchall())

# creates list of dictionaries out of the tuple with column titles for keys.
def toList(titles, data):
    listOfDictionaries= []
    for item in range(len(data)):
        pair = {}
        for column in range(len(data[item])):
            pair[titles[column][0]] = data[item][column]
        listOfDictionaries.append(pair)
    return listOfDictionaries

def errorhandler(e): #| Credit: Harvard's CS50 Finanace
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors | Credit: Harvard's CS50 Finanace
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=5000)