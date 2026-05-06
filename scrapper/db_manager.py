import psycopg2
from typing import Dict

class DatabaseManager:
    def __init__(self):
        # Connect to the local Docker Postgres instance
        self.conn = psycopg2.connect(
            dbname="hunterhub_db",
            user="hunter",
            password="hunterpassword",
            host="localhost",
            port="5432"
        )
        # Autocommit ensures our inserts save immediately
        self.conn.autocommit = True 

    def save_job(self, job: Dict) -> bool:
        """
        Saves a single job dictionary to the database.
        Returns True if the job was inserted, False if it was a duplicate.
        """
        with self.conn.cursor() as cursor:
            # We use ON CONFLICT DO NOTHING to prevent saving duplicates
            # Since we made 'url' a UNIQUE column in our init.sql schema
            sql = """
                INSERT INTO jobs (title, company, description, url, date_posted)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
            """
            cursor.execute(sql, (
                job.get('title'),
                job.get('company'),
                job.get('description'),
                job.get('url'),
                job.get('date_posted')
            ))
            
            # Return True if a new row was inserted, False if it was skipped
            return cursor.rowcount > 0

    def close(self):
        self.conn.close()
        print("Database connection closed.")