"""Storage module for job deduplication using SQLite."""
import sqlite3
import logging
from datetime import datetime
import os


class JobStorage:
    """Manages job history in a SQLite database."""

    def __init__(self, db_path='data/jobs_history.db'):
        """
        Initialize the storage.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS jobs (
                        url TEXT PRIMARY KEY,
                        title TEXT,
                        company TEXT,
                        location TEXT,
                        source TEXT,
                        first_seen_date TEXT
                    )
                ''')
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")

    def is_job_new(self, url):
        """
        Check if a job URL is new.

        Args:
            url: The job URL to check.

        Returns:
            True if the job is new (not in DB), False otherwise.
        """
        if not url:
            return False  # Treat empty URLs as not new (or skip them)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM jobs WHERE url = ?', (url,))
                return cursor.fetchone() is None
        except Exception as e:
            self.logger.error(f"Error checking if job is new: {e}")
            return True # Default to True to avoid missing jobs on DB error

    def add_job(self, job):
        """
        Add a job to the database.

        Args:
            job: Job dictionary.
        """
        if not job.get('url'):
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO jobs (url, title, company, location, source, first_seen_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    job['url'],
                    job.get('title'),
                    job.get('company'),
                    job.get('location'),
                    job.get('source'),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error adding job to history: {e}")
