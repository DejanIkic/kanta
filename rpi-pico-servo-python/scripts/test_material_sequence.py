#!/usr/bin/env python3
"""
Test script for material sequence with 10 iterations
Modified delays (divided by 4) and error checking
Autor: AI Assistant
"""

import requests
import time
import json
from datetime import datetime

# API endpoint
API_URL = "http://localhost:8000"

def test_material_sequence(material="plastic", iterations=10):
    """Test material sequence with multiple iterations"""
    print(f"=== Material Sequence Test ===")
    print(f"Material: {material}")
    print(f"Iterations: {iterations}")
    print(f"Modified delays (÷4): 0.125s, 0.5s, 0.5s")
    print()
    
    success_count = 0
    error_count = 0
    total_time = 0
    
    for i in range(iterations):
        print(f"Iteration {i+1}/{iterations}")
        
        try:
            # Test health first
            health_response = requests.get(f"{API_URL}/health", timeout=5)
            if health_response.status_code != 200:
                print(f"  Health check failed: {health_response.status_code}")
                error_count += 1
                continue
            
            # Get initial status
            status_response = requests.get(f"{API_URL}/api/servo/status", timeout=5)
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"  Initial status: connected={status.get('connected', False)}")
            
            # Send material command
            start_time = time.time()
            
            response = requests.post(
                f"{API_URL}/api/servo/material/{material}",
                timeout=15  # Increased timeout for slower movements
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                result = response.json()
                print(f"  SUCCESS: {result}")
                print(f"  Response time: {response_time:.0f}ms")
                success_count += 1
            else:
                print(f"  ERROR: HTTP {response.status_code}")
                print(f"  Response: {response.text}")
                error_count += 1
            
            total_time += response_time
            
            # Wait between iterations
            if i < iterations - 1:
                print("  Waiting 2 seconds...")
                time.sleep(2)
                
        except requests.exceptions.Timeout:
            print(f"  ERROR: Request timeout")
            error_count += 1
        except requests.exceptions.ConnectionError:
            print(f"  ERROR: Connection failed - API not running?")
            error_count += 1
            break
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            error_count += 1
        
        print()
    
    # Print summary
    print("=== Test Summary ===")
    print(f"Total iterations: {iterations}")
    print(f"Successful: {success_count}")
    print(f"Failed: {error_count}")
    print(f"Success rate: {(success_count/iterations)*100:.1f}%")
    print(f"Average response time: {total_time/max(1,success_count):.0f}ms")
    print(f"Total test time: {datetime.now().strftime('%H:%M:%S')}")

def update_firmware_delays():
    """Update firmware delays to be 4x faster (divide by 4)"""
    print("Updating firmware delays...")
    
    # Read main.py
    with open('pico_firmware/main.py', 'r') as f:
        content = f.read()
    
    # Update delays in main.py
    content = content.replace(
        'time.sleep(0.5)', 
        'time.sleep(0.125)  # 0.5/4'
    )
    content = content.replace(
        'time.sleep(2.0)', 
        'time.sleep(0.5)  # 2.0/4'
    )
    
    # Write back
    with open('pico_firmware/main.py', 'w') as f:
        f.write(content)
    
    print("Delays updated in main.py")
    
    # Update servo_driver.py for faster movement
    with open('pico_firmware/servo_driver.py', 'r') as f:
        content = f.read()
    
    content = content.replace(
        'delay=0.05', 
        'delay=0.025  # 0.05/2 for faster movement'
    )
    content = content.replace(
        'steps=30', 
        'steps=15  # 30/2 for faster movement'
    )
    
    with open('pico_firmware/servo_driver.py', 'w') as f:
        f.write(content)
    
    print("Movement speed updated in servo_driver.py")

def main():
    """Main function"""
    import sys
    
    # Check if API is running
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        if response.status_code != 200:
            print("ERROR: API not responding properly")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("ERROR: API not running. Start with 'make dev'")
        sys.exit(1)
    
    print("API is running. Starting test...")
    
    # Update firmware delays
    update_firmware_delays()
    
    # Upload updated firmware
    print("\nUploading updated firmware...")
    import subprocess
    result = subprocess.run(['make', 'update-firmware'], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Firmware update failed: {result.stderr}")
        sys.exit(1)
    
    print("Firmware updated successfully")
    
    # Wait for Pico to restart
    print("Waiting for Pico to restart...")
    time.sleep(3)
    
    # Run test
    test_material_sequence(material="plastic", iterations=10)

if __name__ == "__main__":
    main()
