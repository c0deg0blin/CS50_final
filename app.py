
import os
# from cs50 import SQL
import sqlite3
from struct import pack
from flask import Flask, flash, jsonify, redirect, render_template, request, session, g
import json

DB_NAME = 'TripPacker'
PACKLIST = 'packingList'
CATLIST = 'categories'
LUGLIST = 'luggage_opts'
DELETE_HEADER = 'DELETE_BUTTONS'

def insert_tmp_data(conn):
    
    # PACKING LIST
    # Load template packing list from json
    with open('static/packingList_template.json', 'r') as f:
        tmp_packingList = json.load(f)

    # Prepare the insert statement
    insert_stmt = f'''
    INSERT INTO {PACKLIST} (item, quantity, category, luggage, packed)
    VALUES(?, ?, ?, ?, ?)
    '''

    print('Inserting temp packing list data...')
    # Execute the statement for each item
    db = conn.cursor()
    for d in tmp_packingList:
        db.execute(insert_stmt, (
                d['item'],
                d['quantity'],
                d['category'],
                d['luggage'],
                d['packed'],
            )
        )
        
    conn.commit()
    
    # CATEGORY LIST
    # Load template category list from json
    with open('static/categoryList_template.json', 'r') as f:
        tmp_catList = json.load(f)

    # Prepare the insert statement
    insert_stmt = f'INSERT INTO {CATLIST} (category) VALUES(?)'

    print('Inserting temp category list data...')
    # Execute the statement for each item
    db = conn.cursor()
    for d in tmp_catList:
        db.execute(insert_stmt, (d['category'],))
        
    conn.commit()

    # LUGGAGE LIST
    # Load template luggage list from json
    with open('static/luggageList_template.json', 'r') as f:
        tmp_lugList = json.load(f)

    # Prepare the insert statement
    insert_stmt = f'INSERT INTO {LUGLIST} (luggage) VALUES(?)'

    print('Inserting temp luggage list data...')
    # Execute the statement for each item
    db = conn.cursor()
    for d in tmp_lugList:
        db.execute(insert_stmt, (d['luggage'],))
        
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
    
    # If the db file is new, create the tables (empty)
    if not db_exists:
        db.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {PACKLIST} (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
                item TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                category TEXT NOT NULL,
                luggage TEXT NOT NULL,
                packed INTEGER NOT NULL
            );
            '''
        )
        db.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {CATLIST} (
                category TEXT NOT NULL UNIQUE
            );
            '''
        )
        db.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {LUGLIST} (
                luggage TEXT NOT NULL UNIQUE
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
        elif data['action'] == 'itemAdded':
            # Get new item name
            item_name = data.get('itemName')
            # Get first category and luggage options
            g.db.execute(f'SELECT * FROM {CATLIST} ORDER BY category LIMIT 1;')
            first_cat = [cat[0] for cat in g.db.fetchall()][0]
            # first_cat = g.db.fetchall()
            g.db.execute(f'SELECT * FROM {LUGLIST} ORDER BY luggage LIMIT 1;')
            first_lug = [lug[0] for lug in g.db.fetchall()][0]
            # first_lug = g.db.fetchall()
            # Prepare the insert row statement
            insert_stmt = f'''
            INSERT INTO {PACKLIST} (item, quantity, category, luggage, packed)
            VALUES(?, ?, ?, ?, ?);
            '''
            
            # Execute the statement
            g.db.execute(insert_stmt, (
                    item_name,
                    1,
                    first_cat,
                    first_lug,
                    0
                )
            )
            
            # Commit the changes to the database
            g.conn.commit()
        
            return jsonify('Table update source: add button')
        # Category changed action
        elif data['action'] == 'category_changed':
            try:
                data = request.get_json()
                id_val = data.get('id')
                cat_val = data.get('category')
                
                # Update selected category in the database
                g.db.execute(
                    f'''
                    UPDATE {PACKLIST}
                    SET category = ?
                    WHERE id = ?;
                    ''',
                    (cat_val,
                    id_val)
                )
                
                # Commit the changes to the database
                g.conn.commit()
                
                return jsonify({'message': 'Data received successfully (category change)'})
            except Exception as e:
                return jsonify({'error': str(e)})
        elif data['action'] == 'luggage_changed':
            try:
                data = request.get_json()
                id_val = data.get('id')
                lug_val = data.get('luggage')
                
                # Update selected category in the database
                g.db.execute(
                    f'''
                    UPDATE {PACKLIST}
                    SET luggage = ?
                    WHERE id = ?;
                    ''',
                    (lug_val,
                    id_val)
                )
                
                # Commit the changes to the database
                g.conn.commit()
                
                return jsonify({'message': 'Data received successfully (luggage change)'})
            except Exception as e:
                return jsonify({'error': str(e)})
        elif data['action'] == 'delete_item':
            try:
                data = request.get_json()
                id_val = data.get('id')

                # Delete item from the database
                g.db.execute(
                    f'''
                    DELETE FROM {PACKLIST}
                    WHERE id = ?;
                    ''',
                    (id_val)
                )
                
                # Commit the changes to the database
                g.conn.commit()
                
                return jsonify({'message': 'Data received successfully (item deletion)'})
            except Exception as e:
                return jsonify({'error': str(e)})
        elif data['action'] == 'item_renamed':
            try:
                data = request.get_json()
                id_val = data.get('id')
                item_name = data.get('item_name')
                
                # Rename item in database
                g.db.execute(
                    f'''
                    UPDATE {PACKLIST}
                    SET item = ?
                    WHERE id = ?;
                    ''',
                    (item_name,
                     id_val)
                )
                
                # Commit the changes to the database
                g.conn.commit()
                
                return jsonify({'message': 'Data received successfully (item rename)'})
            except Exception as e:
                return jsonify({'error': str(e)})
        elif data['action'] == 'quantity_changed':
            try:
                data = request.get_json()
                id_val = data.get('id')
                quantity = data.get('quantity')
                
                # Change quantity in database
                g.db.execute(
                    f'''
                    UPDATE {PACKLIST}
                    SET quantity = ?
                    WHERE id = ?;
                    ''',
                    (quantity,
                     id_val)
                )
                
                # Commit the changes to the database
                g.conn.commit()
                
                return jsonify({'message': 'Data received successfully (item rename)'})
            except Exception as e:
                return jsonify({'error': str(e)})
                

    # Handle GET request
    # ==================
    # Get all rows from the table
    print('INDEX: GET')
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
        
    # Add a column for "delete item" buttons
    column_names.append(DELETE_HEADER)
    
    return render_template('index.html',
                           column_names=column_names,
                           checked=checked,
                           rows=rows)


# Get packing list table data from database to update web app
@app.route('/get_table_data', methods=['GET'])
def get_table_data():
    conn = sqlite3.connect(f'{DB_NAME}.db')
    c = conn.cursor()
    c.execute(f'SELECT * FROM {PACKLIST}')
    
    # Get headers
    headers = [column[0] for column in c.description]
    
    # Add a column for "delete item" buttons
    headers.append(DELETE_HEADER)
    
    # Fetch all rows
    rows = c.fetchall()
    conn.close()
    
    # Get all categories
    g.db.execute(f'SELECT * FROM {CATLIST} ORDER BY category;')
    # Fetch all rows returned by the last query result
    categories = [cat[0] for cat in g.db.fetchall()]
    
    # Get all luggage options
    g.db.execute(f'SELECT * FROM {LUGLIST} ORDER BY luggage;')
    # Fetch all rows returned by the last query result
    luggage_opts = [cat[0] for cat in g.db.fetchall()]
    
    # Combine headers and rows into a list of dictionaries.
    # Each dictionary is a row, where each key is the header
    # and each value is the cell data.
    rows_dict = [dict(zip(headers, row)) for row in rows]
    
    response = {
        'rows': rows_dict,
        'categories': categories,
        'luggage_opts': luggage_opts
    }

    return jsonify(response)

# Get categories table data from database to update web app
@app.route('/get_catTable_data', methods=['GET'])
def get_catTable_data():
    conn = sqlite3.connect(f'{DB_NAME}.db')
    c = conn.cursor()
    c.execute(f'SELECT * FROM {CATLIST}')
    
    # Get headers
    headers = [column[0] for column in c.description]
    
    # Add a column for "delete item" buttons
    headers.append(DELETE_HEADER)
    
    # Fetch all rows
    rows = c.fetchall()
    conn.close()
    
    # Combine headers and rows into a list of dictionaries.
    # Each dictionary is a row, where each key is the header
    # and each value is the cell data.
    rows_dict = [dict(zip(headers, row)) for row in rows]
    
    response = {
        'rows': rows_dict
    }

    return jsonify(response)


@app.route('/categories', methods=["GET"])
def categories():
    # Get all rows from the table
    print('CATEGORIES: GET')
    g.db.execute(f'SELECT * FROM {CATLIST};')
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
        
    # Add a column for "delete item" buttons
    column_names.append(DELETE_HEADER)    
    
    return render_template('categories.html',
                           column_names=column_names)