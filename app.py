
import os
# from cs50 import SQL
import sqlite3
from struct import pack
from flask import Flask, flash, jsonify, redirect, render_template, request, session, g
import json

DB_NAME = 'TripPacker'
PACKLIST = 'packingList'

def insert_tmp_data(conn):
    
    # Load template packing list from json
    with open('static/packingList_template.json', 'r') as f:
        tmp_packingList = json.load(f)

    # Prepare the insert statement
    insert_stmt = f'''
    INSERT INTO {PACKLIST} (item, quantity, category, luggage, packed)
    VALUES(?, ?, ?, ?, ?)
    '''

    print('Inserting temp packig data...')
    # Execute the statement for each item
    db = conn.cursor()
    for d in tmp_packingList:
        db.execute(insert_stmt, (
                d['item'],
                d['quantity'],
                d['category'],
                d['luggage'],
                d['packed']
            )
        )
        
    conn.commit()


def db_connect(db_name):
    '''
    Connect to the SQLite database. Also, create the database
    file if it doesn't already exist.
    '''
    # Check if database already exists
    db_exists = os.path.isfile(f'{db_name}.db')
    
    # If it doesn't exist, create it
    if not db_exists:
        print("Database doesn't exist. Creating...")
        open(f'{db_name}.db', 'w').close()
        print(f'Created: {db_name}.db')
        
    # Connect to SQLite database
    conn = sqlite3.connect(f'{db_name}.db')
    db = conn.cursor()
    
    # If the db file is new, create the packing
    # list table, empty.
    if not db_exists:
        db.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {PACKLIST} (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
                item TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                category TEXT NOT NULL,
                luggage TEXT NOT NULL,
                packed INTEGER NOT NULL
            );
            '''
        )
        # TMP: Pre-populate table for testing purposes
        insert_tmp_data(conn)
    
    return conn, db

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config['TEMPLATES_AUTO_RELOAD'] = True


# Before every request, connect to database and store
# the connection and database objects (they are
# globally accessible).
@app.before_request
def before_request():
    g.conn, g.db = db_connect(DB_NAME)
    
# After each request to our web application, if we have
# a database connection open, close it.
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()
        

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print('POST');
        data = request.get_json()
        # Checkbox action
        if data['action'] == 'checkbox':
            id_val = data.get('idValue')
            # Get checkbox state from webapp
            checked_val = data.get('isChecked')
            # Update database with new checkbox state
            g.db.execute(
                f'''
                UPDATE {PACKLIST}
                SET packed = ?
                WHERE id = ?;
                ''',
                (checked_val,
                id_val)
            )
            # Update checked count
            g.db.execute(f'SELECT * FROM {PACKLIST} WHERE packed=1;')
            checked = len(g.db.fetchall())
            
            # Commit the changes to the database
            g.conn.commit()
        
            return jsonify('Table update source: checkbox')
        # Add button action
        elif data['action'] == 'addButton':
            # Prepare the insert row statement
            insert_stmt = f'''
            INSERT INTO {PACKLIST} (item, quantity, category, luggage, packed)
            VALUES(?, ?, ?, ?, ?)
            '''

            # Execute the statement
            g.db.execute(insert_stmt, (
                    'Item',
                    1,
                    'Essentials',  # TMP
                    'Red suitcase',  # TMP
                    0
                )
            )
            
            # Commit the changes to the database
            g.conn.commit()
        
            print('Added row')
            return jsonify('Table update source: add button')

    # Handle GET request
    # ==================
    # Get all rows from the table
    print('GET')
    g.db.execute(f'SELECT * FROM {PACKLIST};')
    # Fetch all rows returned by the last query result
    row_list = g.db.fetchall()

    # Get all checked items
    g.db.execute(f'SELECT * FROM {PACKLIST} WHERE packed=1;')
    # Count checked items
    checked = len(g.db.fetchall())
    
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
        
    return render_template('index.html', column_names=column_names, checked=checked, rows=rows)

@app.route('/get_data', methods=['GET'])
def get_data():
    conn = sqlite3.connect(f'{DB_NAME}.db')
    c = conn.cursor()
    c.execute(f'SELECT * FROM {PACKLIST}')
    
    # Get headers
    headers = [column[0] for column in c.description]
    
    # Fetch all rows
    rows = c.fetchall()
    conn.close()
    
    # Combine headers and rows into a list of dictionaries.
    # Each dictionary is a row, where each key is the header
    # and each value is the cell data.
    data = [dict(zip(headers, row)) for row in rows]

    return jsonify(data)
 