#!/usr/bin/env python3
"""
Create Demo User and Admin Accounts
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from neondb_service import get_db_service
    from auth_service import get_auth_service
    
    print("🌊 Creating Ocean Demo Accounts...")
    
    # Initialize services
    db_service = get_db_service()
    auth_service = get_auth_service(db_service)
    
    # Demo User Account
    demo_user = {
        "user_id": "demo_user_001",
        "email": "demo@ocean.com",
        "password": "DemoUser123!",
        "full_name": "Ocean Demo User",
        "organization": "Marine Conservation Society",
        "phone": "+91 98765 43210",
        "role": "user",
        "email_verified": True
    }
    
    # Demo Admin Account  
    demo_admin = {
        "user_id": "demo_admin_001",
        "email": "admin@ocean.com", 
        "password": "AdminOcean123!",
        "full_name": "Ocean Admin",
        "organization": "National Centre for Coastal Research",
        "phone": "+91 87654 32109",
        "role": "admin",
        "email_verified": True
    }
    
    # Check if users already exist
    existing_user = db_service.get_user_by_email(demo_user["email"])
    existing_admin = db_service.get_user_by_email(demo_admin["email"])
    
    users_created = []
    
    # Create demo user if not exists
    if not existing_user:
        print(f"Creating demo user: {demo_user['email']}")
        result = auth_service.register_user(demo_user)
        if result["success"]:
            users_created.append(f"Demo User: {demo_user['email']}")
            print(f"✅ Created demo user: {demo_user['email']}")
        else:
            print(f"❌ Failed to create demo user: {result.get('error', 'Unknown error')}")
    else:
        print(f"ℹ️  Demo user already exists: {demo_user['email']}")
    
    # Create demo admin if not exists  
    if not existing_admin:
        print(f"Creating demo admin: {demo_admin['email']}")
        result = auth_service.register_user(demo_admin)
        if result["success"]:
            users_created.append(f"Demo Admin: {demo_admin['email']}")
            print(f"✅ Created demo admin: {demo_admin['email']}")
        else:
            print(f"❌ Failed to create demo admin: {result.get('error', 'Unknown error')}")
    else:
        print(f"ℹ️  Demo admin already exists: {demo_admin['email']}")
    
    # Display credentials
    print(f"\n🌊 OCEAN DEMO ACCOUNTS:")
    print(f"{'='*50}")
    print(f"👤 Demo User:")
    print(f"   Email: {demo_user['email']}")
    print(f"   Password: {demo_user['password']}")
    print(f"   Role: User")
    print(f"")
    print(f"🔑 Demo Admin:")
    print(f"   Email: {demo_admin['email']}")
    print(f"   Password: {demo_admin['password']}")
    print(f"   Role: Admin")
    print(f"{'='*50}")
    print(f"🌐 Login at: http://localhost:3000/login")
    print(f"{'='*50}\n")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()