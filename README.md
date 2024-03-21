# TripPacker
#### Video Demo: <https://youtu.be/9Qvas3rIhT8>
#### Description:
TripPacker is a web app with a Python and SQL backend. It's a simple packing list where items can be checked off, added, renamed and deleted, as well as assigned to different categories and luggage.
The landing page of the app is the packing list itself. In the top left it has a counter which keeps track of how many items have been checked off the list, as well as the total number of items in the list.
There are links in the main page that take you to subpages where the categories and luggage options can be edited (added, renamed, deleted). In the case of the luggage, a color can be assigned to it and, when in the main page that luggage is selected for an item, the row that that item is in will get that same color.
The item list table can be sorted by any of the headers. Click a header once and the table will be sorted in ascending order. Click it again and it will be sorted in descending order.
If no database file is present when "flask run" is executed, a new TripPacker.db database file will be procedurally created with pre-populated template tables.

Files included:
- README.md: This file.
- app.py: Contains the main Python code for the server, which makes use of the Flask library. It includes routes and funtions to access and update the SQL database, and to provide the client with the data it needs to draw the different tables and pages. It also contains functions to procedurally generate a database file from data stored in existing JSON templates, if one doesn't already exists when "flask run" is executed.
- TripPacker.db: The database file. Contains tables for the  packing list, categories and luggage options.
- static/categoryList_template.json: Contains data to procedurally generate a template categories table for the TripPacker.db database.
- static/luggageList_template.json: Contains data to procedurally generate a template luggage table for the TripPacker.db database.
- static/packingList_template.json: Contains data to procedurally generate a packing list table for the TripPacker.db database.
- static/styles.css: Styling rules for the web app.
- templates/categories.html: Contains HTML and JavaScript for the categories editor page and table. 
- templates/index.html: Contains HTML and JavaScript for the main page and packing list table. 
- templates/layout.html: Base page which all other pages extend from.
- templates/luggqge.html: Contains HTML and JavaScript for the luggqge page and table.


