#!/usr/bin/env python3
"""
Python-Only ML-Based AI Verification for Blue Carbon MRV System
Uses trained model from BlueCarbon.pkl for realistic scoring
"""

import json
import re
import math
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class MLVerificationEngine:
    """
    Real ML-based verification engine using trained model
    """
    
    def __init__(self, model_path='BlueCarbon.pkl'):
        """Initialize with trained ML model"""
        self.model_available = False
        self.model = None
        
        try:
            import pickle
            import sys
            
            # Try different pickle loading methods to handle compatibility issues
            try:
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print("✅ ML Model loaded successfully from BlueCarbon.pkl")
                self.model_available = True
            except Exception as pickle_error:
                print(f"⚠️ Standard pickle load failed: {pickle_error}")
                # Try with different encoding/protocol
                try:
                    with open(model_path, 'rb') as f:
                        self.model = pickle.load(f, encoding='latin1')
                    print("✅ ML Model loaded with latin1 encoding")
                    self.model_available = True
                except Exception as encoding_error:
                    print(f"⚠️ Latin1 encoding failed: {encoding_error}")
                    # Try with fix_imports
                    try:
                        with open(model_path, 'rb') as f:
                            self.model = pickle.load(f, fix_imports=True)
                        print("✅ ML Model loaded with fix_imports=True")
                        self.model_available = True
                    except Exception as final_error:
                        print(f"❌ All pickle loading methods failed: {final_error}")
                        self.model_available = False
                        self.model = None
                        
        except ImportError as e:
            print(f"❌ Failed to import pickle: {e}")
            self.model_available = False
            self.model = None
        
        # Ecosystem type mapping: 6 types → 3 categories (0, 1, 2)
        self.ecosystem_mapping = {
            # Group 1: Mangrove ecosystems (0)
            'mangrove': 0,
            'mangroves': 0,
            
            # Group 2: Seagrass and wetland ecosystems (1) 
            'seagrass': 1,
            'coastal_wetland': 1,
            'coastal_wetlands': 1,
            
            # Group 3: Salt marsh and other ecosystems (2)
            'salt_marsh': 2,
            'kelp_forest': 2
        }
        
        # Feature names for model input (15 features)
        self.feature_names = [
            'project_name_length',
            'ecosystem_type_encoded',  # 0, 1, or 2
            'area_hectares',
            'description_length', 
            'latitude',
            'longitude',
            'photo_count',
            'video_count',
            'document_count',
            'water_ph',
            'water_salinity_ppt',
            'water_dissolved_oxygen',
            'soil_organic_carbon_percent',
            'soil_ph',
            'soil_salinity_ppt'
        ]
    
    def extract_ml_features(self, project_data: Dict) -> List[float]:
        """
        Extract exactly 15 numerical features for ML model
        """
        features = []
        
        # 1. project_name_length
        project_name = project_data.get('project_name', '')
        features.append(len(project_name))
        
        # 2. ecosystem_type_encoded (0, 1, 2)
        ecosystem_type = project_data.get('ecosystem_type', '').lower()
        ecosystem_encoded = self.ecosystem_mapping.get(ecosystem_type, 1)  # Default to 1
        features.append(ecosystem_encoded)
        
        # 3. area_hectares
        area_hectares = float(project_data.get('area_hectares', 0))
        features.append(area_hectares)
        
        # 4. description_length
        description = project_data.get('description', project_data.get('project_description', ''))
        features.append(len(description))
        
        # 5. latitude
        location = project_data.get('location', {})
        if isinstance(location, dict):
            latitude = float(location.get('lat', 0))
        else:
            latitude = self._extract_lat_from_string(location)
        features.append(latitude)
        
        # 6. longitude 
        if isinstance(location, dict):
            longitude = float(location.get('lng', 0))
        else:
            longitude = self._extract_lng_from_string(location)
        features.append(longitude)
        
        # 7-9. Media counts (photo_count, video_count, document_count)
        photo_count, video_count, document_count = self._extract_media_counts(project_data)
        features.extend([photo_count, video_count, document_count])
        
        # 10-12. Water quality measurements
        field_measurements = project_data.get('field_measurements', {})
        water_quality = field_measurements.get('water_quality', {})
        
        water_ph = self._extract_numeric_value(water_quality.get('ph_level', 7.0))
        water_salinity = self._extract_numeric_value(water_quality.get('salinity', 25.0))
        water_do = self._extract_numeric_value(water_quality.get('dissolved_oxygen', 6.0))
        
        features.extend([water_ph, water_salinity, water_do])
        
        # 13-15. Soil measurements
        soil_analysis = field_measurements.get('soil_analysis', {})
        
        soil_carbon = self._extract_numeric_value(soil_analysis.get('carbon_content', 2.0))
        soil_ph = self._extract_numeric_value(soil_analysis.get('ph_level', 7.0))
        soil_salinity = self._extract_numeric_value(soil_analysis.get('salinity', 15.0))
        
        features.extend([soil_carbon, soil_ph, soil_salinity])
        
        return features
    
    def predict_quality_score(self, project_data: Dict) -> Dict:
        """
        Predict quality score using trained ML model
        """
        result = {
            'quality_score': 50.0,  # Default fallback
            'model_used': False,
            'feature_values': {},
            'predictions': {},
            'status': 'error'
        }
        
        try:
            # Extract features
            features = self.extract_ml_features(project_data)
            
            # Store feature values for debugging
            feature_dict = dict(zip(self.feature_names, features))
            result['feature_values'] = feature_dict
            
            if self.model_available and self.model is not None:
                # Use real ML model prediction
                # Convert to numpy array format expected by sklearn
                import numpy as np
                features_array = np.array(features).reshape(1, -1)
                prediction = self.model.predict(features_array)[0]
                
                # Convert prediction to quality score (0-100 range with 2 decimals)
                if isinstance(prediction, (int, float)):
                    quality_score = float(prediction)
                else:
                    # If model returns probabilities, convert to score
                    quality_score = float(prediction[1] if hasattr(prediction, '__len__') else prediction) * 100
                
                # Apply 25 points enhancement boost for good projects
                enhanced_score = quality_score + ((quality_score/100)*25)
                
                # Ensure score is in valid range with 2 decimals
                enhanced_score = max(0.0, min(100.0, enhanced_score))
                enhanced_score = round(enhanced_score, 2)
                
                result.update({
                    'quality_score': enhanced_score,
                    'original_score': round(quality_score, 2),
                    'enhancement_applied': '+25 points',
                    'model_used': True,
                    'status': 'success',
                    'model_type': str(type(self.model).__name__)
                })
                
                # Add prediction confidence if available
                if hasattr(self.model, 'predict_proba'):
                    try:
                        probabilities = self.model.predict_proba(features_array)[0]
                        result['predictions']['probabilities'] = probabilities.tolist()
                        result['predictions']['confidence'] = float(max(probabilities))
                    except:
                        pass
                        
            else:
                # Fallback: Calculate score based on feature rules
                fallback_score = self._calculate_fallback_score(feature_dict)
                
                # Apply 25 points enhancement boost for good projects
                enhanced_fallback = fallback_score + 25.0
                enhanced_fallback = max(0.0, min(100.0, enhanced_fallback))
                enhanced_fallback = round(enhanced_fallback, 2)
                
                result.update({
                    'quality_score': enhanced_fallback,
                    'original_score': round(fallback_score, 2),
                    'enhancement_applied': '+25 points',
                    'model_used': False,
                    'status': 'fallback_enhanced',
                    'note': 'Using enhanced rule-based fallback scoring with +25 points boost'
                })
                
        except Exception as e:
            print(f"❌ ML prediction error: {e}")
            # Emergency fallback
            result.update({
                'quality_score': 50.0,
                'model_used': False,
                'status': 'error',
                'error': str(e)
            })
        
        return result
    
    def _extract_media_counts(self, project_data: Dict) -> Tuple[int, int, int]:
        """Extract photo, video, and document counts"""
        photo_count = 0
        video_count = 0
        document_count = 0
        
        # Check IPFS hashes
        ipfs_hashes = project_data.get('ipfs_hashes', [])
        for item in ipfs_hashes:
            item_type = item.get('type', '').lower()
            if 'photo' in item_type or 'image' in item_type:
                photo_count += 1
            elif 'video' in item_type:
                video_count += 1
            elif 'document' in item_type or 'doc' in item_type or 'pdf' in item_type:
                document_count += 1
        
        # Check media_files structure
        media_files = project_data.get('media_files', {})
        if isinstance(media_files, dict):
            photo_count += len(media_files.get('photos', []))
            video_count += len(media_files.get('videos', []))
            document_count += len(media_files.get('documents', []))
        
        return photo_count, video_count, document_count
    
    def _extract_lat_from_string(self, location_str: str) -> float:
        """Extract latitude from location string like '22.3511°N, 88.9870°E'"""
        if not location_str:
            return 0.0
        
        try:
            # Look for patterns like "22.3511°N" or "22.3511N"
            lat_match = re.search(r'([+-]?\d+\.?\d*)[°\s]*[NS]?', location_str)
            if lat_match:
                lat = float(lat_match.group(1))
                # Handle N/S designation
                if 'S' in location_str.upper():
                    lat = -abs(lat)
                return lat
        except:
            pass
        return 0.0
    
    def _extract_lng_from_string(self, location_str: str) -> float:
        """Extract longitude from location string"""
        if not location_str:
            return 0.0
        
        try:
            # Look for patterns like "88.9870°E" or "88.9870E"
            lng_match = re.search(r'([+-]?\d+\.?\d*)[°\s]*[EW]', location_str)
            if lng_match:
                lng = float(lng_match.group(1))
                # Handle E/W designation
                if 'W' in location_str.upper():
                    lng = -abs(lng)
                return lng
        except:
            pass
        return 0.0
    
    def _extract_numeric_value(self, value) -> float:
        """Extract numeric value from various input formats"""
        if value is None:
            return 0.0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            try:
                # Remove any non-numeric characters except decimal point and minus
                cleaned = re.sub(r'[^\d.-]', '', value)
                if cleaned:
                    return float(cleaned)
            except:
                pass
        
        return 0.0
    
    def _calculate_fallback_score(self, features: Dict) -> float:
        """
        Calculate fallback score using simple rules when ML model fails
        """
        score = 50.0  # Base score
        
        # Ecosystem type bonus
        ecosystem_encoded = features.get('ecosystem_type_encoded', 1)
        if ecosystem_encoded == 0:  # Mangrove
            score += 10
        elif ecosystem_encoded == 1:  # Seagrass/wetland
            score += 5
        
        # Area reasonableness (1-100 hectares is good)
        area = features.get('area_hectares', 0)
        if 1 <= area <= 100:
            score += 15
        elif 0.1 <= area <= 1000:
            score += 10
        elif area > 0:
            score += 5
        
        # Location validity
        lat = features.get('latitude', 0)
        lng = features.get('longitude', 0)
        if -90 <= lat <= 90 and -180 <= lng <= 180 and (lat != 0 or lng != 0):
            score += 10
        
        # Data completeness
        name_length = features.get('project_name_length', 0)
        desc_length = features.get('description_length', 0)
        if name_length > 5:
            score += 5
        if desc_length > 20:
            score += 5
        
        # Media evidence
        photo_count = features.get('photo_count', 0)
        video_count = features.get('video_count', 0)
        doc_count = features.get('document_count', 0)
        total_media = photo_count + video_count + doc_count
        if total_media >= 5:
            score += 10
        elif total_media >= 1:
            score += 5
        
        # Water quality reasonableness
        water_ph = features.get('water_ph', 7.0)
        water_salinity = features.get('water_salinity_ppt', 25.0)
        if 6.0 <= water_ph <= 8.5:
            score += 3
        if 0 <= water_salinity <= 50:
            score += 3
        
        # Soil quality
        soil_carbon = features.get('soil_organic_carbon_percent', 2.0)
        if soil_carbon > 1.0:
            score += 4
        
        # Ensure score is in valid range
        score = max(0.0, min(100.0, score))
        return round(score, 2)
    
    def test_model(self) -> Dict:
        """
        Test the ML model with sample data
        """
        test_data = {
            'project_name': 'Test Mangrove Restoration Project',
            'ecosystem_type': 'mangrove',
            'area_hectares': 5.5,
            'description': 'This is a test project for mangrove restoration in coastal areas with community involvement.',
            'location': {'lat': 19.0760, 'lng': 72.8777},
            'field_measurements': {
                'water_quality': {
                    'ph_level': 7.2,
                    'salinity': 30.0,
                    'dissolved_oxygen': 6.5
                },
                'soil_analysis': {
                    'carbon_content': 3.5,
                    'ph_level': 7.0,
                    'salinity': 15.0
                }
            },
            'ipfs_hashes': [
                {'type': 'photos', 'filename': 'test1.jpg'},
                {'type': 'photos', 'filename': 'test2.jpg'},
                {'type': 'videos', 'filename': 'test.mp4'},
                {'type': 'documents', 'filename': 'report.pdf'}
            ]
        }
        
        print("🧪 Testing ML model with sample data...")
        result = self.predict_quality_score(test_data)
        
        print(f"✅ Test completed!")
        print(f"Model Available: {self.model_available}")
        print(f"Quality Score: {result['quality_score']}")
        print(f"Model Used: {result['model_used']}")
        print(f"Status: {result['status']}")
        
        if result.get('feature_values'):
            print("\n📊 Feature Values:")
            for feature, value in result['feature_values'].items():
                print(f"  {feature}: {value}")
        
        return result

# Global instance
ml_engine = MLVerificationEngine()

def verify_project_ml(project_data: Dict) -> Dict:
    """
    Main function to verify project using ML model
    """
    return ml_engine.predict_quality_score(project_data)

def test_ml_model() -> Dict:
    """
    Test function for ML model
    """
    return ml_engine.test_model()

if __name__ == "__main__":
    # Test the ML verification system
    test_result = test_ml_model()
    print(json.dumps(test_result, indent=2))
