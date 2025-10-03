#!/usr/bin/env python3
"""
NeonDB PostgreSQL Database Service for Python Backend
Handles all database operations for the Blue Carbon MRV system
"""

import os
import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Optional, Any

class NeonDBService:
    def __init__(self):
        # Get database URL from environment or use the provided NeonDB connection
        self.database_url = os.getenv(
            'DATABASE_URL', 
            'postgresql://neondb_owner:npg_IwfHYBX1zSn6@ep-dark-pine-a1g29cp7-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
        )
        self.connection = None
        self.connect()

    def connect(self):
        """Establish connection to NeonDB PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                self.database_url,
                cursor_factory=RealDictCursor,
                sslmode='require',
                connect_timeout=10,  # 10 second timeout
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=5,
                keepalives_count=5
            )
            self.connection.autocommit = True
            print("✅ Connected to NeonDB PostgreSQL successfully")
            self.ensure_tables()
        except Exception as e:
            print(f"❌ Failed to connect to NeonDB: {e}")
            self.connection = None

    def ensure_tables(self):
        """Ensure all required tables exist"""
        if not self.connection:
            return
            
        try:
            cursor = self.connection.cursor()
            
            # Create tables if they don't exist (same as Node.js migration)
            create_tables_query = '''
                -- Projects table
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    project_id VARCHAR(255) UNIQUE NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    location JSONB,
                    ecosystem_type VARCHAR(100),
                    area_hectares DECIMAL(10,2),
                    carbon_estimate DECIMAL(15,2),
                    status VARCHAR(50) DEFAULT 'submitted',
                    carbon_credits DECIMAL(15,2) DEFAULT 0,
                    admin_review JSONB,
                    blockchain_tx_hash VARCHAR(255),
                    ipfs_hash VARCHAR(255),
                    workflow_id VARCHAR(255),
                    field_measurements JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Add missing columns if they don't exist
                ALTER TABLE projects ADD COLUMN IF NOT EXISTS carbon_credits DECIMAL(15,2) DEFAULT 0;
                ALTER TABLE projects ADD COLUMN IF NOT EXISTS admin_review JSONB;
                ALTER TABLE projects ADD COLUMN IF NOT EXISTS field_measurements JSONB;
                ALTER TABLE projects ADD COLUMN IF NOT EXISTS reviewer_comments TEXT;
                ALTER TABLE projects ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP;
                ALTER TABLE projects ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(255);

                -- Verification data table
                CREATE TABLE IF NOT EXISTS verification_data (
                    id SERIAL PRIMARY KEY,
                    project_id VARCHAR(255) REFERENCES projects(project_id),
                    verification_type VARCHAR(100),
                    data JSONB,
                    ai_score INTEGER,
                    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Users table (enhanced with full auth fields)
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    organization VARCHAR(255),
                    phone VARCHAR(50),
                    role VARCHAR(50) DEFAULT 'user',
                    email_verified BOOLEAN DEFAULT FALSE,
                    wallet_address VARCHAR(255),
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Add user_id column to projects table if not exists
                ALTER TABLE projects ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
                ALTER TABLE projects ADD COLUMN IF NOT EXISTS user_email VARCHAR(255);

                -- Carbon credits table
                CREATE TABLE IF NOT EXISTS carbon_credits (
                    id SERIAL PRIMARY KEY,
                    project_id VARCHAR(255) REFERENCES projects(project_id),
                    token_id VARCHAR(255),
                    amount DECIMAL(15,2),
                    price_per_credit DECIMAL(10,2),
                    blockchain_tx_hash VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- MRV data table (for AI verification data)
                CREATE TABLE IF NOT EXISTS mrv_data (
                    id SERIAL PRIMARY KEY,
                    project_id VARCHAR(255) REFERENCES projects(project_id),
                    data_type VARCHAR(100),
                    data JSONB,
                    file_hash VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Carbon credit purchases table
                CREATE TABLE IF NOT EXISTS purchases (
                    id SERIAL PRIMARY KEY,
                    transaction_id VARCHAR(255) UNIQUE NOT NULL,
                    buyer_email VARCHAR(255) NOT NULL,
                    project_id VARCHAR(255) REFERENCES projects(project_id),
                    project_name VARCHAR(255) NOT NULL,
                    credits_purchased INTEGER NOT NULL,
                    price_per_credit DECIMAL(10,2) NOT NULL,
                    total_amount DECIMAL(15,2) NOT NULL,
                    purchase_date DATE NOT NULL,
                    status VARCHAR(50) DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            '''
            
            cursor.execute(create_tables_query)
            print("✅ Database tables ensured")
            cursor.close()
            
        except Exception as e:
            print(f"❌ Error ensuring tables: {e}")

    def execute_query(self, query: str, params: tuple = None, retries: int = 3) -> Optional[List[Dict]]:
        """Execute a query and return results with retry logic"""
        for attempt in range(retries):
            if not self.connection:
                print(f"❌ No database connection (attempt {attempt + 1}/{retries})")
                if attempt < retries - 1:
                    print("🔄 Attempting to reconnect...")
                    self.connect()
                    continue
                return None
                
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                    cursor.close()
                    return [dict(row) for row in result]
                elif 'RETURNING' in query.upper():
                    # For INSERT/UPDATE with RETURNING clause
                    result = cursor.fetchall()
                    cursor.close()
                    return [dict(row) for row in result] if result else []
                else:
                    # For INSERT/UPDATE/DELETE without RETURNING
                    cursor.close()
                    return []
                    
            except psycopg2.OperationalError as e:
                print(f"⚠️ Connection error (attempt {attempt + 1}/{retries}): {e}")
                if hasattr(cursor, 'close'):
                    cursor.close()
                self.connection = None
                if attempt < retries - 1:
                    print("🔄 Reconnecting...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    self.connect()
                else:
                    return None
                    
            except Exception as e:
                print(f"❌ Query error: {e}")
                if hasattr(cursor, 'close'):
                    cursor.close()
                return None

    # Project operations
    def create_project(self, project_data: Dict) -> Optional[Dict]:
        """Create a new project"""
        query = '''
            INSERT INTO projects (project_id, title, description, location, ecosystem_type, 
                                area_hectares, carbon_estimate, blockchain_tx_hash, ipfs_hash, workflow_id, field_measurements, user_id, user_email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        '''
        
        params = (
            project_data.get('project_id'),
            project_data.get('title'),
            project_data.get('description'),
            json.dumps(project_data.get('location', {})),
            project_data.get('ecosystem_type'),
            project_data.get('area_hectares'),
            project_data.get('carbon_estimate'),
            project_data.get('blockchain_tx_hash'),
            project_data.get('ipfs_hash'),
            project_data.get('workflow_id'),
            json.dumps(project_data.get('field_measurements', {})),
            project_data.get('user_id', 'unknown'),
            project_data.get('user_email', 'unknown')
        )
        
        result = self.execute_query(query, params)
        return result[0] if result else None

    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get a project by ID with verification data"""
        query = 'SELECT * FROM projects WHERE project_id = %s'
        result = self.execute_query(query, (project_id,))
        
        if not result:
            return None
            
        project = result[0]
        
        # Add verification data
        verification_data = self.get_verification_data(project_id)
        if verification_data:
            latest_verification = verification_data[0]  # Most recent
            verification_info = latest_verification.get('data', {})
            project['verification_score'] = latest_verification.get('ai_score', 0)
            project['ai_verification'] = verification_info.get('ai_verification', {})
            project['enhanced_ai_verification'] = verification_info.get('enhanced_ai_verification', {})
        else:
            project['verification_score'] = 0
            project['ai_verification'] = {}
            project['enhanced_ai_verification'] = {}
            
        return project

    def update_project(self, project_id: str, update_data: Dict) -> Optional[Dict]:
        """Update a project with verification data support"""
        # First, get the current project
        current_project = self.get_project(project_id)
        if not current_project:
            return None
            
        # Handle AI verification data separately
        ai_verification = update_data.get('ai_verification')
        enhanced_ai_verification = update_data.get('enhanced_ai_verification')
        verification_score = update_data.get('verification_score')
        
        # Store verification data in verification_data table if provided
        if ai_verification or enhanced_ai_verification or verification_score is not None:
            verification_data = {
                'project_id': project_id,
                'verification_type': 'ai_analysis',
                'data': {
                    'ai_verification': ai_verification or {},
                    'enhanced_ai_verification': enhanced_ai_verification or {},
                    'verification_score': verification_score or 0
                },
                'ai_score': verification_score or 0
            }
            self.create_verification_data(verification_data)
        
        # Update basic project fields
        set_clauses = []
        params = []
        
        for key, value in update_data.items():
            if key in ['blockchain_tx_hash', 'ipfs_hash', 'workflow_id', 'status', 'area_hectares', 'carbon_estimate', 'carbon_credits', 'reviewer_comments', 'reviewed_at', 'reviewed_by']:
                set_clauses.append(f"{key} = %s")
                params.append(value)
        
        if not set_clauses:
            return self.get_project(project_id)
            
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(project_id)
        
        query = f'''
            UPDATE projects 
            SET {', '.join(set_clauses)}
            WHERE project_id = %s
            RETURNING *
        '''
        
        result = self.execute_query(query, tuple(params))
        updated_project = result[0] if result else None
        
        # Add verification data to the response
        if updated_project:
            verification_data = self.get_verification_data(project_id)
            if verification_data:
                latest_verification = verification_data[0]  # Most recent
                verification_info = latest_verification.get('data', {})
                updated_project['verification_score'] = latest_verification.get('ai_score', 0)
                updated_project['ai_verification'] = verification_info.get('ai_verification', {})
                updated_project['enhanced_ai_verification'] = verification_info.get('enhanced_ai_verification', {})
        
        return updated_project

    def get_all_projects(self, limit: int = 50) -> List[Dict]:
        """Get all projects with verification data"""
        query = 'SELECT * FROM projects ORDER BY created_at DESC LIMIT %s'
        result = self.execute_query(query, (limit,))
        
        if not result:
            return []
            
        # Add verification data to each project
        projects = []
        for project in result:
            project_id = project['project_id']
            verification_data = self.get_verification_data(project_id)
            
            if verification_data:
                latest_verification = verification_data[0]  # Most recent
                verification_info = latest_verification.get('data', {})
                project['verification_score'] = latest_verification.get('ai_score', 0)
                project['ai_verification'] = verification_info.get('ai_verification', {})
                project['enhanced_ai_verification'] = verification_info.get('enhanced_ai_verification', {})
            else:
                project['verification_score'] = 0
                project['ai_verification'] = {}
                project['enhanced_ai_verification'] = {}
                
            projects.append(project)
            
        return projects

    def get_projects_by_status(self, status: str) -> List[Dict]:
        """Get projects by status"""
        query = 'SELECT * FROM projects WHERE status = %s ORDER BY created_at DESC'
        result = self.execute_query(query, (status,))
        return result or []

    # Verification data operations
    def create_verification_data(self, verification_data: Dict) -> Optional[Dict]:
        """Create verification data"""
        try:
            # Safely extract data ensuring no 'bool' object errors
            project_id = verification_data.get('project_id', '')
            verification_type = verification_data.get('verification_type', 'ai_analysis')
            data = verification_data.get('data', {})
            ai_score = verification_data.get('ai_score', 0)
            
            # Ensure data is JSON serializable
            if not isinstance(data, dict):
                data = {'raw_data': str(data)}
            
            # Ensure ai_score is numeric
            if not isinstance(ai_score, (int, float)):
                ai_score = 0
                
            query = '''
                INSERT INTO verification_data (project_id, verification_type, data, ai_score)
                VALUES (%s, %s, %s, %s)
                RETURNING *
            '''
            
            params = (project_id, verification_type, json.dumps(data), ai_score)
            
            result = self.execute_query(query, params)
            if result and len(result) > 0:
                return result[0]
            else:
                print(f"✅ Verification data created for project {project_id} (no RETURNING data)")
                return {'project_id': project_id, 'verification_type': verification_type, 'ai_score': ai_score}
            
        except Exception as e:
            print(f"❌ Error creating verification data: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_verification_data(self, project_id: str) -> List[Dict]:
        """Get verification data for a project"""
        query = 'SELECT * FROM verification_data WHERE project_id = %s ORDER BY verified_at DESC'
        result = self.execute_query(query, (project_id,))
        return result or []

    # MRV data operations
    def create_mrv_data(self, mrv_data: Dict) -> Optional[Dict]:
        """Create MRV data entry"""
        query = '''
            INSERT INTO mrv_data (project_id, data_type, data, file_hash)
            VALUES (%s, %s, %s, %s)
            RETURNING *
        '''
        
        params = (
            mrv_data.get('project_id'),
            mrv_data.get('data_type'),
            json.dumps(mrv_data.get('data', {})),
            mrv_data.get('file_hash')
        )
        
        result = self.execute_query(query, params)
        return result[0] if result else None

    def get_mrv_data(self, project_id: str) -> List[Dict]:
        """Get MRV data for a project"""
        query = 'SELECT * FROM mrv_data WHERE project_id = %s ORDER BY created_at DESC'
        result = self.execute_query(query, (project_id,))
        return result or []

    # Analytics operations
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        stats = {}
        
        # Total projects
        result = self.execute_query('SELECT COUNT(*) as count FROM projects')
        stats['total_projects'] = result[0]['count'] if result else 0
        
        # Projects by status
        for status in ['submitted', 'approved', 'rejected', 'pending']:
            result = self.execute_query('SELECT COUNT(*) as count FROM projects WHERE status = %s', (status,))
            stats[f'{status}_projects'] = result[0]['count'] if result else 0
        
        # Recent projects
        result = self.execute_query('SELECT * FROM projects ORDER BY created_at DESC LIMIT 10')
        stats['recent_projects'] = result or []
        
        return stats

    def update_project_status(self, project_id: str, status: str, carbon_credits: float, admin_review: Dict) -> Optional[Dict]:
        """Update project status and admin review"""
        query = '''
            UPDATE projects 
            SET status = %s, carbon_credits = %s, admin_review = %s, updated_at = CURRENT_TIMESTAMP
            WHERE project_id = %s
            RETURNING *
        '''
        
        params = (
            status,
            carbon_credits,
            json.dumps(admin_review),
            project_id
        )
        
        result = self.execute_query(query, params)
        return result[0] if result else None

    # User Management Methods
    def create_user(self, user_data: Dict) -> Optional[Dict]:
        """Create a new user"""
        query = '''
            INSERT INTO users (user_id, email, password_hash, full_name, organization, phone, role, email_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        '''
        
        params = (
            user_data.get('user_id'),
            user_data.get('email'),
            user_data.get('password_hash'),
            user_data.get('full_name'),
            user_data.get('organization', ''),
            user_data.get('phone', ''),
            user_data.get('role', 'user'),
            user_data.get('email_verified', False)
        )
        
        result = self.execute_query(query, params)
        return result[0] if result else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        query = 'SELECT * FROM users WHERE email = %s'
        result = self.execute_query(query, (email,))
        return result[0] if result else None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by user_id"""
        query = 'SELECT * FROM users WHERE user_id = %s'
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def update_user_password(self, user_id: str, password_hash: str) -> bool:
        """Update user password"""
        query = '''
            UPDATE users 
            SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
        '''
        result = self.execute_query(query, (password_hash, user_id))
        return result is not None
    
    def update_user_last_login(self, user_id: str) -> bool:
        """Update user last login timestamp"""
        query = '''
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP
            WHERE user_id = %s
        '''
        result = self.execute_query(query, (user_id,))
        return result is not None
    
    def update_user_email_verified(self, user_id: str, verified: bool = True) -> bool:
        """Update user email verification status"""
        query = '''
            UPDATE users 
            SET email_verified = %s, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
        '''
        result = self.execute_query(query, (verified, user_id))
        return result is not None

    def create_purchase(self, purchase_data: Dict) -> Optional[Dict]:
        """Create a new purchase record"""
        query = '''
            INSERT INTO purchases (
                transaction_id, buyer_email, project_id, project_name,
                credits_purchased, price_per_credit, total_amount, 
                purchase_date, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        '''
        result = self.execute_query(query, (
            purchase_data['transaction_id'],
            purchase_data['buyer_email'], 
            purchase_data['project_id'],
            purchase_data['project_name'],
            purchase_data['credits_purchased'],
            purchase_data['price_per_credit'],
            purchase_data['total_amount'],
            purchase_data['purchase_date'],
            purchase_data.get('status', 'completed')
        ))
        return result[0] if result else None

    def get_purchases_by_buyer(self, buyer_email: str) -> List[Dict]:
        """Get all purchases by buyer email"""
        query = '''
            SELECT * FROM purchases 
            WHERE buyer_email = %s 
            ORDER BY created_at DESC
        '''
        result = self.execute_query(query, (buyer_email,))
        return result if result else []

    def get_all_purchases(self) -> List[Dict]:
        """Get all purchases"""
        query = '''
            SELECT * FROM purchases 
            ORDER BY created_at DESC
        '''
        result = self.execute_query(query)
        return result if result else []

    def get_project_total_sold(self, project_id: str) -> int:
        """Get total credits sold for a project"""
        query = '''
            SELECT COALESCE(SUM(credits_purchased), 0) as total_sold
            FROM purchases 
            WHERE project_id = %s AND status = 'completed'
        '''
        result = self.execute_query(query, (project_id,))
        return int(result[0]['total_sold']) if result else 0

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("🔒 Database connection closed")

# Global database instance
db_service = NeonDBService()

def get_db_service():
    """Get the global database service instance"""
    return db_service