import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Point to project root
sys.path.append(os.path.abspath("."))

def get_db_path():
    # Logic copied from services/backend_api/app/db.py to avoid import issues
    # shared is at services/shared
    current_dir = Path(os.getcwd())
    data_dir = current_dir / "ai_data_final"
    # Or use services/shared/config if we could import it
    # But db.py uses: DATA_DIR / "ai_learning_table.db"
    # Let's try to locate the one db.py uses:
    # services/shared/config imports from env or defaults to project_root/ai_data_final
    return data_dir / "ai_learning_table.db"

def seed_users(limit=50):
    db_path = get_db_path()
    print(f"Seeding database at: {db_path}")
    
    if not db_path.parent.exists():
        print(f"Directory {db_path.parent} does not exist. Creating...")
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Ensure table exists (in case app hasn't run)
    # We rely on existing schema mostly, but let's be safe if it's empty
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            display_name TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    
    profiles_dir = Path("ai_data_final/profiles")
    if not profiles_dir.exists():
        print("No profiles directory found.")
        return

    count = 0
    for file_path in profiles_dir.glob("candidate_*.json"):
        if count >= limit: break
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Extract
            email = data.get("email") or data.get("Email")
            name = data.get("name") or data.get("Name") or "Unknown User"
            
            if not email:
                candidate_id = file_path.stem.split('_')[1]
                email = f"user_{candidate_id}@example.com"

            # Check existence
            cur.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cur.fetchone():
                continue

            print(f"Inserting user: {email}")
            cur.execute(
                "INSERT INTO users (email, display_name, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                (email, name, "hashed_secret", "candidate", str(datetime.now()))
            )
            count += 1

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    conn.commit()
    conn.close()
    print(f"Successfully seeded {count} users.")

if __name__ == "__main__":
    seed_users()
