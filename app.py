
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
COLOR_HEADER = 'COLOR'

def insert_tmp_data(conn):
    
    # PACKING LIST
    # Load template packing list from json
    with open('static/packingList_template.json', 'r') as f:
        tmp_packingList = json.load(f)

    # Prepare the insert statement
    insert_stmt = f'''
    INSERT INTO {PACKLIST} (item, sort_index, quantity, category, luggage, packed)
    VALUES(?, ?, ?, ?, ?, ?)
    '''

    print('Inserting temp packing list data...')
    # Execute the statement for each item
    db = conn.cursor()
    sort_index = 1
    for d in tmp_packingList:
        print(d['quantity']+1)
        db.execute(insert_stmt, (
                d['item'],
                sort_index,
                d['quantity'],
                d['category'],
                d['luggage'],
                d['packed'],
            )
        )
        sort_index += 1
        
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
    insert_stmt = f'INSERT INTO {LUGLIST} (luggage, color) VALUES(?, ?)'

    print('Inserting temp luggage list data...')
    # Execute the statement for each item
    db = conn.cursor()
    for d in tmp_lugList:
        db.execute(insert_stmt, (
            d['luggage'],
            d['color'],
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
    
    # If the db file is new, create the tables (empty)
    if not db_exists:
        db.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {PACKLIST} (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
                sort_index INTEGER NOT NULL,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
                category TEXT NOT NULL UNIQUE
            );
            '''
        )
        db.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {LUGLIST} (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
                luggage TEXT NOT NULL UNIQUE,
                color TEXT NOT NULL
            );
            '''
        )
        db.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {LUGLIST} (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
                luggage TEXT NOT NULL UNIQUE,
                color TEXT NOT NULL
            );
            '''
        )
        
        # Pre-populate table for testing purposes
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
        data = request.get_json()
        # Checkbox action
        if data['action'] == 'checkbox':
            print('POST action: checkbox')
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
        elif data['action'] == 'add_item':
            print('POST action: add_item')
            # Get new item name
            item_name = data.get('itemName')
            # Get first category and luggage options
            g.db.execute(f'SELECT * FROM {CATLIST} ORDER BY category LIMIT 1;')
            first_cat = [cat[0] for cat in g.db.fetchall()][0]
            g.db.execute(f'SELECT * FROM {LUGLIST} ORDER BY luggage LIMIT 1;')
            first_lug = [lug[0] for lug in g.db.fetchall()][0]
            # Get number of items in the list
            g.db.execute(f'SELECT * FROM {PACKLIST};')
            last_idx = len(g.db.fetchall())
            print(f'Insert after index: {last_idx}')
            # Prepare the insert row statement
            insert_stmt = f'''
            INSERT INTO {PACKLIST} (item, sort_index, quantity, category, luggage, packed)
            VALUES(?, ?, ?, ?, ?, ?);
            '''
            # Execute the statement
            g.db.execute(insert_stmt, (
                    item_name,
                    (last_idx + 1),
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
            print('POST action: category_changed')
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
            print('POST action: luggage_changed')
            try:
                data = request.get_json()
                id_val = data.get('id')
                lug_val = data.get('luggage')
                
                print(f'ID value: {id_val}')
                print(f'Luggage value: {lug_val}')
                g.db.execute(
                    f'''
                    SELECT color FROM {LUGLIST}
                    WHERE id = {lug_val}
                    LIMIT 1;
                    '''
                )
                test = g.db.fetchall()
                print('TEST:')
                print(test)
                # Get color for the selected luggage
                g.db.execute(
                    f'''
                    SELECT color FROM {LUGLIST}
                    WHERE id = {lug_val}
                    LIMIT 1;
                    '''
                )
                lug_color = g.db.fetchall()[0][0]
                print('COLOR:')
                print(lug_color)

                # Commit the changes to the database
                g.conn.commit()
                
                # Update selected luggage in the database
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
                
                return jsonify({
                    'message': 'Data received successfully (luggage change)',
                    'lug_color': lug_color 
                })
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
                
                # Get list of IDS in current order, post deletion
                g.db.execute(
                    f'''
                    SELECT id
                    FROM {PACKLIST}
                    ORDER BY sort_index
                    '''
                )
                ids = [id[0] for id in g.db.fetchall()]
                
                # Update sort indexes numbering to fill gap from deleted item
                i = 1
                for id in ids:
                    g.db.execute(
                        f'''
                        UPDATE {PACKLIST}
                        SET sort_index = {i}
                        WHERE id = {id}
                        '''
                    )
                    i += 1
                
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
        elif data['action'] == 'sort_table':
            try:
                data = request.get_json()
                action = data.get('action')
                sort_header = data.get('sort_header')
                
                # Get list of IDS in current order
                g.db.execute(
                    f'''
                    SELECT id
                    FROM {PACKLIST}
                    ORDER BY sort_index
                    '''
                )
                unsorted_ids = [id[0] for id in g.db.fetchall()]
                print('UNSORTED IDS:')
                print(unsorted_ids)
                               
                # Get list of IDs sorted by the given header
                g.db.execute(
                    f'''
                    SELECT id
                    FROM {PACKLIST}
                    ORDER BY {sort_header}
                    '''
                )
                sorted_ids = [id[0] for id in g.db.fetchall()]
                print('SORTED IDS:')
                print(sorted_ids)
                
                # If rows are already ordered for the given header, reverse the order
                if sorted_ids == unsorted_ids:
                    g.db.execute(
                        f'''
                        SELECT id
                        FROM {PACKLIST}
                        ORDER BY {sort_header} DESC
                        '''
                    )
                    sorted_ids = [id[0] for id in g.db.fetchall()]
 
                
                # Update packing list with new numbering for sort indexes
                i = 1
                for id in sorted_ids:
                    g.db.execute(
                        f'''
                        UPDATE {PACKLIST}
                        SET sort_index = {i}
                        WHERE id = {id}
                        '''
                    )
                    i += 1
                
                # Commit the changes to the database
                g.conn.commit()
                
                return jsonify({'message': 'Data received successfully (table sort)'})
            except Exception as e:
                return jsonify({'error': str(e)})
                
    # Handle GET request
    # vvvvvvvvvvvvvvvvvv
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
@app.route('/get_listTable_data', methods=['GET'])
def get_listTable_data():

    conn = sqlite3.connect(f'{DB_NAME}.db')
    c = conn.cursor()

    # Get sorting parameter
    # sort_header = request.args.get('sort_header')
    # c.execute(f'SELECT * FROM {PACKLIST} ORDER BY {sort_header}')
    c.execute(f'SELECT * FROM {PACKLIST} ORDER BY sort_index')
    
    # Get headers
    headers = [column[0] for column in c.description]
    
    # Add a column for "delete item" buttons
    headers.append(DELETE_HEADER)
    
    # Fetch all rows
    rows = c.fetchall()
    conn.close()
    
    # Get categories table
    g.db.execute(f'SELECT * FROM {CATLIST} ORDER BY category;')
    # Store categories list of tuples into dictionary
    cat_dict = dict(g.db.fetchall())

    # Get luggage data
    g.db.execute(f'SELECT * FROM {LUGLIST} ORDER BY luggage;')
    lug_data = g.db.fetchall()
    # # Store luggage data into dictionary
    lug_dict = {}
    for tup in lug_data:
        id, luggage, color = tup
        lug_dict[id] = {'luggage': luggage, 'color': color}
        
    # Combine headers and rows into a list of dictionaries.
    # Each dictionary is a row, where each key is the header
    # and each value is the cell data.
    rows_dict = [dict(zip(headers, row)) for row in rows]
    
    response = {
        'rows': rows_dict,
        'cat_dict': cat_dict,
        'lug_dict': lug_dict
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


@app.route('/categories', methods=['GET', 'POST'])
def categories():
    if request.method == 'POST':
        print('POST: CATEGORIES')
        data = request.get_json()
        # Add button action
        if data['action'] == 'categoryAdded':
            # Get new item name
            category_name = data.get('categoryName')
            # Prepare the insert row statement
            insert_stmt = f'INSERT INTO {CATLIST} (category) VALUES(?);'
            
            print(insert_stmt)
            
            # Execute the statement
            g.db.execute(insert_stmt, (category_name,))
            
            # Commit the changes to the database
            g.conn.commit()
        
            return jsonify('Table update source: add category button')
        # Delete category action
        elif data['action'] == 'delete_category':
            try:
                data = request.get_json()
                id_val = data.get('id')

                # Delete category from the database
                g.db.execute(
                    f'''
                    DELETE FROM {CATLIST}
                    WHERE id = ?;
                    ''',
                    (id_val)
                )
                
                # Commit the changes to the database
                g.conn.commit()
                
                return jsonify({'message': 'Data received successfully (item deletion)'})
            except Exception as e:
                return jsonify({'error': str(e)})
        # Rename category action
        elif data['action'] == 'category_renamed':
            try:
                data = request.get_json()
                id_val = data.get('id')
                category_name = data.get('category_name')
                
                # Rename item in database
                g.db.execute(
                    f'''
                    UPDATE {CATLIST}
                    SET category = ?
                    WHERE id = ?;
                    ''',
                    (category_name,
                     id_val)
                )
                
                # Commit the changes to the database
                g.conn.commit()
                
                return jsonify({'message': 'Data received successfully (category rename)'})
            except Exception as e:
                return jsonify({'error': str(e)})
    # Handle GET request
    # vvvvvvvvvvvvvvvvvv
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
        
    # Add a column for "delete category" buttons
    column_names.append(DELETE_HEADER)    
    
    return render_template('categories.html',
                           column_names=column_names)

    
# Get luggage table data from database to update web app
@app.route('/get_lugTable_data', methods=['GET'])
def get_lugTable_data():
    conn = sqlite3.connect(f'{DB_NAME}.db')
    c = conn.cursor()
    c.execute(f'SELECT * FROM {LUGLIST}')
    
    # Get headers
    headers = [column[0] for column in c.description]

    # Add a column for colours
    headers.append(COLOR_HEADER)
    
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


@app.route('/luggage', methods=["GET", "POST"])
def luggage():
    if request.method == 'POST':
        print('POST: LUGGAGE')
        data = request.get_json()
        # Add button action
        if data['action'] == 'luggageAdded':
            # Get new item name
            luggage_name = data.get('luggageName')
            # Default color = white
            color = "#ffffff"
            # Prepare the insert row statement
            insert_stmt = f'INSERT INTO {LUGLIST} (luggage, color) VALUES(?, ?);'

            # Execute the statement
            g.db.execute(insert_stmt, (luggage_name, color))
            
            # Commit the changes to the database
            g.conn.commit()
        
            return jsonify('Table update source: add luggage button')
        # Delete luggage action
        elif data['action'] == 'delete_luggage':
            try:
                data = request.get_json()
                id_val = data.get('id')

                # Delete luggage from the database
                g.db.execute(
                    f'''
                    DELETE FROM {LUGLIST}
                    WHERE id = ?;
                    ''',
                    (id_val)
                )
                
                # Commit the changes to the database
                g.conn.commit()
                
                return jsonify({'message': 'Data received successfully (luggage deletion)'})
            except Exception as e:
                return jsonify({'error': str(e)})
        # Rename luggage action
        elif data['action'] == 'luggage_renamed':
            try:
                data = request.get_json()
                id_val = data.get('id')
                luggage_name = data.get('luggage_name')
                
                # Rename item in database
                g.db.execute(
                    f'''
                    UPDATE {LUGLIST}
                    SET luggage = ?
                    WHERE id = ?;
                    ''',
                    (luggage_name,
                     id_val)
                )
                
                # Commit the changes to the database
                g.conn.commit()
                
                return jsonify({'message': 'Data received successfully (luggage rename)'})
            except Exception as e:
                return jsonify({'error': str(e)})
        # Change color action
        elif data['action'] == 'color_changed':
            try:
                data = request.get_json()
                id_val = data.get('id')
                color = data.get('color')
                
                # Rename item in database
                g.db.execute(
                    f'''
                    UPDATE {LUGLIST}
                    SET color = ?
                    WHERE id = ?;
                    ''',
                    (color,
                     id_val)
                )
                
                # Commit the changes to the database
                g.conn.commit()
                
                return jsonify({'message': 'Data received successfully (color change)'})
            except Exception as e:
                return jsonify({'error': str(e)})
    # Handle GET request
    # vvvvvvvvvvvvvvvvvv
    # Get all rows from the table
    print('LUGGAGE: GET')
    g.db.execute(f'SELECT * FROM {LUGLIST};')
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
        
    # # Add a column for colours
    # column_names.append(COLOR_HEADER)

    # Add a column for "delete luggage" buttons
    column_names.append(DELETE_HEADER)
    
    return render_template('luggage.html',
                           column_names=column_names)