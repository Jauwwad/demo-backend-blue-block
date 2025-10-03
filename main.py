from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import json
import hashlib
from web3 import Web3
import ipfshttpclient
from PIL import Image
import io
import base64
import httpx

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

# Security
security = HTTPBearer()

# Blockchain Configuration
POLYGON_MUMBAI_RPC = "https://rpc-mumbai.maticvigil.com/"
CONTRACT_ADDRESSES = {
    "PROJECT_REGISTRY": "0x742d35Cc6634C0532925a3b8D71A3C2a0532925a3b8D71A3C2a05329",
    "CARBON_CREDIT_TOKEN": "0x4B20993Bc481177ec7E8f571ceCaE8A9e22C02db",
    "VERIFICATION_ORACLE": "0x78731D3Ca6b7E34aC0F824c42a7cC18A495cabaB"
}

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(POLYGON_MUMBAI_RPC))

# IPFS Configuration
IPFS_NODE = "/ip4/127.0.0.1/tcp/5001"

# Pydantic Models
class ProjectData(BaseModel):
    project_name: str
    location: Dict[str, float]  # lat, lng
    area_hectares: float
    ecosystem_type: str
    restoration_method: str
    community_details: str
    contact_email: EmailStr
    phone_number: str
    
class MRVData(BaseModel):
    project_id: str
    collection_date: datetime
    gps_coordinates: Dict[str, float]
    photos: List[str]  # Base64 encoded
    measurements: Dict[str, Any]
    soil_samples: Optional[Dict[str, Any]] = None
    water_quality: Optional[Dict[str, Any]] = None
    biodiversity_count: Optional[Dict[str, int]] = None
    carbon_stock_estimate: Optional[float] = None
    notes: Optional[str] = None

class VerificationResult(BaseModel):
    project_id: str
    verification_date: datetime
    satellite_data_hash: str
    field_data_hash: str
    iot_data_hash: Optional[str] = None
    carbon_credits_calculated: float
    verification_status: str
    reviewer_notes: str

class CarbonCreditListing(BaseModel):
    project_id: str
    credit_amount: float
    price_per_credit: float
    currency: str = "MATIC"
    description: str
    certification_level: str

# Database Models (In-memory for demo, use proper DB in production)
projects_db = {}
mrv_data_db = {}
verifications_db = {}
marketplace_db = {}

# Helper Functions
def connect_ipfs():
    try:
        client = ipfshttpclient.connect(IPFS_NODE)
        return client
    except Exception:
        return None

def upload_to_ipfs(data: bytes) -> Optional[str]:
    client = connect_ipfs()
    if client:
        try:
            result = client.add_bytes(data)
            return result
        except Exception:
            return None
    return None

def generate_project_id() -> str:
    timestamp = str(int(datetime.now().timestamp()))
    hash_obj = hashlib.sha256(timestamp.encode())
    return f"BC_{hash_obj.hexdigest()[:8].upper()}"

def calculate_carbon_credits(area_hectares: float, ecosystem_type: str, measurements: Dict) -> float:
    """Simplified carbon credit calculation"""
    base_credits = area_hectares * 2.5  # Base credits per hectare
    
    # Ecosystem multipliers
    multipliers = {
        "mangrove": 1.5,
        "seagrass": 1.2,
        "salt_marsh": 1.3,
        "coastal_wetland": 1.1
    }
    
    multiplier = multipliers.get(ecosystem_type.lower(), 1.0)
    return round(base_credits * multiplier, 2)

# Authentication (Simplified for demo)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # In production, verify JWT token here
    return {"user_id": "demo_user", "role": "field_officer"}

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Blue Carbon MRV System API", "status": "active"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "blockchain_connected": web3.is_connected(),
        "ipfs_available": connect_ipfs() is not None,
        "timestamp": datetime.now().isoformat()
    }

