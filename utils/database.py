import os, dotenv
from typing import *

from mysql.connector import connect, Error
from mysql.connector.connection import MySQLConnection, MySQLCursor
from mysql.connector.connection_cext import CMySQLConnection
from mysql.connector.cursor_cext import CMySQLCursorBuffered

class Database:
    def __init__(self):
        self.connect()
        self.cursor.execute('SHOW TABLES LIKE "guild"')
        if len(self.cursor.fetchall()) == 0:
            self.cursor.execute("CREATE TABLE guild(id int, prefix varchar(255), volume int)")
    
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

    def create_guild_info(self, guild_id)-> Tuple: 
        self.cursor.execute(f"INSERT INTO guild(id, prefix, volume) VALUES ({guild_id}, '$', 100)")
        self.connection.commit()
        return '$', 100

    def get_guild_info(self, guild_id) -> Tuple:
        self.cursor.execute(f"SELECT * FROM guild WHERE id={guild_id}")
        result = self.cursor.fetchall()
        if len(result) == 0:
            return self.create_guild_info(guild_id)
        return result[0][1:] # return info without id

    def get_prefix(self, guild_id: int) -> str:
        return self.get_guild_info(guild_id)[0]
    
    def set_prefix(self, guild_id: int, prefix: str):
        self.cursor.execute(f'UPDATE guild SET prefix="{prefix}" WHERE id={guild_id}')
        self.connection.commit()

    def get_volume(self, guild_id: int) -> int:
        return self.get_guild_info(guild_id)[1]

    def set_volume(self, guild_id: int, volume: int):
        self.cursor.execute(f"UPDATE guild SET volume={volume} WHERE id={guild_id}")
        self.connection.commit()
        