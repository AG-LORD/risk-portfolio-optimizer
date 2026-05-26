"""
Run this once from the Backend folder:
    python migrate_kyc.py

Adds kyc_status column to existing users table without deleting data.
"""
from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        with db.engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS kyc_status VARCHAR(20) NOT NULL DEFAULT 'pending';"
            ))
            conn.commit()
        print("✓ Migration successful — kyc_status column added to users table.")
    except Exception as e:
        print(f"Note: {e}")
        print("If the column already exists, this is fine — no action needed.")
