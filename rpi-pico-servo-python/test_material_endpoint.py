#!/usr/bin/env python3
"""
Test script for the new material endpoint
Tests all material types: plastic, glass, pet, organic
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_endpoint():
    """Test the material endpoint with all material types"""
    
    materials = ["plastic", "glass", "pet", "organic"]
    expected_positions = {
        "plastic": {"vertical": -90, "horizontal": -20},
        "glass": {"vertical": -90, "horizontal": 20},
        "pet": {"vertical": 90, "horizontal": -20},
        "organic": {"vertical": 90, "horizontal": 20}
    }
    
    print("Testing Material Endpoint")
    print("=" * 40)
    
    # Test API health first
    try:
        response = requests.get(f"{API_BASE}/health")
        health_data = response.json()
        print(f"API Health: {health_data['status']}")
        print(f"Database: {health_data['database']}")
        print(f"Pico Connected: {health_data['pico_connected']}")
        print()
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Test each material type
    for material in materials:
        print(f"Testing material: {material.upper()}")
        print(f"Expected positions: {expected_positions[material]}")
        
        try:
            response = requests.post(f"{API_BASE}/api/servo/material/{material}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Success! Movement ID: {data['id']}")
                print(f"  Material type: {data.get('material_type', 'N/A')}")
                print(f"  Vertical angle: {data.get('vertical_angle', 'N/A')}")
                print(f"  Horizontal angle: {data.get('horizontal_angle', 'N/A')}")
                print(f"  Command type: {data.get('command_type', 'N/A')}")
                print(f"  Response time: {data.get('response_time_ms', 'N/A')} ms")
                print(f"  Success: {data['success']}")
            else:
                print(f"  Error! Status: {response.status_code}")
                print(f"  Message: {response.text}")
                
        except Exception as e:
            print(f"  Request failed: {e}")
        
        print("-" * 30)
        time.sleep(1)  # Small delay between tests
    
    # Test invalid material
    print("Testing invalid material: 'metal'")
    try:
        response = requests.post(f"{API_BASE}/api/servo/material/metal")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text}")
    except Exception as e:
        print(f"  Request failed: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_endpoint()
