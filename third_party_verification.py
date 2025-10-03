"""
3rd Party Verification System for Blue Carbon MRV
Handles NGO and Environmental Organization verification workflow
"""

import uuid
import datetime
from typing import Dict, List, Optional
import json

class ThirdPartyVerificationSystem:
    def __init__(self):
        # In production, this would be in a database
        self.verified_orgs = {
            "ngo_001": {
                "id": "ngo_001",
                "name": "Coastal Conservation India",
                "type": "Environmental NGO",
                "registration_number": "NGO/2020/001",
                "contact_email": "verify@coastalconservation.in",
                "password": "ngo123",
                "contact_phone": "+91-9876543210",
                "authorized_regions": ["West Bengal", "Odisha", "Tamil Nadu"],
                "specialization": ["mangrove", "coastal_wetlands"],
                "verification_count": 147,
                "success_rate": 94.2,
                "status": "active",
                "wallet_address": "0x742d35Cc6437C8532C3C6B5f0e98C3b2A98765F4",
                "created_at": "2024-01-15T10:30:00Z"
            },
            "ngo_002": {
                "id": "ngo_002", 
                "name": "Blue Ocean Foundation",
                "type": "Marine Research Organization",
                "registration_number": "RES/2019/045",
                "contact_email": "research@blueoceangfoundation.org",
                "password": "blue456",
                "contact_phone": "+91-8765432109",
                "authorized_regions": ["Gujarat", "Maharashtra", "Karnataka"],
                "specialization": ["seagrass", "marine_ecosystems"],
                "verification_count": 89,
                "success_rate": 96.8,
                "status": "active",
                "wallet_address": "0x123d45Cc6437C8532C3C6B5f0e98C3b2A98765F8",
                "created_at": "2024-02-20T14:15:00Z"
            },
            "ngo_003": {
                "id": "ngo_003",
                "name": "Mangrove Research Institute",
                "type": "Research Institute",
                "registration_number": "INST/2021/012",
                "contact_email": "field@mangroveresearch.ac.in",
                "password": "mangrove789",
                "contact_phone": "+91-7654321098",
                "authorized_regions": ["Andhra Pradesh", "Kerala", "Goa"],
                "specialization": ["mangrove", "saltmarsh", "biodiversity"],
                "verification_count": 203,
                "success_rate": 92.1,
                "status": "active",
                "wallet_address": "0x456d78Cc6437C8532C3C6B5f0e98C3b2A98765F9",
                "created_at": "2023-11-10T09:45:00Z"
            }
        }
        
        # Active verification assignments
        self.verification_assignments = {}
        
        # Verification reports
        self.verification_reports = {}

    def authenticate_third_party(self, org_id: str, email: str) -> Dict:
        """Authenticate 3rd party organization"""
        if org_id in self.verified_orgs:
            org = self.verified_orgs[org_id]
            if org["contact_email"] == email and org["status"] == "active":
                return {
                    "success": True,
                    "organization": org,
                    "auth_token": f"3P_{org_id}_{uuid.uuid4().hex[:8]}",
                    "permissions": ["verify_projects", "submit_reports", "upload_evidence"]
                }
        
        return {
            "success": False,
            "error": "Invalid credentials or inactive organization"
        }

    def authenticate_organization(self, email: str, password: str) -> Dict:
        """Authenticate organization by email and password"""
        for org_id, org in self.verified_orgs.items():
            if org["contact_email"] == email and org.get("password") == password and org["status"] == "active":
                return {
                    "success": True,
                    "organization": org,
                    "auth_token": f"3P_{org_id}_{uuid.uuid4().hex[:8]}",
                    "permissions": ["verify_projects", "submit_reports", "upload_evidence"]
                }
        
        return {
            "success": False,
            "error": "Invalid email or password"
        }

    def assign_project_for_verification(self, project_id: str, org_id: str) -> Dict:
        """Assign project to 3rd party for verification"""
        if org_id not in self.verified_orgs:
            return {"success": False, "error": "Organization not found"}
        
        assignment_id = f"ASSIGN_{uuid.uuid4().hex[:8]}"
        
        self.verification_assignments[assignment_id] = {
            "assignment_id": assignment_id,
            "project_id": project_id,
            "org_id": org_id,
            "status": "assigned",
            "assigned_at": datetime.datetime.now().isoformat(),
            "due_date": (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat(),
            "priority": "medium"
        }
        
        return {
            "success": True,
            "assignment_id": assignment_id,
            "message": f"Project {project_id} assigned to {self.verified_orgs[org_id]['name']}"
        }

    def submit_verification_report(self, assignment_id: str, report_data: Dict) -> Dict:
        """Submit 3rd party verification report"""
        if assignment_id not in self.verification_assignments:
            return {"success": False, "error": "Assignment not found"}
        
        assignment = self.verification_assignments[assignment_id]
        
        # Validate required fields
        required_fields = [
            "environmental_baseline", "biodiversity_assessment", 
            "community_impact", "technical_feasibility", "recommendation"
        ]
        
        missing_fields = [field for field in required_fields if field not in report_data]
        if missing_fields:
            return {
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }
        
        report_id = f"RPT_{uuid.uuid4().hex[:8]}"
        
        verification_report = {
            "report_id": report_id,
            "assignment_id": assignment_id,
            "project_id": assignment["project_id"],
            "org_id": assignment["org_id"],
            "submitted_at": datetime.datetime.now().isoformat(),
            "status": "submitted",
            
            # Environmental Assessment
            "environmental_baseline": report_data["environmental_baseline"],
            "biodiversity_assessment": report_data["biodiversity_assessment"],
            "water_quality_analysis": report_data.get("water_quality_analysis", {}),
            "ecosystem_health_score": report_data.get("ecosystem_health_score", 0),
            
            # Community Assessment  
            "community_impact": report_data["community_impact"],
            "stakeholder_engagement": report_data.get("stakeholder_engagement", {}),
            "local_employment_potential": report_data.get("local_employment_potential", 0),
            
            # Technical Assessment
            "technical_feasibility": report_data["technical_feasibility"],
            "restoration_methodology": report_data.get("restoration_methodology", ""),
            "monitoring_plan": report_data.get("monitoring_plan", ""),
            
            # Evidence Documentation
            "field_photos": report_data.get("field_photos", []),
            "gps_coordinates_verified": report_data.get("gps_coordinates_verified", False),
            "measurement_data": report_data.get("measurement_data", {}),
            
            # Final Assessment
            "overall_score": report_data.get("overall_score", 0),
            "recommendation": report_data["recommendation"],  # approve/reject/conditional
            "conditions": report_data.get("conditions", []),
            "risks_identified": report_data.get("risks_identified", []),
            "mitigation_suggestions": report_data.get("mitigation_suggestions", [])
        }
        
        self.verification_reports[report_id] = verification_report
        
        # Update assignment status
        self.verification_assignments[assignment_id]["status"] = "completed"
        self.verification_assignments[assignment_id]["completed_at"] = datetime.datetime.now().isoformat()
        
        return {
            "success": True,
            "report_id": report_id,
            "message": "Verification report submitted successfully",
            "overall_score": verification_report["overall_score"],
            "recommendation": verification_report["recommendation"]
        }

    def get_organization_dashboard(self, org_id: str) -> Dict:
        """Get dashboard data for 3rd party organization"""
        if org_id not in self.verified_orgs:
            return {"success": False, "error": "Organization not found"}
        
        org = self.verified_orgs[org_id]
        
        # Get assignments for this org
        pending_assignments = [
            a for a in self.verification_assignments.values() 
            if a["org_id"] == org_id and a["status"] == "assigned"
        ]
        
        completed_assignments = [
            a for a in self.verification_assignments.values()
            if a["org_id"] == org_id and a["status"] == "completed"
        ]
        
        # Get recent reports
        recent_reports = [
            r for r in self.verification_reports.values()
            if r["org_id"] == org_id
        ][-10:]  # Last 10 reports
        
        return {
            "success": True,
            "organization": org,
            "statistics": {
                "pending_verifications": len(pending_assignments),
                "completed_verifications": len(completed_assignments),
                "total_reports": len([r for r in self.verification_reports.values() if r["org_id"] == org_id]),
                "average_score": sum([r.get("overall_score", 0) for r in recent_reports]) / max(len(recent_reports), 1)
            },
            "pending_assignments": pending_assignments,
            "recent_reports": recent_reports
        }

    def get_project_verification_status(self, project_id: str) -> Dict:
        """Get verification status for a project"""
        
        # Find assignment for this project
        project_assignment = None
        for assignment in self.verification_assignments.values():
            if assignment["project_id"] == project_id:
                project_assignment = assignment
                break
        
        if not project_assignment:
            return {
                "status": "not_assigned",
                "message": "Project not yet assigned for 3rd party verification"
            }
        
        # Find verification report
        verification_report = None
        for report in self.verification_reports.values():
            if report["project_id"] == project_id:
                verification_report = report
                break
        
        if not verification_report:
            return {
                "status": "assigned",
                "assignment": project_assignment,
                "organization": self.verified_orgs.get(project_assignment["org_id"]),
                "message": "Project assigned for verification, awaiting report"
            }
        
        return {
            "status": "verified",
            "assignment": project_assignment,
            "report": verification_report,
            "organization": self.verified_orgs.get(project_assignment["org_id"]),
            "message": "3rd party verification completed"
        }

    def list_available_organizations(self) -> List[Dict]:
        """List all available 3rd party organizations"""
        return [
            {
                "id": org["id"],
                "name": org["name"],
                "type": org["type"],
                "specialization": org["specialization"],
                "authorized_regions": org["authorized_regions"],
                "verification_count": org["verification_count"],
                "success_rate": org["success_rate"],
                "status": org["status"]
            }
            for org in self.verified_orgs.values()
            if org["status"] == "active"
        ]

    def get_all_organizations(self) -> List[Dict]:
        """Get all organizations"""
        return list(self.verified_orgs.values())

    def get_project_reports(self, project_id: str) -> List[Dict]:
        """Get verification reports for a project"""
        reports = []
        for report in self.verification_reports.values():
            if report["project_id"] == project_id:
                reports.append(report)
        return reports

    def assign_project(self, org_id: str, project_id: str) -> Dict:
        """Assign project to organization (alternative method signature)"""
        return self.assign_project_for_verification(project_id, org_id)

# Global instance
third_party_system = ThirdPartyVerificationSystem()