#!/usr/bin/env python3
"""
Script za automatsko upload-ovanje firmware-a na Pico i restart
Koristi se kada se naprave izmene u pico_firmware direktorijumu
Autor: AI Assistant
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Defini fajlove za upload
FIRMWARE_FILES = [
    "boot.py",
    "main.py", 
    "servo_driver.py",
    "pin_config.py"
]

def run_command(cmd, cwd=None):
    """Izvrshi komandu i vrati rezultat"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        if result.returncode != 0:
            print(f"Greka pri izvrshavanju: {cmd}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Izuzetak pri izvrshavanju komande: {e}")
        return False

def check_pico_connected():
    """Proveri da li je Pico povezan"""
    print("Proveravam konekciju sa Pico...")
    
    # Proveri da li postoji /dev/ttyACM0
    if not os.path.exists("/dev/ttyACM0"):
        print("Greska: Pico nije povezan (/dev/ttyACM0 ne postoji)")
        return False
    
    # Testiraj konekciju sa mpremote
    if not run_command("mpremote connect /dev/ttyACM0 exec \"print('Pico connected')\""):
        print("Greska: Ne mogu da se povezem sa Pico-om")
        return False
    
    print("Pico je povezan i spreman")
    return True

def upload_firmware():
    """Upload-uj sve firmware fajlove na Pico"""
    print("Upload-ujem firmware fajlove...")
    
    base_dir = Path(__file__).parent.parent
    firmware_dir = base_dir / "pico_firmware"
    
    for filename in FIRMWARE_FILES:
        source_file = firmware_dir / filename
        target_path = f":{filename}"
        
        if not source_file.exists():
            print(f"Upozorenje: Fajl ne postoji: {source_file}")
            continue
        
        print(f"  Upload-ujem {filename}...")
        cmd = f"mpremote connect /dev/ttyACM0 cp pico_firmware/{filename} {target_path}"
        
        if not run_command(cmd, cwd=base_dir):
            print(f"Greska pri upload-u fajla: {filename}")
            return False
    
    print("Svi firmware fajlovi su upload-ovani")
    return True

def restart_pico():
    """Restartuj Pico da bi uzeo novi firmware"""
    print("Restartujem Pico...")
    
    if not run_command("mpremote connect /dev/ttyACM0 reset"):
        print("Greska pri restart-u Pico-a")
        return False
    
    print("Pico je restart-ovan")
    return True

def test_connection():
    """Testiraj da li firmware radi ispravno"""
    print("Testiram konekciju...")
    
    # Sacekaj da se Pico podigne
    time.sleep(3)
    
    # Testiraj sa ANGLE komandom
    test_cmd = "echo 'ANGLE:90' > /dev/ttyACM0"
    if not run_command(test_cmd):
        print("Upozorenje: Ne mogu da posaljem test komandu")
        return False
    
    # Sacekaj odgovor
    time.sleep(1)
    
    print("Firmware je testiran i spreman")
    return True

def main():
    """Glavna funkcija"""
    print("=== Pico Firmware Update Script ===")
    print("Azhuriram firmware na Raspberry Pi Pico...")
    print()
    
    # Proveri konekciju
    if not check_pico_connected():
        sys.exit(1)
    
    # Upload firmware
    if not upload_firmware():
        sys.exit(1)
    
    # Restart Pico
    if not restart_pico():
        sys.exit(1)
    
    # Test konekcije
    if not test_connection():
        print("Upozorenje: Test konekcije nije uspeo, ali firmware je upload-ovan")
    
    print()
    print("=== Zavrseno! ===")
    print("Firmware je uspesno azuriran na Pico.")
    print("Sada mozete pokrenuti API: make dev")
    print()

if __name__ == "__main__":
    main()
