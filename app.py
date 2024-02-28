
import os
# from readline import insert_text
from cs50 import SQL
from flask import Flask, render_template
# from flask import Flask, flash, jsonify, redirect, render_template, request, session
import json

DB_NAME = "TripPacker"

def insert_tmp_data(db):
    
    # Load template packing list from json
    with open("static/packingList_template.json", "r") as f:
        tmp_packingList = json.load(f)

    # Prepare the insert statement
    insert_stmt = """
    INSERT INTO packingList (item, quantity, category, luggage, packed)
    VALUES(?, ?, ?, ?, ?)
    """

    # Execute the statement for each item
    for d in tmp_packingList:
        db.execute(insert_stmt, 
            d["item"],
            d["quantity"],
            d["category"],
            d["luggage"],
            d["packed"]
        )


def create_database(db_name):
    """
    Connect to the SQLite database. Also, create the database
    file if it doesn't already exist.
    """
    # Check if database already exists
    db_exists = os.path.isfile(f"{db_name}.db")
    
    # If it doesn't exist, create it
    if not db_exists:
        open(f"{db_name}.db", "w").close()
        
    # Connect to SQLite database
    db = SQL(f"sqlite:///{db_name}.db")
    
    # If the db file is new, create the packing
    # list table, empty.
    # TMP: Pre-populate table for testing purposes
    if not db_exists:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS packingList (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
                item TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                category TEXT NOT NULL,
                luggage TEXT NOT NULL,
                packed INTEGER NOT NULL
            );
            """
        )
        insert_tmp_data(db)
    
    return db

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Connect to SQLite database
db = create_database(DB_NAME)


@app.route("/", methods=["GET", "POST"])
def index():
    # Get all rows from the table
    rows = db.execute("SELECT * FROM packingList;")
    
    # Check if there are any rows returned
    if len(rows) > 0:
        # Get the column names
        column_names = rows[0].keys()
    else:
        column_names = []
        
    return render_template("index.html",
                           column_names=column_names,
                           rows=rows)
