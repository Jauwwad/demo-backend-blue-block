#!/usr/bin/env python3
"""
Blue Carbon MRV System - Simple HTTP Server
A basic HTTP server implementation for testing without external dependencies
"""

import http.server
import socketserver
import json
import urllib.parse
from datetime import datetime
import hashlib

try:
    from ai_verification import verify_project, get_verification_status
    AI_VERIFICATION_AVAILABLE = True
    print("✅ AI Verification module loaded successfully")
except ImportError:
    AI_VERIFICATION_AVAILABLE = False
    print("⚠️  AI Verification module not available")

# In-memory database
projects_db = {}
marketplace_db = {}

def initialize_sample_data():
    """Initialize with comprehensive sample data for Blue Carbon MRV system"""
    projects_db["BC_SAMPLE01"] = {
        "id": "BC_SAMPLE01",
        "project_name": "Sundarbans Mangrove Restoration Initiative",
        "ecosystem_type": "mangrove",
        "restoration_method": "Community-based restoration",
        "area_hectares": 150.5,
        "location": {"lat": 22.2587, "lng": 89.9486},
        "community_details": "Local fishing communities participating in restoration with training and compensation",
        "contact_email": "sundarbans@example.com",
        "phone_number": "+91 98765 43210",
        "status": "approved",
        "verification_score": 95,
        "created_at": "2024-01-15T10:30:00Z",
        "created_by": "community_leader_01",
        "media_count": {
            "photos": 25,
            "videos": 8,
            "documents": 12
        },
        "field_measurements": {
            "water_quality": {
                "ph_level": 7.8,
                "salinity": 15.2,
                "temperature": 28.5,
                "dissolved_oxygen": 6.8
            },
            "soil_analysis": {
                "carbon_content": 3.2,
                "nitrogen_level": 0.8,
                "phosphorus_level": 45,
                "moisture_content": 65
            },
            "biodiversity": {
                "species_count": 47,
                "vegetation_density": 78,
                "wildlife_observations": "Tigers, spotted deer, various bird species observed"
            },
            "environmental": {
                "tide_level": "medium",
                "weather_conditions": "sunny",
                "visibility": "good"
            }
        },
        "gps_data": {
            "waypoints": [
                {"id": 1, "lat": 22.2587, "lng": 89.9486, "timestamp": "2024-01-15T10:30:00Z"},
                {"id": 2, "lat": 22.2601, "lng": 89.9502, "timestamp": "2024-01-15T11:15:00Z"}
            ]
        },
        "ipfs_hashes": [
            {"hash": "QmXyZ123mangroveBeforeRestoration", "type": "photos", "filename": "mangrove_before.jpg"},
            {"hash": "QmAbc456restorationProcessVideo", "type": "videos", "filename": "restoration_process.mp4"}
        ],
        "carbon_credits": 1850,
        "blockchain_tx": "0x123abc...def789",
        "nccr_approval_date": "2024-01-20T14:00:00Z",
        "field_data_completeness": {
            "water_quality": True,
            "soil_analysis": True,
            "biodiversity": True,
            "environmental": True
        },
        "gps_waypoints": 15,
        "main_backend_status": "integrated"
    }
    
    projects_db["BC_SAMPLE02"] = {
        "id": "BC_SAMPLE02",
        "project_name": "Coastal Seagrass Conservation Project",
        "ecosystem_type": "seagrass",
        "restoration_method": "Assisted regeneration",
        "area_hectares": 75.0,
        "location": {"lat": 11.9139, "lng": 79.8145},
        "community_details": "Fishermen cooperatives working on seagrass bed protection",
        "contact_email": "seagrass@example.com",
        "phone_number": "+91 87654 32109",
        "status": "pending_verification",
        "verification_score": 75,
        "created_at": "2024-02-01T09:45:00Z",
        "created_by": "marine_biologist_02",
        "media_count": {
            "photos": 18,
            "videos": 4,
            "documents": 8
        },
        "field_measurements": {
            "water_quality": {
                "ph_level": 8.1,
                "salinity": 35.0,
                "temperature": 26.8,
                "dissolved_oxygen": 7.2
            },
            "soil_analysis": {
                "carbon_content": 2.8,
                "nitrogen_level": 0.6,
                "phosphorus_level": 38,
                "moisture_content": 85
            },
            "biodiversity": {
                "species_count": 32,
                "vegetation_density": 62,
                "wildlife_observations": "Sea turtles, various fish species"
            }
        },
        "gps_waypoints": 8,
        "ipfs_hashes": [
            {"hash": "QmDef789seagrassBedMapping", "type": "photos", "filename": "seagrass_bed.jpg"}
        ],
        "carbon_credits": 950,
        "field_data_completeness": {
            "water_quality": True,
            "soil_analysis": True,
            "biodiversity": True,
            "environmental": False
        },
        "main_backend_status": "pending"
    }
    
    projects_db["BC_SAMPLE03"] = {
        "id": "BC_SAMPLE03",
        "project_name": "Salt Marsh Rehabilitation Program",
        "ecosystem_type": "salt_marsh",
        "restoration_method": "Active restoration",
        "area_hectares": 45.2,
        "location": {"lat": 23.0225, "lng": 72.5714},
        "community_details": "University research collaboration with local communities",
        "contact_email": "saltmarsh@example.com",
        "phone_number": "+91 76543 21098",
        "status": "under_review",
        "verification_score": 85,
        "created_at": "2024-02-10T16:20:00Z",
        "created_by": "research_team_03",
        "media_count": {
            "photos": 22,
            "videos": 6,
            "documents": 15
        },
        "carbon_credits": 680,
        "gps_waypoints": 12,
        "field_data_completeness": {
            "water_quality": True,
            "soil_analysis": True,
            "biodiversity": False,
            "environmental": True
        },
        "main_backend_status": "integrated"
    }
    
    marketplace_db["LIST_SAMPLE01"] = {
        "listing_id": "LIST_SAMPLE01",
        "project_id": "BC_SAMPLE01",
        "credit_amount": 50.0,
        "price_per_credit": 15.0,
        "currency": "MATIC",
        "description": "Verified carbon credits from Mumbai mangrove project",
        "certification_level": "Gold Standard",
        "status": "active",
        "total_value": 750.0,
        "listed_at": "2024-03-01T12:00:00"
    }

class BlueCarbonMRVHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_cors_headers()
        
        if self.path == "/":
            self.send_json_response({"message": "Blue Carbon MRV System API", "status": "active"})
        elif self.path == "/health":
            self.send_json_response({
                "status": "healthy",
                "blockchain_connected": True,
                "ipfs_available": True,
                "timestamp": datetime.now().isoformat()
            })
        elif self.path == "/api/status":
            self.send_json_response({
                "status": "online",
                "backend": "python",
                "version": "2.0.0",
                "ai_verification": AI_VERIFICATION_AVAILABLE,
                "timestamp": datetime.now().isoformat()
            })
        
        elif self.path == "/api/verification/status":
            # Return AI verification system status
            self.send_json_response({
                "ai_verification_available": AI_VERIFICATION_AVAILABLE,
                "models_loaded": [
                    "image_recognition",
                    "fraud_detection", 
                    "data_validation",
                    "location_verification",
                    "temporal_analysis"
                ] if AI_VERIFICATION_AVAILABLE else [],
                "confidence_thresholds": {
                    "high": 0.85,
                    "medium": 0.65,
                    "low": 0.45
                },
                "status": "operational" if AI_VERIFICATION_AVAILABLE else "disabled"
            })
        
        elif self.path.startswith("/api/verification/"):
            # Get specific verification result
            verification_id = self.path.split("/")[-1]
            if verification_id == "status":
                pass  # Already handled above
            elif AI_VERIFICATION_AVAILABLE:
                try:
                    result = get_verification_status(verification_id)
                    self.send_json_response(result)
                except Exception as e:
                    self.send_error_response(404, f"Verification not found: {str(e)}")
            else:
                self.send_error_response(503, "AI verification service not available")
        elif self.path == "/api/projects":
            projects = list(projects_db.values())
            self.send_json_response({"projects": projects, "total": len(projects)})
        elif self.path.startswith("/api/projects/"):
            project_id = self.path.split("/")[-1]
            if project_id in projects_db:
                self.send_json_response(projects_db[project_id])
            else:
                self.send_error_response(404, "Project not found")
        elif self.path == "/api/admin/dashboard":
            # Enhanced admin dashboard with comprehensive statistics
            total_projects = len(projects_db)
            pending_review = len([p for p in projects_db.values() if p.get("status") in ["submitted", "pending_verification", "requires_review"]])
            ai_flagged = len([p for p in projects_db.values() if p.get("verification_score", 100) < 60])
            approved = len([p for p in projects_db.values() if p.get("status") == "approved"])
            rejected = len([p for p in projects_db.values() if p.get("status") == "rejected"])
            total_credits = sum(p.get("carbon_credits", 0) for p in projects_db.values())
            
            # Recent activities and alerts
            recent_projects = sorted(projects_db.values(), key=lambda x: x.get('created_at', ''), reverse=True)[:10]
            ai_alerts = [p for p in projects_db.values() if p.get('verification_score', 100) < 70]
            
            self.send_json_response({
                "status": "success",
                "statistics": {
                    "total_projects": total_projects,
                    "pending_review": pending_review,
                    "ai_flagged": ai_flagged,
                    "approved": approved,
                    "rejected": rejected,
                    "total_credits": total_credits,
                    "total_revenue": total_credits * 50  # Assuming $50 per credit
                },
                "recent_projects": recent_projects,
                "pending_projects": [p for p in projects_db.values() if p.get("status") in ["submitted", "pending_verification", "requires_review"]],
                "ai_alerts": ai_alerts,
                "system_status": {
                    "ai_verification": "operational" if AI_VERIFICATION_AVAILABLE else "offline",
                    "blockchain": "connected",
                    "ipfs": "online",
                    "backend": "running"
                }
            })
            
        elif self.path == "/api/admin/analytics":
            # Analytics endpoint for comprehensive reporting
            projects_list = list(projects_db.values())
            
            # Ecosystem distribution
            ecosystem_stats = {}
            for project in projects_list:
                ecosystem = project.get('ecosystem_type', 'unknown')
                ecosystem_stats[ecosystem] = ecosystem_stats.get(ecosystem, 0) + 1
            
            # Status distribution  
            status_stats = {}
            for project in projects_list:
                status = project.get('status', 'pending')
                status_stats[status] = status_stats.get(status, 0) + 1
            
            # Monthly submissions
            monthly_stats = {}
            for project in projects_list:
                created_date = project.get('created_at', '')
                try:
                    month = created_date[:7]  # YYYY-MM
                    monthly_stats[month] = monthly_stats.get(month, 0) + 1
                except:
                    pass
            
            self.send_json_response({
                "status": "success",
                "ecosystem_distribution": ecosystem_stats,
                "status_distribution": status_stats,
                "monthly_submissions": monthly_stats,
                "total_carbon_credits": sum(p.get('carbon_credits', 0) for p in projects_list),
                "average_ai_score": sum(p.get('verification_score', 0) for p in projects_list) / max(len(projects_list), 1),
                "verification_trends": {
                    "high_confidence": len([p for p in projects_list if p.get('verification_score', 0) >= 80]),
                    "medium_confidence": len([p for p in projects_list if 60 <= p.get('verification_score', 0) < 80]),
                    "low_confidence": len([p for p in projects_list if p.get('verification_score', 0) < 60])
                }
            })
        elif self.path == "/api/marketplace":
            listings = list(marketplace_db.values())
            self.send_json_response({"listings": listings, "total": len(listings)})
        elif self.path == "/api/reports/dashboard":
            total_projects = len(projects_db)
            total_credits = sum(p.get("carbon_credits", 0) for p in projects_db.values())
            total_area = sum(p["area_hectares"] for p in projects_db.values())
            
            status_counts = {}
            for project in projects_db.values():
                status = project["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
            
            self.send_json_response({
                "system_statistics": {
                    "total_projects": total_projects,
                    "total_carbon_credits": total_credits,
                    "total_area_restored_hectares": total_area,
                    "active_marketplace_listings": len(marketplace_db)
                },
                "project_status_breakdown": status_counts,
                "recent_activity": {
                    "recent_projects": list(projects_db.values())[-5:],
                    "recent_verifications": [],
                    "recent_marketplace_activity": list(marketplace_db.values())[-5:]
                },
                "blockchain_status": {
                    "network": "Polygon Mumbai",
                    "connected": True,
                    "latest_block": 12345678
                },
                "generated_at": datetime.now().isoformat()
            })
        else:
            self.send_error_response(404, "Endpoint not found")

    def do_POST(self):
        self.send_cors_headers()
        
        if self.path == "/api/projects/create":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                project_id = f"BC_{hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:8].upper()}"
                
                # Generate IPFS hashes for media files (simulated)
                ipfs_hashes = []
                media_files = data.get('media_files', {})
                
                for media_type, files in media_files.items():
                    for file_data in files:
                        if isinstance(file_data, dict) and 'name' in file_data:
                            # Simulate IPFS hash generation
                            content_hash = hashlib.sha256(
                                f"{file_data['name']}{file_data.get('timestamp', '')}{project_id}".encode()
                            ).hexdigest()
                            ipfs_hash = f"Qm{content_hash[:40]}"
                            
                            ipfs_hashes.append({
                                "hash": ipfs_hash,
                                "type": media_type,
                                "filename": file_data['name'],
                                "location": file_data.get('location', {}),
                                "timestamp": file_data.get('timestamp'),
                                "size": file_data.get('size', 0)
                            })
                
                # Calculate verification score based on data completeness
                verification_score = 0
                ai_verification_result = None
                
                # Run AI verification if available
                if AI_VERIFICATION_AVAILABLE:
                    try:
                        print(f"🤖 Running AI verification for project: {data.get('project_name', 'Unknown')}")
                        ai_verification_result = verify_project(data)
                        verification_score = int(ai_verification_result.get('overall_score', 0) * 100)
                        print(f"✅ AI verification completed with score: {verification_score}")
                    except Exception as e:
                        print(f"❌ AI verification failed: {str(e)}")
                        verification_score = self._calculate_manual_score(data, media_files)
                else:
                    verification_score = self._calculate_manual_score(data, media_files)
                
                # Determine project status based on verification score
                if verification_score >= 85:
                    status = "approved"
                elif verification_score >= 65:
                    status = "requires_review"
                else:
                    status = "pending_verification"
                
                # Get field and GPS data for completeness check
                field_data = data.get('field_measurements', {})
                gps_data = data.get('gps_data', {})
                
                project = {
                    "id": project_id,
                    "created_by": "demo_user",
                    "created_at": datetime.now().isoformat(),
                    "status": status,
                    "verification_score": verification_score,
                    "ai_verification": ai_verification_result,
                    "ipfs_hashes": ipfs_hashes,
                    "media_count": {
                        "photos": len(media_files.get('photos', [])),
                        "videos": len(media_files.get('videos', [])),
                        "documents": len(media_files.get('documents', []))
                    },
                    "field_data_completeness": {
                        "water_quality": bool(field_data.get('water_quality', {}).get('ph_level')),
                        "soil_analysis": bool(field_data.get('soil_analysis', {}).get('carbon_content')),
                        "biodiversity": bool(field_data.get('biodiversity', {}).get('species_count')),
                        "environmental": bool(field_data.get('environmental', {}).get('weather_conditions'))
                    },
                    "gps_waypoints": len(gps_data.get('waypoints', [])),
                    **data
                }
                
                projects_db[project_id] = project
                
                # **INTEGRATION: Send to main blockchain backend**
                try:
                    import urllib.request
                    import urllib.parse
                    
                    integration_data = {
                        **project,
                        "source": "user_app_v2",
                        "integration_timestamp": datetime.now().isoformat(),
                        "verification_ready": verification_score >= 50
                    }
                    
                    req_data = json.dumps(integration_data).encode('utf-8')
                    req = urllib.request.Request(
                        "http://localhost:8001/api/workflow/project/upload",
                        data=req_data,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    with urllib.request.urlopen(req, timeout=10) as response:
                        if response.status == 200:
                            result = json.loads(response.read().decode('utf-8'))
                            project["blockchain_tx"] = result.get("blockchain_tx")
                            project["workflow_id"] = result.get("workflowId")
                            project["main_backend_status"] = "integrated"
                        else:
                            project["main_backend_status"] = "failed"
                            
                except Exception as e:
                    print(f"Warning: Failed to integrate with main backend: {e}")
                    project["main_backend_status"] = "offline"
                
                self.send_json_response({
                    "project_id": project_id,
                    "status": "created", 
                    "verification_score": verification_score,
                    "ipfs_hashes": len(ipfs_hashes),
                    "message": f"Project submitted for AI verification (Score: {verification_score}/100)",
                    "next_steps": [
                        "🤖 AI/ML verification in progress",
                        "👩‍💼 NCCR admin review pending", 
                        "⛓️ Blockchain registration queued",
                        "🪙 Carbon credit tokenization planned"
                    ],
                    "blockchain_integration": project.get("blockchain_tx") is not None,
                    "estimated_verification_time": "2-4 hours"
                })
            except Exception as e:
                self.send_error_response(400, str(e))
                
        elif self.path.startswith("/api/admin/projects/") and self.path.endswith("/review"):
            # Admin project review endpoint
            try:
                project_id = self.path.split('/')[-2]
                content_length = int(self.headers['Content-Length'])
                review_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
                
                # Find project
                if project_id not in projects_db:
                    self.send_error_response(404, "Project not found")
                    return
                
                project = projects_db[project_id]
                
                # Update project with review
                decision = review_data.get('decision')
                projects_db[project_id].update({
                    'status': decision,
                    'admin_review': {
                        'decision': decision,
                        'comments': review_data.get('comments', ''),
                        'reviewer_id': review_data.get('reviewer_id', 'admin'),
                        'review_timestamp': review_data.get('review_timestamp'),
                        'credits_awarded': review_data.get('credits_awarded', 0) if decision == 'approved' else 0,
                        'compliance_notes': review_data.get('compliance_notes', '')
                    },
                    'updated_at': datetime.now().isoformat()
                })
                
                # If approved, calculate carbon credits
                if decision == 'approved':
                    credits_awarded = int(review_data.get('credits_awarded', 0))
                    if credits_awarded > 0:
                        projects_db[project_id]['carbon_credits'] = credits_awarded
                    else:
                        # Auto-calculate based on area and ecosystem
                        area = float(project.get('area_hectares', 0))
                        ecosystem = project.get('ecosystem_type', 'mangrove')
                        
                        # Credit calculation factors
                        credit_factors = {
                            'mangrove': 3.2,  # tCO2/hectare/year
                            'seagrass': 2.8,
                            'salt_marsh': 2.5,
                            'coastal_wetland': 2.0
                        }
                        
                        annual_credits = area * credit_factors.get(ecosystem, 2.0)
                        projects_db[project_id]['carbon_credits'] = round(annual_credits, 2)
                
                self.send_json_response({
                    'status': 'success',
                    'message': f'Project {decision} successfully',
                    'project': projects_db[project_id]
                })
                
            except Exception as e:
                self.send_error_response(500, f'Review error: {str(e)}')
        else:
            self.send_error_response(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_cors_headers()
        self.end_headers()

    def send_cors_headers(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:8004')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-type', 'application/json')

    def send_json_response(self, data):
        response = json.dumps(data, indent=2)
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        error_response = json.dumps({"error": message})
        self.wfile.write(error_response.encode('utf-8'))
    
    def _calculate_manual_score(self, data, media_files):
        """Calculate verification score manually when AI is not available"""
        score = 0
        
        # Basic info (20 points)
        if data.get('project_name') and data.get('ecosystem_type'):
            score += 20
        
        # Location and GPS data (20 points)
        if data.get('location') and data.get('area_hectares'):
            score += 20
        
        # Media evidence (25 points)
        total_media = sum(len(files) for files in media_files.values())
        if total_media >= 5:
            score += 25
        elif total_media >= 3:
            score += 15
        elif total_media >= 1:
            score += 10
        
        # Field measurements (25 points)
        field_data = data.get('field_measurements', {})
        if any(field_data.get(category, {}).values() for category in field_data):
            score += 25
        
        # GPS waypoints (10 points)
        gps_data = data.get('gps_data', {})
        if gps_data.get('waypoints'):
            score += 10
        
        return score

def main():
    initialize_sample_data()
    
    PORT = 8002
    Handler = BlueCarbonMRVHandler
    
    print("🌊 Blue Carbon MRV System - Simple HTTP Server")
    print(f"🔧 Backend API: http://localhost:{PORT}")
    print("✅ Starting server...")
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()
