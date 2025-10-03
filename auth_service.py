#!/usr/bin/env python3
"""
Authentication Service for Blue Carbon MRV System
Handles user registration, login, OTP verification, and password reset
"""

import os
import json
import random
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import re

class AuthService:
    def __init__(self, db_service):
        self.db_service = db_service
        
        # Email configuration from environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL', 'your-email@gmail.com')
        self.sender_password = os.getenv('SENDER_APP_PASSWORD', '')  # 16-digit Google App Password
        
        # Check if email is configured
        self.email_configured = bool(self.sender_email and self.sender_password and 
                                     self.sender_email != 'your-email@gmail.com')
        
        if self.email_configured:
            print(f"✅ Email service configured: {self.sender_email}")
        else:
            print("⚠️  Email not configured - emails will be printed to console")
            print("   Set SENDER_EMAIL and SENDER_APP_PASSWORD environment variables")
        
        # OTP settings
        self.otp_expiry_minutes = 10
        self.max_otp_attempts = 3
        
        # OTP storage (in production, use Redis or database)
        self.otp_storage = {}
        
    def generate_otp(self) -> str:
        """Generate 6-digit OTP"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        return True, "Password is valid"
    
    def send_email(self, to_email, subject, html_body):
        """
        Send email using SMTP.
        If email is not configured, prints to console instead.
        """
        try:
            if self.email_configured:
                # Production mode - send actual email
                msg = MIMEMultipart('alternative')
                msg['From'] = self.sender_email
                msg['To'] = to_email
                msg['Subject'] = subject
                
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
                
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)
                
                print(f"✅ Email sent successfully to {to_email}")
            else:
                # Development mode - print to console
                print(f"\n{'='*60}")
                print(f"📧 EMAIL NOTIFICATION (Development Mode)")
                print(f"{'='*60}")
                print(f"To: {to_email}")
                print(f"Subject: {subject}")
                print(f"\n{html_body}")
                print(f"{'='*60}\n")
            
            return True
        except Exception as e:
            print(f"❌ Error sending email: {str(e)}")
            return False
    
    def send_otp(self, email: str, purpose: str = "registration") -> Dict:
        """Send OTP to email"""
        try:
            # Generate OTP
            otp = self.generate_otp()
            expires_at = datetime.now() + timedelta(minutes=self.otp_expiry_minutes)
            
            # Store OTP
            self.otp_storage[email] = {
                "otp": otp,
                "expires_at": expires_at,
                "purpose": purpose,
                "attempts": 0
            }
            
            # Prepare email content
            if purpose == "registration":
                subject = "🌊 Blue Carbon MRV - Verify Your Email"
                body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #1976d2; text-align: center;">🌊 Welcome to Blue Carbon MRV System</h2>
                        <p style="font-size: 16px; color: #333;">Thank you for registering with Blue Carbon MRV System!</p>
                        <p style="font-size: 16px; color: #333;">Your verification code is:</p>
                        <div style="background-color: #e3f2fd; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0;">
                            <h1 style="color: #1976d2; font-size: 36px; letter-spacing: 5px; margin: 0;">{otp}</h1>
                        </div>
                        <p style="font-size: 14px; color: #666;">This code will expire in {self.otp_expiry_minutes} minutes.</p>
                        <p style="font-size: 14px; color: #666;">If you didn't request this code, please ignore this email.</p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="font-size: 12px; color: #999; text-align: center;">Blue Carbon MRV System - Protecting Coastal Ecosystems</p>
                    </div>
                </body>
                </html>
                """
            elif purpose == "reset":
                subject = "🔐 Blue Carbon MRV - Password Reset Code"
                body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #1976d2; text-align: center;">🔐 Password Reset Request</h2>
                        <p style="font-size: 16px; color: #333;">You requested to reset your password.</p>
                        <p style="font-size: 16px; color: #333;">Your password reset code is:</p>
                        <div style="background-color: #e3f2fd; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0;">
                            <h1 style="color: #1976d2; font-size: 36px; letter-spacing: 5px; margin: 0;">{otp}</h1>
                        </div>
                        <p style="font-size: 14px; color: #666;">This code will expire in {self.otp_expiry_minutes} minutes.</p>
                        <p style="font-size: 14px; color: #d32f2f;">If you didn't request this, please secure your account immediately.</p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="font-size: 12px; color: #999; text-align: center;">Blue Carbon MRV System - Protecting Coastal Ecosystems</p>
                    </div>
                </body>
                </html>
                """
            else:
                return {"success": False, "error": "Invalid OTP purpose"}
            
            # Send email
            email_sent = self.send_email(email, subject, body)
            
            if email_sent:
                return {
                    "success": True,
                    "message": f"OTP sent to {email}",
                    "expires_in_minutes": self.otp_expiry_minutes
                }
            else:
                return {"success": False, "error": "Failed to send OTP email"}
                
        except Exception as e:
            print(f"❌ Error sending OTP: {e}")
            return {"success": False, "error": str(e)}
    
    def verify_otp(self, email: str, otp: str, purpose: str = "registration") -> Dict:
        """Verify OTP"""
        try:
            # Check if OTP exists
            if email not in self.otp_storage:
                return {"success": False, "error": "No OTP found for this email"}
            
            stored_data = self.otp_storage[email]
            
            # Check purpose
            if stored_data["purpose"] != purpose:
                return {"success": False, "error": "Invalid OTP purpose"}
            
            # Check expiry
            if datetime.now() > stored_data["expires_at"]:
                del self.otp_storage[email]
                return {"success": False, "error": "OTP has expired"}
            
            # Check attempts (max 3)
            if stored_data["attempts"] >= 3:
                del self.otp_storage[email]
                return {"success": False, "error": "Too many failed attempts. Request a new OTP."}
            
            # Verify OTP
            if stored_data["otp"] == otp:
                del self.otp_storage[email]
                return {"success": True, "message": "OTP verified successfully"}
            else:
                stored_data["attempts"] += 1
                remaining = 3 - stored_data["attempts"]
                return {
                    "success": False, 
                    "error": f"Invalid OTP. {remaining} attempts remaining."
                }
                
        except Exception as e:
            print(f"❌ Error verifying OTP: {e}")
            return {"success": False, "error": str(e)}
    
    def register_user(self, user_data: Dict) -> Dict:
        """Register new user (after OTP verification)"""
        try:
            email = user_data.get('email')
            password = user_data.get('password')
            full_name = user_data.get('full_name')
            organization = user_data.get('organization', '')
            phone = user_data.get('phone', '')
            role = user_data.get('role', 'user')
            
            # Validate required fields
            if not all([email, password, full_name]):
                return {"success": False, "error": "Email, password, and full name are required"}
            
            # Validate email
            if not self.validate_email(email):
                return {"success": False, "error": "Invalid email format"}
            
            # Validate password
            is_valid, message = self.validate_password(password)
            if not is_valid:
                return {"success": False, "error": message}
            
            # Check if user already exists
            existing_user = self.db_service.get_user_by_email(email)
            if existing_user:
                return {"success": False, "error": "User with this email already exists"}
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Generate user ID
            user_id = f"USER_{secrets.token_hex(8).upper()}"
            
            # Create user in database
            user_data_db = {
                'user_id': user_id,
                'email': email,
                'password_hash': password_hash,
                'full_name': full_name,
                'organization': organization,
                'phone': phone,
                'role': role,
                'email_verified': True,  # Already verified via OTP
                'created_at': datetime.now().isoformat()
            }
            
            result = self.db_service.create_user(user_data_db)
            
            if result:
                # Send welcome email
                self.send_welcome_email(email, full_name)
                
                return {
                    "success": True,
                    "message": "User registered successfully",
                    "user": {
                        "user_id": user_id,
                        "email": email,
                        "full_name": full_name,
                        "role": role
                    }
                }
            else:
                return {"success": False, "error": "Failed to create user in database"}
                
        except Exception as e:
            print(f"❌ Error registering user: {e}")
            return {"success": False, "error": str(e)}
    
    def login_user(self, email: str, password: str) -> Dict:
        """Login user"""
        try:
            # Get user from database
            user = self.db_service.get_user_by_email(email)
            
            if not user:
                return {"success": False, "error": "Invalid email or password"}
            
            # Verify password
            password_hash = self.hash_password(password)
            
            if user['password_hash'] != password_hash:
                return {"success": False, "error": "Invalid email or password"}
            
            # Check if email is verified
            if not user.get('email_verified', False):
                return {"success": False, "error": "Email not verified. Please verify your email first."}
            
            # Generate session token
            session_token = secrets.token_hex(32)
            
            # Update last login
            self.db_service.update_user_last_login(user['user_id'])
            
            return {
                "success": True,
                "message": "Login successful",
                "user": {
                    "user_id": user['user_id'],
                    "email": user['email'],
                    "full_name": user['full_name'],
                    "organization": user.get('organization', ''),
                    "role": user.get('role', 'user')
                },
                "token": session_token
            }
            
        except Exception as e:
            print(f"❌ Error logging in user: {e}")
            return {"success": False, "error": str(e)}
    
    def reset_password(self, email: str, new_password: str) -> Dict:
        """Reset user password (after OTP verification)"""
        try:
            # Get user
            user = self.db_service.get_user_by_email(email)
            
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Validate new password
            is_valid, message = self.validate_password(new_password)
            if not is_valid:
                return {"success": False, "error": message}
            
            # Hash new password
            password_hash = self.hash_password(new_password)
            
            # Update password in database
            result = self.db_service.update_user_password(user['user_id'], password_hash)
            
            if result:
                # Send confirmation email
                self.send_password_reset_confirmation(email, user['full_name'])
                
                return {
                    "success": True,
                    "message": "Password reset successfully"
                }
            else:
                return {"success": False, "error": "Failed to update password"}
                
        except Exception as e:
            print(f"❌ Error resetting password: {e}")
            return {"success": False, "error": str(e)}
    
    def send_welcome_email(self, email: str, full_name: str) -> bool:
        """Send welcome email after registration"""
        subject = "🎉 Welcome to Blue Carbon MRV System!"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #1976d2; text-align: center;">🌊 Welcome to Blue Carbon MRV!</h2>
                <p style="font-size: 16px; color: #333;">Dear {full_name},</p>
                <p style="font-size: 16px; color: #333;">Thank you for joining the Blue Carbon MRV System. Your account has been successfully created!</p>
                <p style="font-size: 16px; color: #333;">You can now:</p>
                <ul style="font-size: 14px; color: #666;">
                    <li>Create and manage blue carbon restoration projects</li>
                    <li>Upload field data and media evidence</li>
                    <li>Track verification progress</li>
                    <li>Earn carbon credits for verified projects</li>
                    <li>Trade carbon credits in the marketplace</li>
                </ul>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:3000/login" style="background-color: #1976d2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-size: 16px;">Login to Dashboard</a>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #999; text-align: center;">Blue Carbon MRV System - Protecting Coastal Ecosystems</p>
            </div>
        </body>
        </html>
        """
        return self.send_email(email, subject, body)
    
    def send_password_reset_confirmation(self, email: str, full_name: str) -> bool:
        """Send password reset confirmation email"""
        subject = "✅ Password Reset Successful"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #2e7d32; text-align: center;">✅ Password Reset Successful</h2>
                <p style="font-size: 16px; color: #333;">Dear {full_name},</p>
                <p style="font-size: 16px; color: #333;">Your password has been successfully reset.</p>
                <p style="font-size: 14px; color: #666;">If you did not make this change, please contact us immediately.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:3000/login" style="background-color: #1976d2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-size: 16px;">Login Now</a>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #999; text-align: center;">Blue Carbon MRV System - Protecting Coastal Ecosystems</p>
            </div>
        </body>
        </html>
        """
        return self.send_email(email, subject, body)
    
    def send_project_status_notification(self, email: str, full_name: str, project_name: str, 
                                        status: str, comments: str = "", carbon_credits: int = 0) -> bool:
        """Send email notification when project is approved/rejected"""
        
        if status == "approved":
            subject = "✅ Project Approved - Blue Carbon MRV"
            status_color = "#2e7d32"
            status_text = "APPROVED"
            status_icon = "✅"
            message = f"Congratulations! Your project has been approved and {carbon_credits} carbon credits have been awarded."
        else:
            subject = "❌ Project Status Update - Blue Carbon MRV"
            status_color = "#d32f2f"
            status_text = "REJECTED"
            status_icon = "❌"
            message = "Unfortunately, your project has not been approved at this time."
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: {status_color}; text-align: center;">{status_icon} Project {status_text}</h2>
                <p style="font-size: 16px; color: #333;">Dear {full_name},</p>
                <p style="font-size: 16px; color: #333;">{message}</p>
                
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Project:</strong> {project_name}</p>
                    <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{status_text}</span></p>
                    {f'<p style="margin: 5px 0;"><strong>Carbon Credits Awarded:</strong> {carbon_credits}</p>' if status == "approved" else ''}
                </div>
                
                {f'<div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;"><p style="margin: 0; color: #856404;"><strong>Reviewer Comments:</strong><br>{comments}</p></div>' if comments else ''}
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:3000/dashboard" style="background-color: #1976d2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-size: 16px;">View Dashboard</a>
                </div>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #999; text-align: center;">Blue Carbon MRV System - Protecting Coastal Ecosystems</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(email, subject, body)

# Global auth service (will be initialized with db_service)
auth_service = None

def get_auth_service(db_service):
    """Get or create auth service instance"""
    global auth_service
    if auth_service is None:
        auth_service = AuthService(db_service)
    return auth_service
