
import os
# from cs50 import SQL
import sqlite3
from struct import pack
from flask import Flask, flash, jsonify, redirect, render_template, request, session, g
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
        db.execute(insert_stmt, (
                d["item"],
                d["quantity"],
                d["category"],
                d["luggage"],
                d["packed"]
            )
        )


def db_connect(db_name):
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
    conn = sqlite3.connect(f"{db_name}.db")
    db = conn.cursor()
    
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
        # db.commit()
    
    return conn, db

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.before_request
def before_request():
    g.conn, g.db = db_connect(DB_NAME)
    
    
@app.teardown_appcontext
def teardown_request(exception):
    if hasattr(g, "db"):
        g.db.close()
        

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        print("======")
        print("<POST>")
        print("======")
        id_value = request.form.get('idValue')
        checked_val = request.form.get('isChecked')
        print("==============")
        print(checked_val)
        print(id_value)
        print("==============")
        return jsonify(message="Checkbox ID received successfully")
        
        # Update database with new checkbox state
        # g.db.execute(
        #     """
        #     UPDATE packingList
        #     SET packed = ?
        #     WHERE id = ?;
        #     """,
        #     (packed_val,
        #      id)
        # )
            
        # if packed_val:
        #     print("Checked")
        # else:
        #     print("Unchecked")
        # row_number = request.form.get('row')
        # print(row_number)
        # return redirect("/")
    else:
        print("===")
        print("GET")
        print("===")
        # Get all rows from the table
        g.db.execute("SELECT * FROM packingList;")
        # Fetch all rows returned by the last query result
        row_list = g.db.fetchall()
        
        # Get the column names ("db.description" provides the column names
        # of the last select query as a list of tuples where the first item
        # is the column name)
        column_names = [description[0] for description in g.db.description]
        
        # Stores rows as list of dictionaries, for easier management in HTML
        rows = []
        for row in row_list:
            i = 0
            tmp_dict = {}
            while i < len(column_names):
                tmp_dict[column_names[i]] = row[i]
                i += 1
            rows.append(tmp_dict)
        
        return render_template("index.html", column_names=column_names, rows=rows)
