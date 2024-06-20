from pymongo import MongoClient
from dotenv import load_dotenv
import os

# ######################################
# Functions for calling MONGODB database
# ######################################

def insert_to_database(database_name, database_url, user_info):
  """
  Connects to the specified MongoDB database and inserts a predefined item into the 'user-data' collection.

  Parameters:
  database_name (str): The name of the database to connect to.
  database_url (str): the database to connect to. Name of env variable that hold the endpoint
  user_info: user_info object from current session. (session["user_info"])
  Returns:
  InsertOneResult: The result of the insert operation.

  Note:
    Change database url to correct database in working, staging, or production.
    TODO Avoid hardcoding and instead, try call railway environment variables to determine
    if currently in working, staging, or production if possible.
  """
  load_dotenv()
  client = MongoClient(os.getenv(database_url)) # Connect to endpoint
  dbname = client[database_name] # Select the database. Create if not exist
  collection_name = dbname["user-data"] # Select the collection
  collection_name.insert_one(user_info) 
