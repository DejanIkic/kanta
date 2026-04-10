#!/usr/bin/env python3
"""
Comprehensive API test runner for RPi Pico Servo Control System
Tests all endpoints including material positioning, legacy endpoints, and status checks
"""

import requests
import json
import time
from typing import Dict, List, Any

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}")
        if details:
            print(f"       {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def test_root_endpoint(self) -> bool:
        """Test root endpoint"""
        try:
            response = requests.get(f"{self.base_url}/")
            success = response.status_code == 200
            data = response.json()
            
            details = f"Status: {response.status_code}"
            if success:
                details += f", Message: {data.get('message', 'N/A')}, Version: {data.get('version', 'N/A')}"
            
            self.log_test("Root Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_health_check(self) -> bool:
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health")
            success = response.status_code == 200
            data = response.json()
            
            details = f"Status: {response.status_code}"
            if success:
                details += f", System: {data.get('status', 'N/A')}, DB: {data.get('database', 'N/A')}, Pico: {data.get('pico_connected', 'N/A')}"
            
            self.log_test("Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_material_positioning(self) -> bool:
        """Test all material positioning endpoints"""
        materials = {
            "plastic": {"vertical": -90, "horizontal": -20},
            "glass": {"vertical": -90, "horizontal": 20},
            "pet": {"vertical": 90, "horizontal": -20},
            "organic": {"vertical": 90, "horizontal": 20}
        }
        
        all_success = True
        
        for material, expected_positions in materials.items():
            try:
                response = requests.post(f"{self.base_url}/api/servo/material/{material}")
                success = response.status_code == 200
                
                if success:
                    data = response.json()
                    v_angle = data.get('vertical_angle')
                    h_angle = data.get('horizontal_angle')
                    material_type = data.get('material_type')
                    command_type = data.get('command_type')
                    response_time = data.get('response_time_ms')
                    
                    # Validate response data
                    validations = []
                    if v_angle != expected_positions['vertical']:
                        validations.append(f"Vertical angle mismatch: expected {expected_positions['vertical']}, got {v_angle}")
                    if h_angle != expected_positions['horizontal']:
                        validations.append(f"Horizontal angle mismatch: expected {expected_positions['horizontal']}, got {h_angle}")
                    if material_type != material:
                        validations.append(f"Material type mismatch: expected {material}, got {material_type}")
                    if command_type != 'material':
                        validations.append(f"Command type mismatch: expected 'material', got {command_type}")
                    
                    details = f"V:{v_angle}°, H:{h_angle}°, Time:{response_time}ms"
                    if validations:
                        details += f", Errors: {', '.join(validations)}"
                        success = False
                else:
                    details = f"Status: {response.status_code}, Response: {response.text}"
                
                self.log_test(f"Material - {material.upper()}", success, details)
                if not success:
                    all_success = False
                    
            except Exception as e:
                self.log_test(f"Material - {material.upper()}", False, f"Exception: {str(e)}")
                all_success = False
        
        return all_success
    
    def test_invalid_material(self) -> bool:
        """Test invalid material rejection"""
        try:
            response = requests.post(f"{self.base_url}/api/servo/material/metal")
            success = response.status_code == 422
            
            details = f"Status: {response.status_code}"
            if success:
                details += ", Correctly rejected invalid material"
            else:
                details += f", Should have rejected with 422, got {response.status_code}"
            
            self.log_test("Invalid Material Rejection", success, details)
            return success
        except Exception as e:
            self.log_test("Invalid Material Rejection", False, f"Exception: {str(e)}")
            return False
    
    def test_legacy_endpoints(self) -> bool:
        """Test legacy endpoints for backward compatibility"""
        legacy_tests = [
            ("left", -20),
            ("right", 20)
        ]
        
        all_success = True
        
        for side, expected_angle in legacy_tests:
            try:
                response = requests.post(f"{self.base_url}/api/servo/{side}")
                success = response.status_code == 200
                
                if success:
                    data = response.json()
                    angle = data.get('angle')
                    command_type = data.get('command_type')
                    
                    validations = []
                    if angle != expected_angle:
                        validations.append(f"Angle mismatch: expected {expected_angle}, got {angle}")
                    if command_type != 'legacy':
                        validations.append(f"Command type mismatch: expected 'legacy', got {command_type}")
                    
                    details = f"Angle: {angle}°, Type: {command_type}"
                    if validations:
                        details += f", Errors: {', '.join(validations)}"
                        success = False
                else:
                    details = f"Status: {response.status_code}"
                
                self.log_test(f"Legacy - {side.upper()}", success, details)
                if not success:
                    all_success = False
                    
            except Exception as e:
                self.log_test(f"Legacy - {side.upper()}", False, f"Exception: {str(e)}")
                all_success = False
        
        return all_success
    
    def test_status_endpoints(self) -> bool:
        """Test status and history endpoints"""
        endpoints = [
            ("/api/servo/status", "Status"),
            ("/api/servo/history", "History"),
            ("/api/servo/history/5", "History (limit 5)")
        ]
        
        all_success = True
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                success = response.status_code == 200
                
                details = f"Status: {response.status_code}"
                if success:
                    data = response.json()
                    if name == "Status":
                        details += f", Connected: {data.get('connected', 'N/A')}, Movements: {data.get('total_movements', 'N/A')}"
                    elif name == "History":
                        details += f", Count: {data.get('total_count', 'N/A')}, Movements: {len(data.get('movements', []))}"
                
                self.log_test(name, success, details)
                if not success:
                    all_success = False
                    
            except Exception as e:
                self.log_test(name, False, f"Exception: {str(e)}")
                all_success = False
        
        return all_success
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all API tests"""
        print("=" * 60)
        print("RPi Pico Servo Control API - Comprehensive Test Suite")
        print("=" * 60)
        print()
        
        start_time = time.time()
        
        # Run all test categories
        self.test_root_endpoint()
        self.test_health_check()
        material_success = self.test_material_positioning()
        self.test_invalid_material()
        legacy_success = self.test_legacy_endpoints()
        status_success = self.test_status_endpoints()
        
        end_time = time.time()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Print summary
        print()
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {end_time - start_time:.2f}s")
        print()
        
        # Category summary
        print("CATEGORIES:")
        print(f"  Material Positioning: {'PASS' if material_success else 'FAIL'}")
        print(f"  Legacy Endpoints: {'PASS' if legacy_success else 'FAIL'}")
        print(f"  Status Endpoints: {'PASS' if status_success else 'FAIL'}")
        print()
        
        # Failed tests details
        if failed_tests > 0:
            print("FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        overall_success = failed_tests == 0
        print(f"OVERALL RESULT: {'PASS' if overall_success else 'FAIL'}")
        print("=" * 60)
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": success_rate,
            "duration": end_time - start_time,
            "overall_success": overall_success,
            "results": self.test_results
        }

if __name__ == "__main__":
    # Run tests
    tester = APITester()
    results = tester.run_all_tests()
    
    # Save results to file
    with open("api_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: api_test_results.json")
