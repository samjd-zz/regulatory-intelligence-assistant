#!/usr/bin/env python3
"""
Database status checker for entrypoint script.
Returns the count of regulations in the database.
"""
import os
import sys
from sqlalchemy import create_engine, text

def get_regulation_count():
    """Get the count of regulations from the database."""
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/regulatory_db')

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text('SELECT COUNT(*) FROM regulations'))
            count = result.scalar()
            return int(count or 0)
    except Exception as e:
        print(f"Error checking database: {e}", file=sys.stderr)
        return 0

if __name__ == '__main__':
    count = get_regulation_count()
    print(count)