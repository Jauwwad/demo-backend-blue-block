# Simple FastAPI Backend for Blue Carbon MRV System
# Minimal dependencies version for quick testing

try:
    from fastapi import FastAPI, HTTPException, Form
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
except ImportError:
    print("Installing FastAPI...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "python-multipart", "pydantic"])
    from fastapi import FastAPI, HTTPException, Form
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import hashlib
import os

# Initialize FastAPI app
app = FastAPI(
    title="Blue Carbon MRV System",
    description="Blockchain-based Monitoring, Reporting, and Verification system for blue carbon projects",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class ProjectData(BaseModel):
    project_name: str
    location: Dict[str, float]  # lat, lng
    area_hectares: float
    ecosystem_type: str
    restoration_method: str
    community_details: str
    contact_email: str
    phone_number: str

# In-memory database for demo
projects_db = {}
mrv_data_db = {}
verifications_db = {}
marketplace_db = {}

# Sample data for demo
def initialize_sample_data():
    """Initialize with sample data for demo purposes"""
    sample_projects = [
        {
            "id": "BC_SAMPLE01",
            "project_name": "Mumbai Coastal Mangrove Restoration",
            "location": {"lat": 19.0760, "lng": 72.8777},
            "area_hectares": 25.5,
            "ecosystem_type": "mangrove",
            "restoration_method": "Natural regeneration",
            "community_details": "Local fishing community of 150 families involved in restoration and monitoring activities",
            "contact_email": "mumbai.mangroves@example.com",
            "phone_number": "+91 98765 43210",
            "created_by": "field_officer_1",
            "created_at": "2024-01-15T10:30:00",
            "status": "approved",
            "carbon_credits": 95.6
        },
        {
            "id": "BC_SAMPLE02", 
            "project_name": "Kerala Backwater Seagrass Project",
            "location": {"lat": 9.9312, "lng": 76.2673},
            "area_hectares": 18.2,
            "ecosystem_type": "seagrass",
            "restoration_method": "Active restoration",
            "community_details": "Coastal village cooperative with 80 members participating in seagrass cultivation",
            "contact_email": "kerala.seagrass@example.com", 
            "phone_number": "+91 94567 89012",
            "created_by": "field_officer_2",
            "created_at": "2024-02-20T14:15:00",
            "status": "verified",
            "carbon_credits": 65.8
        },
        {
            "id": "BC_SAMPLE03",
            "project_name": "Goa Salt Marsh Conservation",
            "location": {"lat": 15.2993, "lng": 74.1240},
            "area_hectares": 12.8,
            "ecosystem_type": "salt_marsh", 
            "restoration_method": "Assisted regeneration",
            "community_details": "Salt pan workers association restoring degraded marshlands for carbon sequestration",
            "contact_email": "goa.saltmarsh@example.com",
            "phone_number": "+91 87654 32109",
            "created_by": "field_officer_3", 
            "created_at": "2024-03-10T09:45:00",
            "status": "submitted",
            "carbon_credits": 0
        }
    ]
    
    for project in sample_projects:
        projects_db[project["id"]] = project

    # Sample marketplace listings
    marketplace_db["LIST_SAMPLE01"] = {
        "listing_id": "LIST_SAMPLE01",
        "project_id": "BC_SAMPLE01",
        "credit_amount": 50.0,
        "price_per_credit": 15.0,
        "currency": "MATIC",
        "description": "Verified carbon credits from Mumbai mangrove restoration project",
        "certification_level": "Gold Standard",
        "listed_by": "project_owner_1",
        "listed_at": "2024-03-01T12:00:00",
        "status": "active",
        "total_value": 750.0
    }

# Initialize sample data on startup
initialize_sample_data()

def generate_project_id() -> str:
    timestamp = str(int(datetime.now().timestamp()))
    hash_obj = hashlib.sha256(timestamp.encode())
    return f"BC_{hash_obj.hexdigest()[:8].upper()}"

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Blue Carbon MRV System API", "status": "active"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "blockchain_connected": True,  # Simulated for demo
        "ipfs_available": True,  # Simulated for demo
        "timestamp": datetime.now().isoformat()
    }

# Projects API
@app.post("/api/projects/create")
async def create_project(project: ProjectData):
    """Create a new blue carbon restoration project"""
    project_id = generate_project_id()
    
    project_data = {
        "id": project_id,
        "created_by": "demo_user",
        "created_at": datetime.now().isoformat(),
        "status": "submitted",
        **project.dict()
    }
    
    projects_db[project_id] = project_data
    
    return {
        "project_id": project_id,
        "status": "created",
        "message": "Project submitted for NCCR review"
    }

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project details"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    return projects_db[project_id]

@app.get("/api/projects")
async def list_projects(status: Optional[str] = None):
    """List all projects with optional status filter"""
    projects = list(projects_db.values())
    if status:
        projects = [p for p in projects if p["status"] == status]
    return {"projects": projects, "total": len(projects)}

# Admin API
@app.post("/api/admin/projects/{project_id}/review")
async def review_project(project_id: str, action: str = Form(...), comments: str = Form(...)):
    """Admin review project"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
    
    project["admin_review"] = {
        "action": action,
        "comments": comments,
        "reviewed_by": "admin_user",
        "reviewed_at": datetime.now().isoformat()
    }
    
    project["status"] = "approved" if action == "approve" else "rejected"
    
    return {
        "project_id": project_id,
        "status": project["status"],
        "message": f"Project {action}d by NCCR admin"
    }

@app.get("/api/admin/dashboard")
async def admin_dashboard():
    """Admin dashboard"""
    total_projects = len(projects_db)
    pending_review = len([p for p in projects_db.values() if p["status"] == "submitted"])
    approved = len([p for p in projects_db.values() if p["status"] == "approved"])
    rejected = len([p for p in projects_db.values() if p["status"] == "rejected"])
    
    return {
        "statistics": {
            "total_projects": total_projects,
            "pending_review": pending_review,
            "approved": approved,
            "rejected": rejected
        },
        "recent_projects": list(projects_db.values())[-10:],
        "pending_projects": [p for p in projects_db.values() if p["status"] == "submitted"]
    }

# Marketplace API
@app.get("/api/marketplace")
async def get_marketplace_listings(status: str = "active"):
    """Get marketplace listings"""
    listings = [l for l in marketplace_db.values() if l["status"] == status]
    return {"listings": listings, "total": len(listings)}

@app.post("/api/marketplace/{listing_id}/purchase")
async def purchase_credits(listing_id: str, quantity: float = Form(...)):
    """Purchase carbon credits"""
    if listing_id not in marketplace_db:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    listing = marketplace_db[listing_id]
    if listing["status"] != "active":
        raise HTTPException(status_code=400, detail="Listing is not active")
    
    if quantity > listing["credit_amount"]:
        raise HTTPException(status_code=400, detail="Insufficient credits available")
    
    purchase_value = quantity * listing["price_per_credit"]
    
    # Update listing
    listing["credit_amount"] -= quantity
    if listing["credit_amount"] <= 0:
        listing["status"] = "sold_out"
    
    return {
        "quantity": quantity,
        "total_paid": purchase_value,
        "status": "completed",
        "message": "Carbon credits purchased successfully"
    }

# Reports API
@app.get("/api/reports/dashboard")
async def system_dashboard():
    """System dashboard with statistics"""
    total_projects = len(projects_db)
    total_credits_issued = sum(p.get("carbon_credits", 0) for p in projects_db.values())
    total_area_restored = sum(p["area_hectares"] for p in projects_db.values())
    
    status_counts = {}
    for project in projects_db.values():
        status = project["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "system_statistics": {
            "total_projects": total_projects,
            "total_carbon_credits": total_credits_issued,
            "total_area_restored_hectares": total_area_restored,
            "active_marketplace_listings": len([l for l in marketplace_db.values() if l["status"] == "active"])
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
    }

if __name__ == "__main__":
    try:
        import uvicorn
    except ImportError:
        print("Installing uvicorn...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uvicorn"])
        import uvicorn
    
    print("🌊 Blue Carbon MRV System - FastAPI Backend")
    print("🔧 Backend API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("✅ Starting server...")
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
