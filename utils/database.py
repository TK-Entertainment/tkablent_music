import os, dotenv

from mysql.connector import connect, Error
from mysql.connector.connection import MySQLConnection, MySQLCursor
from mysql.connector.connection_cext import CMySQLConnection
from mysql.connector.cursor_cext import CMySQLCursorBuffered

class Database:
    def __init__(self):
        self.connect()
    
    def connect(self):
        self.connection: CMySQLConnection = connect(
            host='localhost',
            user=os.getenv('MYSQLUSER'),
            password=os.getenv('MYSQLPASSWORD'),
            database='tkablent',
        )
        print(type(self.connection))
        self.cursor: CMySQLCursorBuffered = self.connection.cursor(buffered=True)

    def disconnect(self):
        self.connection.disconnect()

    def get_prefix(self, guild_id: int):
        self.cursor.execute(f'SELECT prefix FROM guild WHERE id={guild_id}')
        result = self.cursor.fetchall()
        if len(result) == 0:
            self.cursor.execute(f"INSERT INTO guild(id, prefix) VALUES ({guild_id}, '$')")
            self.connection.commit()
            return '$'
        return result[0][0]
'''
guild:
id, prefix, volume
'''
