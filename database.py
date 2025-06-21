
import sqlite3
import pandas as pd

class DatabaseManager:
    def __init__(self, db_name="youtube_analytics.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                channel_title TEXT,
                published_at TEXT
            )
        """)
        self.conn.commit()

    def insert_videos(self, df):
        for _, row in df.iterrows():
            self.cursor.execute("""
                INSERT OR IGNORE INTO videos (video_id, title, description, channel_title, published_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                row["Video ID"], row["Title"], row["Description"],
                row["Channel Title"], row["Published At"]
            ))
        self.conn.commit()

    def fetch_all_videos(self):
        df = pd.read_sql_query("SELECT * FROM videos", self.conn)
        return df
