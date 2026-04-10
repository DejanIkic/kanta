#!/usr/bin/env python3
"""
Mock test for servo controller logic without hardware
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'rpi_api'))

from rpi_api.servo_service import ServoController
from rpi_api.config import settings

def test_material_logic():
    """Test material position mapping without hardware"""
    
    print("Testing Material Logic (Mock)")
    print("=" * 40)
    
    # Create controller instance
    controller = ServoController()
    
    # Test material positions from config
    print("Material positions from config:")
    for material, positions in settings.material_positions.items():
        print(f"  {material}: vertical={positions['vertical']}, horizontal={positions['horizontal']}")
    
    print("\nTesting command validation (no hardware):")
    
    # Test each material type validation
    materials = ["plastic", "glass", "pet", "organic"]
    
    for material in materials:
        positions = settings.material_positions[material]
        print(f"\n{material.upper()}:")
        print(f"  Target positions: {positions}")
        
        # Validate vertical angle range
        v_angle = positions['vertical']
        if -90 <= v_angle <= 90:
            print(f"  Vertical angle {v_angle}°: VALID")
        else:
            print(f"  Vertical angle {v_angle}°: INVALID")
        
        # Validate horizontal angle range
        h_angle = positions['horizontal']
        if -20 <= h_angle <= 20:
            print(f"  Horizontal angle {h_angle}°: VALID")
        else:
            print(f"  Horizontal angle {h_angle}°: INVALID")
    
    print("\nTesting invalid material:")
    invalid_materials = ["metal", "paper", "wood", ""]
    for material in invalid_materials:
        if material in settings.material_positions:
            print(f"  '{material}': UNEXPECTED VALID")
        else:
            print(f"  '{material}': CORRECTLY INVALID")
    
    print("\nSequence timing test:")
    print(f"  Servo sequence delay: {settings.servo_sequence_delay}s")
    print(f"  Trash drop delay: 1.5s")
    print(f"  Expected total sequence time: ~2.5s (0.5s + 1.5s + 0.5s)")
    
    print("\nMock test completed successfully!")

if __name__ == "__main__":
    test_material_logic()
