import psycopg2
from typing import List, Dict

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

    # change this method so that it takes one job at a time and saves it to the database, instead of taking a list of jobs
    def save_jobs(self, jobs: List[Dict]):
        """Saves a list of job dictionaries to the database."""
        inserted_count = 0
        
        with self.conn.cursor() as cursor:
            for job in jobs:
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
                
                # If a row was actually inserted (not skipped due to conflict)
                if cursor.rowcount > 0:
                    inserted_count += 1
                    
        print(f"Successfully inserted {inserted_count} new jobs into PostgreSQL.")

    def close(self):
        self.conn.close()
        print("Database connection closed.")