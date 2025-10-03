#!/usr/bin/env python3
"""
Blue Carbon MRV System - AI/ML Verification Module
Implements automated verification of uploaded project data using AI/ML algorithms
"""

import json
import time
import random
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import base64

class AIVerificationEngine:
    """
    AI/ML Engine for verifying blue carbon project submissions
    """
    
    def __init__(self):
        self.verification_models = {
            'image_recognition': True,
            'fraud_detection': True,
            'data_validation': True,
            'location_verification': True,
            'temporal_analysis': True
        }
        
        self.confidence_thresholds = {
            'high': 0.85,
            'medium': 0.65,
            'low': 0.45
        }
        
        self.ecosystem_indicators = {
            'mangrove': ['green_vegetation', 'water_proximity', 'tidal_patterns'],
            'seagrass': ['underwater_vegetation', 'shallow_water', 'sediment_type'],
            'salt_marsh': ['salt_tolerant_plants', 'tidal_influence', 'mud_flats'],
            'coastal_wetland': ['wetland_vegetation', 'water_table', 'bird_activity']
        }
    
    def verify_project_submission(self, project_data: Dict) -> Dict:
        """
        Main verification function that processes all project data
        """
        verification_id = self._generate_verification_id()
        
        results = {
            'verification_id': verification_id,
            'project_id': project_data.get('project_name', '').replace(' ', '_').lower(),
            'timestamp': datetime.now().isoformat(),
            'overall_score': 0.0,
            'confidence_level': 'low',
            'status': 'pending',
            'detailed_analysis': {},
            'flags': [],
            'recommendations': []
        }
        
        # Run all verification modules
        media_analysis = self._verify_media_files(project_data.get('media_files', {}))
        location_analysis = self._verify_location_data(project_data.get('location', {}), project_data.get('gps_data', {}))
        field_analysis = self._verify_field_measurements(project_data.get('field_measurements', {}))
        ecosystem_analysis = self._verify_ecosystem_type(project_data.get('ecosystem_type', ''), media_analysis)
        temporal_analysis = self._verify_temporal_consistency(project_data)
        fraud_analysis = self._detect_potential_fraud(project_data, media_analysis)
        
        # Compile results
        results['detailed_analysis'] = {
            'media_verification': media_analysis,
            'location_verification': location_analysis,
            'field_measurements': field_analysis,
            'ecosystem_verification': ecosystem_analysis,
            'temporal_analysis': temporal_analysis,
            'fraud_detection': fraud_analysis
        }
        
        # Calculate overall score
        scores = [
            media_analysis['score'],
            location_analysis['score'],
            field_analysis['score'],
            ecosystem_analysis['score'],
            temporal_analysis['score'],
            fraud_analysis['score']
        ]
        results['overall_score'] = sum(scores) / len(scores)
        
        # Determine confidence level and status
        if results['overall_score'] >= self.confidence_thresholds['high']:
            results['confidence_level'] = 'high'
            results['status'] = 'approved'
        elif results['overall_score'] >= self.confidence_thresholds['medium']:
            results['confidence_level'] = 'medium'
            results['status'] = 'requires_review'
        else:
            results['confidence_level'] = 'low'
            results['status'] = 'flagged'
        
        # Collect all flags and recommendations
        for analysis in results['detailed_analysis'].values():
            if 'flags' in analysis:
                results['flags'].extend(analysis['flags'])
            if 'recommendations' in analysis:
                results['recommendations'].extend(analysis['recommendations'])
        
        return results
    
    def _verify_media_files(self, media_files: Dict) -> Dict:
        """
        Verify uploaded photos, videos, and audio files
        """
        analysis = {
            'score': 0.0,
            'verified_files': 0,
            'total_files': 0,
            'flags': [],
            'recommendations': [],
            'details': {}
        }
        
        for media_type, files in media_files.items():
            analysis['total_files'] += len(files)
            type_analysis = {
                'verified': 0,
                'suspicious': 0,
                'metadata_score': 0.0,
                'quality_score': 0.0,
                'authenticity_score': 0.0
            }
            
            for file_data in files:
                # Simulate AI analysis
                file_analysis = self._analyze_single_file(file_data, media_type)
                
                if file_analysis['authentic']:
                    type_analysis['verified'] += 1
                    analysis['verified_files'] += 1
                else:
                    type_analysis['suspicious'] += 1
                    analysis['flags'].append(f"Suspicious {media_type}: {file_data.get('name', 'unknown')}")
                
                type_analysis['metadata_score'] += file_analysis['metadata_score']
                type_analysis['quality_score'] += file_analysis['quality_score']
                type_analysis['authenticity_score'] += file_analysis['authenticity_score']
            
            if len(files) > 0:
                type_analysis['metadata_score'] /= len(files)
                type_analysis['quality_score'] /= len(files)
                type_analysis['authenticity_score'] /= len(files)
            
            analysis['details'][media_type] = type_analysis
        
        # Calculate overall media score
        if analysis['total_files'] > 0:
            file_ratio = analysis['verified_files'] / analysis['total_files']
            avg_quality = sum(details['quality_score'] for details in analysis['details'].values()) / len(analysis['details']) if analysis['details'] else 0
            avg_authenticity = sum(details['authenticity_score'] for details in analysis['details'].values()) / len(analysis['details']) if analysis['details'] else 0
            
            analysis['score'] = (file_ratio * 0.4 + avg_quality * 0.3 + avg_authenticity * 0.3)
        else:
            analysis['score'] = 0.0
            analysis['flags'].append("No media files uploaded")
        
        # Add recommendations
        if analysis['score'] < 0.7:
            analysis['recommendations'].append("Upload more high-quality media evidence")
        if analysis['total_files'] < 5:
            analysis['recommendations'].append("Minimum 5 media files recommended for verification")
        
        return analysis
    
    def _analyze_single_file(self, file_data: Dict, media_type: str) -> Dict:
        """
        Analyze individual file for authenticity and quality
        """
        # Simulate AI analysis with realistic scoring
        base_score = random.uniform(0.6, 0.95)
        
        # Check for geo-tagging
        geo_bonus = 0.1 if file_data.get('location') else 0
        
        # Check timestamp consistency
        timestamp_bonus = 0.05 if file_data.get('timestamp') else 0
        
        # Simulate quality analysis based on file size and type
        size_score = min(file_data.get('size', 0) / (5 * 1024 * 1024), 1.0)  # Normalize to 5MB
        
        return {
            'authentic': base_score > 0.7,
            'metadata_score': min(base_score + geo_bonus + timestamp_bonus, 1.0),
            'quality_score': (base_score + size_score) / 2,
            'authenticity_score': base_score,
            'geo_tagged': bool(file_data.get('location')),
            'timestamp_valid': bool(file_data.get('timestamp'))
        }
    
    def _verify_location_data(self, location: Dict, gps_data: Dict) -> Dict:
        """
        Verify GPS coordinates and location consistency
        """
        analysis = {
            'score': 0.0,
            'flags': [],
            'recommendations': [],
            'coordinates_valid': False,
            'coastal_proximity': False,
            'waypoints_consistent': False
        }
        
        # Check basic coordinates
        lat = location.get('lat', 0)
        lng = location.get('lng', 0)
        
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            analysis['coordinates_valid'] = True
            base_score = 0.6
        else:
            analysis['flags'].append("Invalid GPS coordinates")
            return analysis
        
        # Check if location is coastal (simplified check for India)
        india_coastal_regions = [
            {'lat_min': 8.0, 'lat_max': 37.0, 'lng_min': 68.0, 'lng_max': 97.0}  # Approximate India bounds
        ]
        
        for region in india_coastal_regions:
            if (region['lat_min'] <= lat <= region['lat_max'] and 
                region['lng_min'] <= lng <= region['lng_max']):
                analysis['coastal_proximity'] = True
                base_score += 0.2
                break
        
        if not analysis['coastal_proximity']:
            analysis['flags'].append("Location not in known coastal region")
        
        # Check GPS waypoints consistency
        waypoints = gps_data.get('waypoints', [])
        if len(waypoints) >= 2:
            analysis['waypoints_consistent'] = self._check_waypoint_consistency(waypoints, location)
            if analysis['waypoints_consistent']:
                base_score += 0.2
            else:
                analysis['flags'].append("GPS waypoints inconsistent with project location")
        
        analysis['score'] = min(base_score, 1.0)
        
        if analysis['score'] < 0.6:
            analysis['recommendations'].append("Verify GPS coordinates and add more waypoints")
        
        return analysis
    
    def _check_waypoint_consistency(self, waypoints: List, main_location: Dict) -> bool:
        """
        Check if waypoints are consistent with main project location
        """
        main_lat = main_location.get('lat', 0)
        main_lng = main_location.get('lng', 0)
        
        for waypoint in waypoints:
            wp_lat = waypoint.get('lat', 0)
            wp_lng = waypoint.get('lng', 0)
            
            # Calculate simple distance (in degrees, simplified)
            distance = ((wp_lat - main_lat) ** 2 + (wp_lng - main_lng) ** 2) ** 0.5
            
            # If waypoint is more than ~5km away (rough approximation), flag as inconsistent
            if distance > 0.05:  # Roughly 5km in degrees
                return False
        
        return True
    
    def _verify_field_measurements(self, measurements: Dict) -> Dict:
        """
        Verify scientific field measurements for consistency
        """
        analysis = {
            'score': 0.0,
            'flags': [],
            'recommendations': [],
            'measurements_count': 0,
            'realistic_values': 0
        }
        
        validation_rules = {
            'water_quality': {
                'ph_level': (6.0, 8.5),
                'salinity': (0, 50),
                'temperature': (10, 40),
                'dissolved_oxygen': (0, 20)
            },
            'soil_analysis': {
                'carbon_content': (0, 15),
                'nitrogen_level': (0, 5),
                'phosphorus_level': (0, 100),
                'moisture_content': (0, 100)
            },
            'biodiversity': {
                'species_count': (1, 200),
                'vegetation_density': (0, 100)
            }
        }
        
        for category, fields in measurements.items():
            if category in validation_rules:
                for field, value in fields.items():
                    if value and field in validation_rules[category]:
                        analysis['measurements_count'] += 1
                        min_val, max_val = validation_rules[category][field]
                        
                        try:
                            num_value = float(value)
                            if min_val <= num_value <= max_val:
                                analysis['realistic_values'] += 1
                            else:
                                analysis['flags'].append(f"Unrealistic {field}: {value}")
                        except ValueError:
                            analysis['flags'].append(f"Invalid numeric value for {field}: {value}")
        
        # Calculate score
        if analysis['measurements_count'] > 0:
            analysis['score'] = analysis['realistic_values'] / analysis['measurements_count']
        else:
            analysis['score'] = 0.0
            analysis['recommendations'].append("Add field measurements for better verification")
        
        if analysis['measurements_count'] < 3:
            analysis['recommendations'].append("More field measurements recommended")
        
        return analysis
    
    def _verify_ecosystem_type(self, ecosystem_type: str, media_analysis: Dict) -> Dict:
        """
        Verify if ecosystem type matches visual evidence
        """
        analysis = {
            'score': 0.0,
            'flags': [],
            'recommendations': [],
            'ecosystem_indicators_found': []
        }
        
        if not ecosystem_type:
            analysis['flags'].append("No ecosystem type specified")
            return analysis
        
        # Simulate visual analysis of media for ecosystem indicators
        if ecosystem_type in self.ecosystem_indicators:
            indicators = self.ecosystem_indicators[ecosystem_type]
            found_indicators = 0
            
            # Simulate AI detection of ecosystem features in images
            for indicator in indicators:
                # Random detection with higher probability for realistic scenarios
                if random.random() > 0.3:  # 70% chance of detecting each indicator
                    found_indicators += 1
                    analysis['ecosystem_indicators_found'].append(indicator)
            
            analysis['score'] = found_indicators / len(indicators)
            
            if analysis['score'] < 0.5:
                analysis['flags'].append(f"Visual evidence doesn't strongly support {ecosystem_type} classification")
            
        else:
            analysis['flags'].append(f"Unknown ecosystem type: {ecosystem_type}")
        
        return analysis
    
    def _verify_temporal_consistency(self, project_data: Dict) -> Dict:
        """
        Check temporal consistency across all uploaded data
        """
        analysis = {
            'score': 0.0,
            'flags': [],
            'recommendations': [],
            'timestamp_spread': 0,
            'consistent_timeframe': True
        }
        
        timestamps = []
        
        # Collect timestamps from media files
        for media_type, files in project_data.get('media_files', {}).items():
            for file_data in files:
                if file_data.get('timestamp'):
                    timestamps.append(file_data['timestamp'])
        
        if len(timestamps) >= 2:
            # Parse timestamps and check spread
            try:
                parsed_times = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps]
                time_spread = (max(parsed_times) - min(parsed_times)).total_seconds()
                analysis['timestamp_spread'] = time_spread / 3600  # Convert to hours
                
                # Reasonable timeframe for data collection (within 30 days)
                if time_spread <= 30 * 24 * 3600:  # 30 days in seconds
                    analysis['score'] = 0.9
                elif time_spread <= 90 * 24 * 3600:  # 90 days
                    analysis['score'] = 0.7
                    analysis['recommendations'].append("Data collection spread over long period")
                else:
                    analysis['score'] = 0.4
                    analysis['flags'].append("Data collected over suspiciously long period")
                
            except Exception as e:
                analysis['flags'].append("Could not parse timestamps")
                analysis['score'] = 0.5
        else:
            analysis['score'] = 0.3
            analysis['recommendations'].append("Add more timestamped evidence")
        
        return analysis
    
    def _detect_potential_fraud(self, project_data: Dict, media_analysis: Dict) -> Dict:
        """
        Enhanced fraud detection algorithms with multiple indicators
        """
        analysis = {
            'score': 0.0,
            'flags': [],
            'recommendations': [],
            'fraud_indicators': [],
            'risk_level': 'low',
            'detailed_checks': {}
        }
        
        fraud_score = 1.0  # Start with no fraud detected
        
        # 1. Media authenticity check
        media_check = self._check_media_authenticity(project_data.get('media_files', {}), media_analysis)
        analysis['detailed_checks']['media_authenticity'] = media_check
        fraud_score *= media_check['score']
        
        # 2. Location consistency check
        location_check = self._check_location_consistency(project_data)
        analysis['detailed_checks']['location_consistency'] = location_check
        fraud_score *= location_check['score']
        
        # 3. Temporal pattern analysis
        temporal_check = self._check_temporal_patterns(project_data)
        analysis['detailed_checks']['temporal_patterns'] = temporal_check
        fraud_score *= temporal_check['score']
        
        # 4. Project scale realism check
        scale_check = self._check_project_scale_realism(project_data)
        analysis['detailed_checks']['scale_realism'] = scale_check
        fraud_score *= scale_check['score']
        
        # 5. Data quality consistency check
        quality_check = self._check_data_quality_consistency(project_data)
        analysis['detailed_checks']['data_quality'] = quality_check
        fraud_score *= quality_check['score']
        
        # 6. Advanced pattern recognition
        pattern_check = self._check_advanced_patterns(project_data)
        analysis['detailed_checks']['advanced_patterns'] = pattern_check
        fraud_score *= pattern_check['score']
        
        # Compile all fraud indicators
        for check in analysis['detailed_checks'].values():
            analysis['fraud_indicators'].extend(check.get('indicators', []))
            analysis['flags'].extend(check.get('flags', []))
        
        analysis['score'] = max(fraud_score, 0.0)
        
        # Enhanced risk level assessment
        if analysis['score'] < 0.2:
            analysis['risk_level'] = 'critical'
            analysis['flags'].append("CRITICAL: Multiple fraud indicators detected")
        elif analysis['score'] < 0.4:
            analysis['risk_level'] = 'high'
            analysis['flags'].append("HIGH: Significant fraud risk detected")
        elif analysis['score'] < 0.7:
            analysis['risk_level'] = 'medium'
            analysis['flags'].append("MEDIUM: Some fraud indicators present")
        else:
            analysis['risk_level'] = 'low'
        
        # Add specific recommendations
        if len(analysis['fraud_indicators']) > 5:
            analysis['recommendations'].append("Manual verification required due to multiple fraud indicators")
        if analysis['score'] < 0.5:
            analysis['recommendations'].append("Independent third-party verification recommended")
        
        return analysis
    
    def _check_media_authenticity(self, media_files: Dict, media_analysis: Dict) -> Dict:
        """
        Advanced media authenticity check
        """
        check = {
            'score': 1.0,
            'indicators': [],
            'flags': []
        }
        
        total_files = sum(len(files) for files in media_files.values())
        verified_files = media_analysis.get('verified_files', 0)
        
        if total_files == 0:
            check['score'] = 0.3
            check['indicators'].append("No media files provided")
            return check
        
        verification_ratio = verified_files / total_files
        
        # Check for suspiciously perfect verification rates (could indicate stock photos)
        if verification_ratio == 1.0 and total_files > 10:
            check['score'] *= 0.8
            check['indicators'].append("Suspiciously high media verification rate")
        
        # Check for low verification rates
        if verification_ratio < 0.5:
            check['score'] *= 0.6
            check['indicators'].append("Low media authenticity rate")
        
        # Check file size patterns (stock photos often have similar sizes)
        file_sizes = []
        for media_type, files in media_files.items():
            for file_data in files:
                if file_data.get('size'):
                    file_sizes.append(file_data['size'])
        
        if len(file_sizes) > 3:
            # Check for suspicious uniformity in file sizes
            avg_size = sum(file_sizes) / len(file_sizes)
            size_variance = sum((size - avg_size) ** 2 for size in file_sizes) / len(file_sizes)
            coefficient_of_variation = (size_variance ** 0.5) / avg_size if avg_size > 0 else 0
            
            if coefficient_of_variation < 0.1:  # Very low variance
                check['score'] *= 0.9
                check['indicators'].append("Suspiciously uniform file sizes")
        
        return check
    
    def _check_location_consistency(self, project_data: Dict) -> Dict:
        """
        Enhanced location consistency check
        """
        check = {
            'score': 1.0,
            'indicators': [],
            'flags': []
        }
        
        main_location = project_data.get('location', {})
        media_files = project_data.get('media_files', {})
        waypoints = project_data.get('gps_data', {}).get('waypoints', [])
        
        if not main_location.get('lat') or not main_location.get('lng'):
            check['score'] = 0.2
            check['indicators'].append("Missing main project location")
            return check
        
        main_lat = main_location['lat']
        main_lng = main_location['lng']
        
        # Check media file locations
        location_deviations = []
        for media_type, files in media_files.items():
            for file_data in files:
                file_location = file_data.get('location', {})
                if file_location.get('lat') and file_location.get('lng'):
                    distance = self._calculate_distance(
                        main_lat, main_lng,
                        file_location['lat'], file_location['lng']
                    )
                    location_deviations.append(distance)
        
        if location_deviations:
            avg_deviation = sum(location_deviations) / len(location_deviations)
            max_deviation = max(location_deviations)
            
            # Flag suspicious location patterns
            if max_deviation > 50:  # More than 50km away
                check['score'] *= 0.4
                check['indicators'].append(f"Media files from distant locations (max: {max_deviation:.1f}km)")
            elif avg_deviation > 10:  # Average more than 10km away
                check['score'] *= 0.7
                check['indicators'].append(f"Media files averaged far from project (avg: {avg_deviation:.1f}km)")
        
        # Check waypoint consistency
        if waypoints:
            waypoint_deviations = []
            for waypoint in waypoints:
                if waypoint.get('lat') and waypoint.get('lng'):
                    distance = self._calculate_distance(
                        main_lat, main_lng,
                        waypoint['lat'], waypoint['lng']
                    )
                    waypoint_deviations.append(distance)
            
            if waypoint_deviations and max(waypoint_deviations) > 20:
                check['score'] *= 0.8
                check['indicators'].append("GPS waypoints far from project location")
        
        return check
    
    def _check_temporal_patterns(self, project_data: Dict) -> Dict:
        """
        Advanced temporal pattern analysis
        """
        check = {
            'score': 1.0,
            'indicators': [],
            'flags': []
        }
        
        timestamps = []
        
        # Collect all timestamps
        for media_type, files in project_data.get('media_files', {}).items():
            for file_data in files:
                if file_data.get('timestamp'):
                    timestamps.append(file_data['timestamp'])
        
        waypoints = project_data.get('gps_data', {}).get('waypoints', [])
        for waypoint in waypoints:
            if waypoint.get('timestamp'):
                timestamps.append(waypoint['timestamp'])
        
        if len(timestamps) < 2:
            check['score'] = 0.6
            check['indicators'].append("Insufficient timestamp data")
            return check
        
        try:
            parsed_times = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps]
            parsed_times.sort()
            
            # Check for suspicious patterns
            intervals = []
            for i in range(1, len(parsed_times)):
                interval = (parsed_times[i] - parsed_times[i-1]).total_seconds()
                intervals.append(interval)
            
            # Check for too regular intervals (could indicate batch uploading)
            if len(intervals) > 5:
                avg_interval = sum(intervals) / len(intervals)
                regular_intervals = sum(1 for interval in intervals if abs(interval - avg_interval) < avg_interval * 0.1)
                
                if regular_intervals > len(intervals) * 0.8:
                    check['score'] *= 0.8
                    check['indicators'].append("Suspiciously regular timestamp intervals")
            
            # Check for all data collected in very short time
            total_span = (parsed_times[-1] - parsed_times[0]).total_seconds()
            if total_span < 300 and len(timestamps) > 10:  # Less than 5 minutes for >10 files
                check['score'] *= 0.6
                check['indicators'].append("All data collected in suspiciously short time")
            
            # Check for data collected outside reasonable hours
            night_uploads = sum(1 for t in parsed_times if t.hour < 6 or t.hour > 22)
            if night_uploads > len(parsed_times) * 0.5:
                check['score'] *= 0.9
                check['indicators'].append("Many files uploaded during unusual hours")
        
        except Exception:
            check['score'] = 0.5
            check['indicators'].append("Could not parse timestamp data")
        
        return check
    
    def _check_project_scale_realism(self, project_data: Dict) -> Dict:
        """
        Check if project scale claims are realistic
        """
        check = {
            'score': 1.0,
            'indicators': [],
            'flags': []
        }
        
        area = float(project_data.get('area_hectares', 0))
        ecosystem_type = project_data.get('ecosystem_type', '')
        community_members = int(project_data.get('community_members', 0))
        budget = float(project_data.get('estimated_budget', 0))
        
        # Check area claims
        if area <= 0:
            check['score'] *= 0.5
            check['indicators'].append("No area specified")
        elif area > 10000:  # Very large area
            check['score'] *= 0.3
            check['indicators'].append(f"Unrealistically large area claimed: {area} hectares")
        elif area > 1000:
            check['score'] *= 0.7
            check['indicators'].append(f"Very large area claimed: {area} hectares")
        
        # Check community scale vs area
        if area > 0 and community_members > 0:
            people_per_hectare = community_members / area
            if people_per_hectare > 100:  # Too many people per hectare
                check['score'] *= 0.6
                check['indicators'].append("Unrealistic community density")
            elif people_per_hectare < 0.01:  # Too few people for large area
                check['score'] *= 0.8
                check['indicators'].append("Very low community engagement for project size")
        
        # Check budget realism
        if budget > 0 and area > 0:
            cost_per_hectare = budget / area
            
            # Typical blue carbon restoration costs: $1000-$10000 per hectare
            if cost_per_hectare < 50000:  # Less than ₹50,000 per hectare
                check['score'] *= 0.7
                check['indicators'].append("Budget seems too low for claimed area")
            elif cost_per_hectare > 1000000:  # More than ₹10,00,000 per hectare
                check['score'] *= 0.6
                check['indicators'].append("Budget seems unrealistically high")
        
        return check
    
    def _check_data_quality_consistency(self, project_data: Dict) -> Dict:
        """
        Check for data quality consistency across all fields
        """
        check = {
            'score': 1.0,
            'indicators': [],
            'flags': []
        }
        
        # Check completeness
        required_fields = ['project_name', 'ecosystem_type', 'location', 'area_hectares']
        missing_fields = [field for field in required_fields if not project_data.get(field)]
        
        if missing_fields:
            check['score'] *= (1 - 0.1 * len(missing_fields))
            check['indicators'].append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Check description quality
        description = project_data.get('description', '')
        if len(description) < 50:
            check['score'] *= 0.9
            check['indicators'].append("Very brief project description")
        elif len(description) > 5000:
            check['score'] *= 0.95
            check['indicators'].append("Unusually long project description")
        
        # Check for copy-paste indicators in text fields
        text_fields = ['description', 'objectives', 'methodology']
        for field in text_fields:
            text = project_data.get(field, '')
            if text and self._check_text_authenticity(text):
                check['score'] *= 0.8
                check['indicators'].append(f"Potentially copy-pasted {field}")
        
        return check
    
    def _check_advanced_patterns(self, project_data: Dict) -> Dict:
        """
        Advanced pattern recognition for fraud detection
        """
        check = {
            'score': 1.0,
            'indicators': [],
            'flags': []
        }
        
        # Check for perfect values (too good to be true)
        measurements = project_data.get('field_measurements', {})
        perfect_values = 0
        total_measurements = 0
        
        for category, fields in measurements.items():
            for field, value in fields.items():
                if value:
                    total_measurements += 1
                    try:
                        num_value = float(value)
                        # Check if value is suspiciously perfect (ending in .0, .5, etc.)
                        if num_value == round(num_value) or num_value == round(num_value * 2) / 2:
                            perfect_values += 1
                    except ValueError:
                        pass
        
        if total_measurements > 5 and perfect_values > total_measurements * 0.8:
            check['score'] *= 0.8
            check['indicators'].append("Too many 'perfect' measurement values")
        
        # Check submission timing patterns
        current_time = datetime.now()
        submission_hour = current_time.hour
        
        # Flag submissions during unusual hours for field work
        if submission_hour < 6 or submission_hour > 22:
            check['score'] *= 0.95
            check['indicators'].append("Submission during unusual hours")
        
        # Check for data diversity
        media_types = len(project_data.get('media_files', {}))
        measurement_categories = len(measurements)
        
        diversity_score = (media_types + measurement_categories) / 10  # Normalize
        if diversity_score < 0.3:
            check['score'] *= 0.8
            check['indicators'].append("Low data diversity")
        
        return check
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate distance between two coordinates in kilometers
        """
        # Simplified distance calculation (Haversine formula approximation)
        lat_diff = abs(lat1 - lat2)
        lng_diff = abs(lng1 - lng2)
        
        # Rough conversion: 1 degree ≈ 111 km
        distance = ((lat_diff * 111) ** 2 + (lng_diff * 111) ** 2) ** 0.5
        return distance
    
    def _check_text_authenticity(self, text: str) -> bool:
        """
        Simple check for potentially copy-pasted text
        """
        # Check for repeated phrases
        words = text.lower().split()
        if len(words) < 10:
            return False
        
        # Check for repetitive patterns
        word_frequency = {}
        for word in words:
            word_frequency[word] = word_frequency.get(word, 0) + 1
        
        # Flag if too many repeated words
        repeated_words = sum(1 for count in word_frequency.values() if count > 3)
        return repeated_words > len(words) * 0.2
    
    def _generate_verification_id(self) -> str:
        """
        Generate unique verification ID
        """
        timestamp = str(int(time.time()))
        random_part = str(random.randint(1000, 9999))
        return f"VERIFY_{timestamp}_{random_part}"
    
    def get_verification_status(self, verification_id: str) -> Dict:
        """
        Get status of a verification process
        """
        # In a real implementation, this would query a database
        return {
            'verification_id': verification_id,
            'status': 'completed',
            'progress': 100,
            'estimated_completion': datetime.now().isoformat()
        }

# Global instance for use in API endpoints
ai_engine = AIVerificationEngine()

def verify_project(project_data: Dict) -> Dict:
    """
    Main function to verify a project submission
    """
    return ai_engine.verify_project_submission(project_data)

def get_verification_status(verification_id: str) -> Dict:
    """
    Get verification status by ID
    """
    return ai_engine.get_verification_status(verification_id)

if __name__ == "__main__":
    # Test the verification system
    test_project = {
        'project_name': 'Test Mangrove Project',
        'ecosystem_type': 'mangrove',
        'area_hectares': 10.5,
        'location': {'lat': 19.0760, 'lng': 72.8777},
        'media_files': {
            'photos': [
                {'name': 'test1.jpg', 'size': 2048576, 'location': {'lat': 19.0760, 'lng': 72.8777}, 'timestamp': datetime.now().isoformat()},
                {'name': 'test2.jpg', 'size': 1548576, 'location': {'lat': 19.0761, 'lng': 72.8778}, 'timestamp': datetime.now().isoformat()}
            ]
        },
        'field_measurements': {
            'water_quality': {'ph_level': '7.2', 'salinity': '35'},
            'soil_analysis': {'carbon_content': '3.5'}
        },
        'gps_data': {
            'waypoints': [
                {'lat': 19.0760, 'lng': 72.8777, 'timestamp': datetime.now().isoformat()},
                {'lat': 19.0761, 'lng': 72.8778, 'timestamp': datetime.now().isoformat()}
            ]
        }
    }
    
    result = verify_project(test_project)
    print(json.dumps(result, indent=2))
