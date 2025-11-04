#!/usr/bin/env python3
"""
Database Initialization Script

This script creates all database tables based on SQLAlchemy models.
Run this script after starting the PostgreSQL database to initialize the schema.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.database import Base, engine  # noqa: E402
from database.database import init_db as db_init_db  # noqa: E402

# Import models to ensure they're registered with Base
from database.models import Application  # noqa: E402, F401


def init_db_verbose():
    """Initialize the database by creating all tables with verbose output."""
    print("Creating database tables...")
    try:
        db_init_db()  # Use the function from database.database
        print("✓ Database tables created successfully!")
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
    except Exception as e:
        print(f"✗ Error creating database tables: {e}")
        sys.exit(1)


def drop_db():
    """Drop all database tables. WARNING: This will delete all data!"""
    print("WARNING: This will drop all database tables and delete all data!")
    confirmation = input("Are you sure you want to continue? (yes/no): ")
    if confirmation.lower() != "yes":
        print("Operation cancelled.")
        return

    print("Dropping database tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        print("✓ Database tables dropped successfully!")
    except Exception as e:
        print(f"✗ Error dropping database tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        drop_db()
    else:
        init_db_verbose()
