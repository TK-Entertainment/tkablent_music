import os, dotenv
from typing import *

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
        self.cursor: CMySQLCursorBuffered = self.connection.cursor(buffered=True)

    def disconnect(self):
        self.connection.disconnect()

    def initdb(self):
        self.cursor.execute(f"SELECT * FROM guild")
        if len(self.cursor.fetchall()) == 0:
            self.cursor.execute(f"CREATE TABLE guild(id int, prefix varchar(255), volume int)")

    def create_columns(self, guild_id)-> Union[Tuple[List], None]: 
        self.cursor.execute(f"SELECT * FROM guild WHERE id={guild_id}")
        if len(self.cursor.fetchall()) == 0:
            self.cursor.execute(f"INSERT INTO guild(id, prefix, volume) VALUES ({guild_id}, '$', 100")
            self.connection.commit()
            # Return default values (list)
            return [('$', 100)]
        else:
            self.cursor.execute(f"SELECT prefix FROM guild WHERE id={guild_id}")
            result1 = self.cursor.fetchall()

            self.cursor.execute(f"SELECT volume FROM guild WHERE id={guild_id}")
            result2 = self.cursor.fetchall()

            if len(result1) == 0:
                self.cursor.execute(f"INSERT INTO guild(id, prefix) VALUES ({guild_id}, '$')")

            elif len(result2) == 0:
                self.cursor.execute(f"INSERT INTO guild(id, volume) VALUES ({guild_id}, 100)")
            
            else: # No case
                return

            self.connection.commit()
            self.cursor.execute(f"SELECT * FROM guild WHERE id={guild_id}")
            return self.cursor.fetchall()


    def get_prefix(self, guild_id: int, mode: str, prefix: str=None) -> Union[str, None]:
        # mode: "get", "set"
        if mode == "get":
            self.cursor.execute(f'SELECT prefix FROM guild WHERE id={guild_id}')
            result = self.cursor.fetchall()
            if len(result) == 0:
                return self.create_columns(guild_id)[0][0]
            return result[0][0]
        elif mode == "set":
            self.cursor.execute(f'UPDATE guild SET prefix={prefix} WHERE id={guild_id}')
            self.connection.commit()

    def volume_data(self, guild_id: int, mode: str, volume: int=None) -> Union[str, None]:
        # mode: "get", "set"
        if mode == "get":
            self.cursor.execute(f"SELECT volume FROM guild WHERE id={guild_id}")
            result = self.cursor.fetchall()
            if len(result) == 0:
                return self.create_columns(guild_id)[0][1]
            return result[0][1]
        elif mode == "set":
            self.cursor.execute(f"UPDATE guild SET volume={volume} WHERE id={guild_id}")
            self.connection.commit()
            
'''
guild:
id, prefix, volume
'''
