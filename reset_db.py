import os
import sqlite3
from app import app, db

def reset_database():
    # Get the database path from the app config
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        print("Database has been reset successfully!")

if __name__ == "__main__":
    reset_database()