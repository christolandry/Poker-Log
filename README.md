# Poker Log: A fullstack web app to track a poker groups results over time hosted on AWS Lightsail with an database on AWS RDS.

**Problem:** I play poker with the same group of people on a website called pokernow.club.  The host of our group wanted to track the results of people over time in a clean and concise format, which we didn’t have. 

**Solution:**
This project allows users to register, add the players in their group, add the aliases each player uses each game, and then upload the ledger file (.csv) from each game to keep track of player results.  Results can be viewed by cumulative player results, individual player results showing each game they played in, and the results of all games on a specific day.

**Link to project:** [poker-log-service.efjajuvn60chi.us-east-1.cs.amazonlightsail.com)
![alt tag](images/charlotteAstrophiles.gif)

## How It's Made:

**Tech used:** Python, Flask, Jinja, MySQL (AWS RDS), AWS Lightsail (in a Docker container), HTML, CSS

<h6>Index</h6>
<p>Displays all players in your poker group (each user has their own poker group) with their poker results, payment info, and a note.  It is sorted by each player's No Limit Hold'em cumlative results</p>
<h6>Add Player</h6>
<p>This page adds a player to the correct poker group along with their associated information</p>
<h6>Add Alias</h6>
<p>Each player an choose their own name each time they play.  This associates the nickname a player choose in game to the name listed as a player in the database</p>
<h6>Add Game</h6>
<p>Takes in information about the game and the ledger .csv file to enter in the results of each game</p>
<h6>Games</h6>
<p>Shows the results of all games on a choosen date (multiple tables can be in play, each uploaded as their own game)</p>
<h6>Players</h6>
<p>Displays each game a player has played in along with the result.</p>


### Sources
<p>Ensuring responses aren't cached, custom jinja filter, session configuration, error reporting, & helpers.py: from Harvard's CS50 Finance problem set</p>
<p>Code to upload .csv files: gist.github.com/dasdachs/69c42dfcfbf2107399323a4c86cdb791</p>
<p>AWS Lightsail flask upload using a Docker Container: AWS Tutorial</p>

## Lessons Learned:

The goal was to host a full-stack web app with the associated database on AWS, which was new to me.  Some of the blockers I faced were trouble installing the required hardware (the path files weren't installing properly on Windows and had to be manually entered), learning Docker, learning MySQL syntax in python (previous experience was with SQLite in python), and learning how to parse an uploaded file in python.  I overcame these blockers though many google searches, reading the documentation, and testing.

## Optimizations:
<ul>
  <li>Add an environmental variable for the password to the database in used in app.py</li>
  <li>Database structure concerning the association of player Id's and the aliases they used in game is a not correct.  It will not work at scale as it doesn't allow for duplicate aliases.</li>
  <li>Track Payments to make sure everyone has paid up / received their money each game</li>
  <li>Make the wesite responsive</li>
  <li>Allow multiple log ins to the same poker group with read/write permissions</li>
</ul>

## Examples:
Take a look at these couple examples that I have in my own portfolio:

**Portfolio Page:** https://github.com/christolandry/Portfolio

**Charlotte Astrophiles:** https://github.com/christolandry/Charlotte-Astrophiles

**Happy Tails Dog Grooming:** https://github.com/christolandry/Happy-Tails

**Ascent Running Camp:** https://github.com/christolandry/AscentRunningCamp

**Professional Runner (retired):** https://ChristoLandry.com

**Ascent Running Coaching:** https://AscentRunningCoaching.com
