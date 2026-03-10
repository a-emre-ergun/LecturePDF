import sqlite3
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS PDFS(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                creation_date TEXT,
                filepath TEXT,
                schedule TEXT,
                week INTEGER,
                course TEXT
            )
        ''')
        self.conn.commit()

    def insert_pdf(self, filename, filepath, schedule, week, course):
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT
            INTO PDFS(filename, creation_date, filepath, schedule, week, course)
            VALUES(?, ?, ?, ?, ?, ?)
        ''', (filename, creation_date, filepath, schedule, week, course))
        self.conn.commit()

    def get_history(self):
        self.cursor.execute('''
            SELECT filename, creation_date, filepath, schedule, week, course
            FROM PDFS
            ORDER BY creation_date DESC
        ''')
        return self.cursor.fetchall()

    def search_history(self, query):
        name = f"%{query}%"
        self.cursor.execute('''
            SELECT filename, creation_date, filepath, schedule, week, course
            FROM PDFS
            WHERE filename LIKE ?
            ORDER BY creation_date DESC
        ''', (name,))
        return self.cursor.fetchall()

    def delete_record(self, filepath):
        self.cursor.execute("DELETE FROM PDFS WHERE filepath = ?", (filepath,))
        self.conn.commit()

    def close(self):
        self.conn.close()
