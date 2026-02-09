#!/usr/bin/env python3
"""
Assign Random Subscription Tiers to Test Users
==============================================
Assigns different tiers to the 100 test users for testing tier-based features:
- Free: 30 users
- Monthly Pro ($15.99): 30 users  
- Annual Pro ($149.99): 30 users
- Enterprise Pro ($299.99): 10 users

Works with SQLite database: user_credentials.db
"""

import sqlite3
import random
from pathlib import Path

def assign_random_tiers():
    """Assign random subscription tiers to all users in SQLite database"""
    
    # Database path
    db_path = Path(__file__).parent / "user_credentials.db"
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add subscription_tier column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT 'free'")
        print("✅ Added subscription_tier column to database")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Get all users
    cursor.execute("SELECT email FROM users WHERE email LIKE '%janatmainswood%@gmail.com'")
    users = cursor.fetchall()
    
    if not users:
        print("❌ No users found matching pattern janatmainswood*@gmail.com")
        conn.close()
        return
    
    print(f"📊 Found {len(users)} test users")
    
    # Define tier distribution
    tiers = {
        'free': 30,
        'monthly_pro': 30,
        'annual_pro': 30,
        'enterprise_pro': 10
    }
    
    # Create tier pool with distribution
    tier_pool = []
    for tier, count in tiers.items():
        tier_pool.extend([tier] * count)
    
    # Shuffle for random assignment
    random.shuffle(tier_pool)
    
    print(f"🎯 Assigning tiers with distribution:")
    for tier, count in tiers.items():
        print(f"   - {tier}: {count} users")
    
    # Assign tiers
    tier_counts = {'free': 0, 'monthly_pro': 0, 'annual_pro': 0, 'enterprise_pro': 0}
    
    for idx, (email,) in enumerate(users):
        if idx < len(tier_pool):
            assigned_tier = tier_pool[idx]
            
            # Update database
            cursor.execute("""
                UPDATE users 
                SET subscription_tier = ? 
                WHERE email = ?
            """, (assigned_tier, email))
            
            tier_counts[assigned_tier] += 1
    
    # Commit changes
    conn.commit()
    
    print(f"\n✅ Tier assignment complete!")
    print(f"\n📊 Final distribution:")
    for tier, count in tier_counts.items():
        print(f"   - {tier}: {count} users")
    
    # Print sample users for each tier
    print(f"\n👥 Sample users by tier:")
    samples_shown = {tier: 0 for tier in tiers.keys()}
    
    cursor.execute("""
        SELECT email, subscription_tier 
        FROM users 
        WHERE email LIKE '%janatmainswood%@gmail.com'
        ORDER BY email
    """)
    
    for email, tier in cursor.fetchall():
        if tier in samples_shown and samples_shown[tier] < 3:  # Show 3 samples per tier
            print(f"   {tier:15} | {email}")
            samples_shown[tier] += 1
    
    conn.close()
    
    print(f"\n🔑 Login Instructions:")
    print(f"   - Email: Any user from Janatmainswood1@gmail.com to Janatmainswood100@gmail.com")
    print(f"   - Password: janj@!3143@? (SAME FOR ALL)")
    print(f"   - Different tiers assigned randomly for testing upgrade paths")
    print(f"\n📍 Database location: {db_path}")


if __name__ == "__main__":
    assign_random_tiers()
