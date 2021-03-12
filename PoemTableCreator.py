# Imports the SQL module in order to create our database. This script only needs to be run once to initialise the database.
import sqlite3

# As there is no database called poems.db, the program just creates one.
database = sqlite3.connect("poems.db")

# This is just a place holder in our database needed to execute commands on it.
cursor = database.cursor()

# Query to create the table in our SQL database.
table_structure =  """CREATE TABLE Poems(
  PoemID INTEGER PRIMARY KEY AUTOINCREMENT,
  PoemName VARCHAR (50),
  Poem TEXT ,
  Author VARCHAR(20),
  TimeAdded TEXT
)"""
# Yes, I know I could make the table more complicated by creating a whole new entity called author and giving them a unique ID
# But I only want to store their name. If I wanted to store their age for example, I'd create a new entity and link it. 

# The query is executed.
cursor.execute(table_structure)
database.commit()

