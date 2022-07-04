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

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
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