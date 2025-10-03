#!/usr/bin/env python3
"""
Fix users table and create initial users
"""

import sys
import os
import hashlib
import secrets
from datetime import datetime

# Add the backend directory to Python path
sys.path.append('/Users/razashaikh/Desktop/sih/backend')

from neondb_service import NeonDBService

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def fix_and_create_users():
    """Fix table structure and create users"""
    
    # Initialize database service
    db_service = NeonDBService()
    
    try:
        # First, let's see what columns exist and fix the username issue
        print("🔧 Fixing users table structure...")
        
        # Drop the NOT NULL constraint on username or set a default value
        fix_queries = [
            "ALTER TABLE users ALTER COLUMN username DROP NOT NULL;",
            "UPDATE users SET username = email WHERE username IS NULL;"
        ]
        
        for query in fix_queries:
            try:
                result = db_service.execute_query(query)
                print(f"✅ Executed: {query}")
            except Exception as e:
                print(f"⚠️  Query might have failed (could be expected): {e}")
        
        # Now create users with all required fields
        admin_data = {
            'user_id': f"USER_{secrets.token_hex(8).upper()}",
            'username': 'admin_nccr',  # Add username field
            'email': 'admin@nccr.gov.in',
            'password_hash': hash_password('admin123'),
            'full_name': 'NCCR Administrator',
            'organization': 'National Centre for Coastal Research',
            'phone': '+91-9876543210',
            'role': 'admin',
            'email_verified': True,
            'wallet_address': '',
            'last_login': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        user_data = {
            'user_id': f"USER_{secrets.token_hex(8).upper()}",
            'username': 'community_user',  # Add username field
            'email': 'user@community.org',
            'password_hash': hash_password('user123'),
            'full_name': 'Community User',
            'organization': 'Local Community Organization',
            'phone': '+91-9876543211',
            'role': 'user',
            'email_verified': True,
            'wallet_address': '',
            'last_login': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Try direct SQL insert to handle all columns properly
        admin_insert = """
        INSERT INTO users (user_id, username, email, password_hash, full_name, organization, 
                          phone, role, email_verified, wallet_address, last_login, created_at, updated_at)
        VALUES (%(user_id)s, %(username)s, %(email)s, %(password_hash)s, %(full_name)s, 
                %(organization)s, %(phone)s, %(role)s, %(email_verified)s, %(wallet_address)s, 
                %(last_login)s, %(created_at)s, %(updated_at)s)
        ON CONFLICT (email) DO NOTHING;
        """
        
        # Create admin user
        try:
            result = db_service.execute_query(admin_insert, admin_data)
            print("✅ Created admin user: admin@nccr.gov.in")
        except Exception as e:
            print(f"❌ Failed to create admin user: {e}")
        
        # Create regular user
        try:
            result = db_service.execute_query(admin_insert, user_data)
            print("✅ Created regular user: user@community.org")
        except Exception as e:
            print(f"❌ Failed to create regular user: {e}")
        
        # Verify users
        print("\n📋 Verification:")
        admin_check = db_service.get_user_by_email('admin@nccr.gov.in')
        user_check = db_service.get_user_by_email('user@community.org')
        
        if admin_check:
            print(f"✅ Admin user: {admin_check.get('full_name', 'N/A')} ({admin_check.get('role', 'N/A')})")
        else:
            print("❌ Admin user not found")
            
        if user_check:
            print(f"✅ Regular user: {user_check.get('full_name', 'N/A')} ({user_check.get('role', 'N/A')})")
        else:
            print("❌ Regular user not found")
            
        print("\n🎉 Setup completed!")
        print("🔐 Login credentials:")
        print("Admin: admin@nccr.gov.in / admin123")
        print("User:  user@community.org / user123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_and_create_users()