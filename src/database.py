import sqlite3
import time
import random
from pathlib import Path
from datetime import datetime
from passlib.hash import argon2
import random

# /app/src/database.py -> /app/data
DATA_DIR = Path(__file__).parent.parent / "data"

class DB:
    def get_connection(self):
        # otherwise we get issue with multithreading
        conn = sqlite3.connect(DATA_DIR / "db.sqlite3")
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        # create tables here
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS candy (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, password_count INTEGER, otp TEXT, email TEXT, balance REAL, iban TEXT, cardnum INTEGER, hash_field TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS hash (username TEXT UNIQUE, letternums TEXT, hash TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS session (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, session_id TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS transfer (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, date TEXT, title TEXT, category TEXT, amount BLOB, recipient TEXT, recnumber INTEGER)")
        conn.commit()

    def add_session(self, username, session_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO session (username, session_id) VALUES (?, ?)", (username, session_id))
        conn.commit()

    def delete_session(self, session_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM session WHERE session_id = ?", (session_id,))
        conn.commit()
 
    def check_user(self, username, password):
        time.sleep(random.randint(1, 5))

        conn = self.get_connection()
        cursor = conn.cursor()

        count = cursor.execute('SELECT password_count FROM user WHERE username = ?', (username, )).fetchone()
        if count is None:
            return False
        
        count = dict(count)['password_count']
        if count > 3:
            return False

        query = "SELECT * FROM user where username = ?"
        result = cursor.execute(query, (username, )).fetchone()

        result = dict(result)['password']
        isValid = argon2.verify(password, result)

        if isValid:
            cursor.execute('UPDATE user SET password_count = 0 WHERE username = ?', (username, ))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        else:
            cursor.execute('UPDATE user SET password_count = password_count + 1 WHERE username = ?', (username, ))
            conn.commit()
            cursor.close()
            conn.close()

        return False
    
    def check_username(self, username):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        count = cursor.execute('SELECT password_count FROM user WHERE username = ?', (username, )).fetchone()
        if count is None:
            return False
        
        count = dict(count)['password_count']
        if count > 3:
            return False
        
        return True

    def get_username(self, session_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM session WHERE session_id=?", (session_id,))
        result = cursor.fetchone()
        return result[0]
    
    def get_balance(self, username):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM user WHERE username=?", (username,))
        result = cursor.fetchone()
        return result[0]
    
    def get_transfers(self, username):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transfer WHERE username=?", (username,))
        result = cursor.fetchall()
        rows = [item[2:8] for item in result]
        return rows
    
    def do_transfer(self, username, title, amount, recipient, iban): 
        conn = self.get_connection()
        cursor = conn.cursor()

        date = datetime.now()
        date = date.strftime('%Y-%m-%d')
        category = "Outcome"
        cursor.execute("INSERT INTO transfer (username, date, title, category, amount, recipient, recnumber) VALUES (?, ?, ?, ?, ?, ?, ?)",
               (username, date, title, category, amount, recipient, iban)) 
        cursor.execute("SELECT balance FROM user WHERE username=?", (username,))
        balance = cursor.fetchone()
        balance = balance[0] - amount
        cursor.execute("UPDATE user SET balance=? WHERE username=?", (balance, username))

        conn.commit()

        cursor.execute("SELECT id FROM user WHERE username=?", (recipient,))
        result = cursor.fetchone()
        if result is None:
            print(f"Recipient outside this bank.")
            conn.close()
            return
        iban2 = cursor.execute("SELECT iban FROM user WHERE username=?", (username,)).fetchone()[0]
        category = "Income"
        cursor.execute("INSERT INTO transfer (username, date, title, category, amount, recipient, recnumber) VALUES (?, ?, ?, ?, ?, ?, ?)",
               (recipient, date, title, category, amount, username, iban2))
        cursor.execute("SELECT balance FROM user WHERE username=?", (recipient,))
        balance = cursor.fetchone()
        balance = balance[0] + amount
        cursor.execute("UPDATE user SET balance=? WHERE username=?", (balance, recipient))      

        conn.commit()
        conn.close()

    def get_data(self, username):
        conn = self.get_connection()
        cursor = conn.cursor()
        return cursor.execute("SELECT iban, cardnum FROM user WHERE username=?", (username,)).fetchone()
    
    def verify_password(self, username, old_pass):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM user WHERE username=?", (username,))
        result = cursor.fetchone()[0]
        isValid = argon2.verify(old_pass, result)
        conn.close()
        return isValid

    def update_password(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        password = argon2.hash(password)
        cursor.execute("UPDATE user SET password=? WHERE username=?", (password, username))
        conn.commit()
        conn.close()


