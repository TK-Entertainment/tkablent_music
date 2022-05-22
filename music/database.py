import os, dotenv

from mysql.connector import connect, Error
from mysql.connector.connection import MySQLConnection, MySQLCursor

class Database:
    def __init__(self):
        self.connect()
    
    def connect(self):
        self.connection: MySQLConnection = connect(
            host="localhost",
            user=os.getenv('MYSQLUSER'),
            password=os.getenv('MYSQLPASSWORD'),
        )

    def disconnect(self):
        self.connection.disconnect()

    def get_prefix(self, guild_id: int):
        with self.connection.cursor() as cursor:
            cursor: MySQLCursor
            cursor.execute()