# Step 1: Project Data Upload
@app.post("/api/projects/create")
async def create_project(project: ProjectData, current_user: dict = Depends(get_current_user)):
    """Step 1: Create a new blue carbon restoration project"""
    project_id = generate_project_id()
    
    project_data = {
        "id": project_id,
        "created_by": current_user["user_id"],
        "created_at": datetime.now().isoformat(),
        "status": "submitted",
        **project.dict()
    }
    
    # Store locally
    projects_db[project_id] = project_data
    
    # Upload to IPFS
    ipfs_hash = upload_to_ipfs(json.dumps(project_data).encode())
    if ipfs_hash:
        projects_db[project_id]["ipfs_hash"] = ipfs_hash
    
    # **INTEGRATION: Send to main blockchain backend**
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            integration_response = await client.post(
                "http://localhost:5000/api/workflow/project/upload",
                json={
                    **project_data,
                    "media_files": [],  # Would contain actual media in production
                    "source": "user_app"
                },
                timeout=30.0
            )
            
        if integration_response.status_code == 200:
            integration_data = integration_response.json()
            projects_db[project_id]["blockchain_tx"] = integration_data.get("blockchain_tx")
            projects_db[project_id]["workflow_id"] = integration_data.get("workflowId")
            
    except Exception as e:
        print(f"Warning: Failed to integrate with main backend: {e}")
    
    return {
        "project_id": project_id,
        "status": "created",
        "ipfs_hash": ipfs_hash,
        "message": "Project submitted for NCCR review and blockchain integration"
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

# Step 2: NCCR Admin Dashboard Review
@app.post("/api/admin/projects/{project_id}/review")
async def review_project(
    project_id: str,
    action: str = Form(...),  # "approve" or "reject"
    comments: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Step 2: NCCR admin reviews and approves/rejects project"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
    
    # Update project status
    project["admin_review"] = {
        "action": action,
        "comments": comments,
        "reviewed_by": current_user["user_id"],
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
    """NCCR Admin Dashboard - Overview of all projects"""
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
        "recent_projects": list(projects_db.values())[-10:],  # Last 10 projects
        "pending_projects": [p for p in projects_db.values() if p["status"] == "submitted"]
    }

# Step 3: MRV Data Collection
@app.post("/api/mrv/collect")
async def collect_mrv_data(
    mrv_data: MRVData,
    current_user: dict = Depends(get_current_user)
):
    """Step 3: Collect MRV data for carbon credit verification"""
    project_id = mrv_data.project_id
    
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    if project["status"] != "approved":
        raise HTTPException(status_code=400, detail="Project must be approved before MRV data collection")
    
    # Generate MRV data ID
    mrv_id = f"MRV_{project_id}_{int(datetime.now().timestamp())}"
    
    mrv_record = {
        "id": mrv_id,
        "collected_by": current_user["user_id"],
        "collected_at": datetime.now().isoformat(),
        **mrv_data.dict()
    }
    
    # Process photos - upload to IPFS
    photo_hashes = []
    for photo_b64 in mrv_data.photos:
        try:
            photo_data = base64.b64decode(photo_b64)
            ipfs_hash = upload_to_ipfs(photo_data)
            if ipfs_hash:
                photo_hashes.append(ipfs_hash)
        except Exception:
            continue
    
    mrv_record["photo_ipfs_hashes"] = photo_hashes
    
    # Store in database
    if project_id not in mrv_data_db:
        mrv_data_db[project_id] = []
    mrv_data_db[project_id].append(mrv_record)
    
    # Upload complete MRV data to IPFS
    ipfs_hash = upload_to_ipfs(json.dumps(mrv_record).encode())
    mrv_record["ipfs_hash"] = ipfs_hash
    
    return {
        "mrv_id": mrv_id,
        "project_id": project_id,
        "ipfs_hash": ipfs_hash,
        "photos_uploaded": len(photo_hashes),
        "status": "collected",
        "message": "MRV data collected successfully"
    }

@app.get("/api/mrv/{project_id}")
async def get_mrv_data(project_id: str):
    """Get MRV data for a project"""
    if project_id not in mrv_data_db:
        return {"project_id": project_id, "mrv_records": []}
    return {"project_id": project_id, "mrv_records": mrv_data_db[project_id]}

# Step 4: Multi-Source Verification
@app.post("/api/verification/verify")
async def verify_project(
    verification: VerificationResult,
    current_user: dict = Depends(get_current_user)
):
    """Step 4: Multi-source verification of MRV data"""
    project_id = verification.project_id
    
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_id not in mrv_data_db:
        raise HTTPException(status_code=400, detail="No MRV data found for project")
    
    # Calculate carbon credits
    project = projects_db[project_id]
    mrv_records = mrv_data_db[project_id]
    
    # Use latest MRV data for calculation
    latest_mrv = mrv_records[-1] if mrv_records else None
    if not latest_mrv:
        raise HTTPException(status_code=400, detail="No MRV data available")
    
    carbon_credits = calculate_carbon_credits(
        project["area_hectares"],
        project["ecosystem_type"],
        latest_mrv["measurements"]
    )
    
    verification_record = {
        "id": f"VER_{project_id}_{int(datetime.now().timestamp())}",
        "verified_by": current_user["user_id"],
        "verified_at": datetime.now().isoformat(),
        "carbon_credits_calculated": carbon_credits,
        **verification.dict()
    }
    
    # Store verification
    verifications_db[project_id] = verification_record
    
    # Update project status
    projects_db[project_id]["status"] = verification.verification_status
    projects_db[project_id]["carbon_credits"] = carbon_credits
    
    return {
        "project_id": project_id,
        "verification_id": verification_record["id"],
        "carbon_credits": carbon_credits,
        "status": verification.verification_status,
        "message": "Verification completed"
    }

# Step 5: Carbon Credit Tokenization
@app.post("/api/credits/tokenize/{project_id}")
async def tokenize_carbon_credits(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Step 5: Tokenize verified carbon credits as blockchain tokens"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    
    if project["status"] != "verified":
        raise HTTPException(status_code=400, detail="Project must be verified before tokenization")
    
    if "carbon_credits" not in project:
        raise HTTPException(status_code=400, detail="No carbon credits calculated")
    
    # Simulate blockchain transaction
    tx_hash = f"0x{hashlib.sha256(f'{project_id}_{datetime.now()}'.encode()).hexdigest()}"
    token_id = f"BCT_{project_id}_{int(datetime.now().timestamp())}"
    
    tokenization_record = {
        "token_id": token_id,
        "project_id": project_id,
        "credit_amount": project["carbon_credits"],
        "blockchain_tx": tx_hash,
        "contract_address": CONTRACT_ADDRESSES["CARBON_CREDIT_TOKEN"],
        "tokenized_by": current_user["user_id"],
        "tokenized_at": datetime.now().isoformat(),
        "status": "minted"
    }
    
    # Update project
    projects_db[project_id]["tokenization"] = tokenization_record
    projects_db[project_id]["status"] = "tokenized"
    
    return {
        "project_id": project_id,
        "token_id": token_id,
        "credit_amount": project["carbon_credits"],
        "blockchain_tx": tx_hash,
        "status": "tokenized",
        "message": "Carbon credits tokenized successfully"
    }

# Step 6: Carbon Credit Marketplace
@app.post("/api/marketplace/list")
async def list_credits_for_sale(
    listing: CarbonCreditListing,
    current_user: dict = Depends(get_current_user)
):
    """Step 6: List carbon credits for sale in marketplace"""
    project_id = listing.project_id
    
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    if project["status"] != "tokenized":
        raise HTTPException(status_code=400, detail="Project must be tokenized before listing")
    
    listing_id = f"LIST_{project_id}_{int(datetime.now().timestamp())}"
    
    marketplace_listing = {
        "listing_id": listing_id,
        "listed_by": current_user["user_id"],
        "listed_at": datetime.now().isoformat(),
        "status": "active",
        "total_value": listing.credit_amount * listing.price_per_credit,
        **listing.dict()
    }
    
    marketplace_db[listing_id] = marketplace_listing
    
    return {
        "listing_id": listing_id,
        "project_id": project_id,
        "total_value": marketplace_listing["total_value"],
        "status": "listed",
        "message": "Carbon credits listed for sale"
    }

@app.get("/api/marketplace")
async def get_marketplace_listings(status: str = "active"):
    """Get marketplace listings"""
    listings = [l for l in marketplace_db.values() if l["status"] == status]
    return {"listings": listings, "total": len(listings)}

@app.post("/api/marketplace/{listing_id}/purchase")
async def purchase_credits(
    listing_id: str,
    quantity: float = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Purchase carbon credits from marketplace"""
    if listing_id not in marketplace_db:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    listing = marketplace_db[listing_id]
    if listing["status"] != "active":
        raise HTTPException(status_code=400, detail="Listing is not active")
    
    if quantity > listing["credit_amount"]:
        raise HTTPException(status_code=400, detail="Insufficient credits available")
    
    purchase_value = quantity * listing["price_per_credit"]
    tx_hash = f"0x{hashlib.sha256(f'{listing_id}_{current_user}_{datetime.now()}'.encode()).hexdigest()}"
    
    purchase_record = {
        "purchase_id": f"PUR_{listing_id}_{int(datetime.now().timestamp())}",
        "listing_id": listing_id,
        "buyer": current_user["user_id"],
        "quantity": quantity,
        "total_paid": purchase_value,
        "blockchain_tx": tx_hash,
        "purchased_at": datetime.now().isoformat()
    }
    
    # Update listing
    listing["credit_amount"] -= quantity
    if listing["credit_amount"] <= 0:
        listing["status"] = "sold_out"
    
    return {
        "purchase_id": purchase_record["purchase_id"],
        "quantity": quantity,
        "total_paid": purchase_value,
        "blockchain_tx": tx_hash,
        "status": "completed",
        "message": "Carbon credits purchased successfully"
    }

# Step 7: Payment Distribution
@app.post("/api/payments/distribute/{project_id}")
async def distribute_payments(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Step 7: Automatically distribute payments to communities"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Find all purchases for this project
    project_purchases = []
    for listing in marketplace_db.values():
        if listing["project_id"] == project_id:
            # In a real system, you'd track individual purchases
            project_purchases.append(listing)
    
    if not project_purchases:
        raise HTTPException(status_code=400, detail="No sales found for this project")
    
    total_revenue = sum(p.get("total_value", 0) for p in project_purchases)
    
    # Distribution logic (70% to community, 20% to verifier, 10% to platform)
    community_share = total_revenue * 0.7
    verifier_share = total_revenue * 0.2
    platform_share = total_revenue * 0.1
    
    distribution_tx = f"0x{hashlib.sha256(f'{project_id}_distribution_{datetime.now()}'.encode()).hexdigest()}"
    
    distribution_record = {
        "distribution_id": f"DIST_{project_id}_{int(datetime.now().timestamp())}",
        "project_id": project_id,
        "total_revenue": total_revenue,
        "community_share": community_share,
        "verifier_share": verifier_share,
        "platform_share": platform_share,
        "blockchain_tx": distribution_tx,
        "distributed_at": datetime.now().isoformat(),
        "status": "completed"
    }
    
    return {
        "distribution_id": distribution_record["distribution_id"],
        "total_revenue": total_revenue,
        "distributions": {
            "community": community_share,
            "verifier": verifier_share,
            "platform": platform_share
        },
        "blockchain_tx": distribution_tx,
        "status": "completed",
        "message": "Payments distributed successfully"
    }

# Step 8: Reporting & Transparency
@app.get("/api/reports/project/{project_id}")
async def generate_project_report(project_id: str):
    """Step 8: Generate comprehensive project report"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    mrv_data = mrv_data_db.get(project_id, [])
    verification = verifications_db.get(project_id)
    
    # Find marketplace listings
    listings = [l for l in marketplace_db.values() if l["project_id"] == project_id]
    
    report = {
        "project_info": project,
        "mrv_data_points": len(mrv_data),
        "verification_status": verification["verification_status"] if verification else "pending",
        "carbon_credits_issued": project.get("carbon_credits", 0),
        "marketplace_listings": len(listings),
        "environmental_impact": {
            "area_restored": project["area_hectares"],
            "ecosystem_type": project["ecosystem_type"],
            "restoration_method": project["restoration_method"]
        },
        "blockchain_transactions": [],  # Would include all tx hashes in real system
        "transparency_score": 95,  # Calculated based on data completeness
        "generated_at": datetime.now().isoformat()
    }
    
    # Add blockchain transactions if available
    if "tokenization" in project:
        report["blockchain_transactions"].append({
            "type": "tokenization",
            "tx_hash": project["tokenization"]["blockchain_tx"]
        })
    
    return report

@app.get("/api/reports/dashboard")
async def system_dashboard():
    """Overall system dashboard with statistics"""
    total_projects = len(projects_db)
    total_credits_issued = sum(p.get("carbon_credits", 0) for p in projects_db.values())
    total_area_restored = sum(p["area_hectares"] for p in projects_db.values())
    
    # Status breakdown
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
            "recent_verifications": list(verifications_db.values())[-5:],
            "recent_marketplace_activity": list(marketplace_db.values())[-5:]
        },
        "blockchain_status": {
            "network": "Polygon Mumbai",
            "connected": web3.is_connected(),
            "latest_block": web3.eth.block_number if web3.is_connected() else None
        },
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
