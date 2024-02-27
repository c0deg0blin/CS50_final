
import os
# from readline import insert_text
from cs50 import SQL
from flask import Flask
# from flask import Flask, flash, jsonify, redirect, render_template, request, session
import json

DB_NAME = "TripPacker"

def create_database(db_name):
    """
    Connect to the SQLite database. Also, create the database
    file if it doesn't already exist.
    """
    if not os.path.isfile(f"{db_name}.db"):
        open(f"{db_name}.db", "w").close()
        
    # Connect to SQLite database
    db = SQL(f"sqlite:///{db_name}.db")
    
    return db

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Connect to SQLite database
db = create_database(DB_NAME)
# db = SQL(f"sqlite:///{DB_NAME}.db")

# Create the packing list table, empty
db.execute(
    """
    CREATE TABLE IF NOT EXISTS packingList (
        item TEXT,
        quantity INTEGER,
        category TEXT,
        luggage TEXT,
        packed INTEGER
    );
    """
)

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