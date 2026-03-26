#!/usr/bin/env python3
"""
Skripta za flashing MicroPython firmware na Raspberry Pi Pico
Autor: AI Assistant
"""

import os
import sys
import time
import serial.tools.list_ports
from pathlib import Path

def find_pico_port():
    """Pronalazi Pico USB port"""
    print("Tražim Raspberry Pi Pico...")
    
    ports = serial.tools.list_ports.comports()
    pico_ports = []
    
    print(f"Pronađeno {len(ports)} COM portova:")
    for port in ports:
        print(f"  - {port.device}: {port.description} ({port.manufacturer})")
        
        # Pico se obično javlja kao USB Serial Device ili MicroPython
        if ("USB Serial" in port.description or 
            "Pico" in port.description or 
            "MicroPython" in port.description or
            "Board in FS mode" in port.description):
            pico_ports.append(port)
            print(f"*** Pico kandidat: {port.device} - {port.description}")
    
    if not pico_ports:
        print("Pico nije pronađen. Uverite se da:")
        print("1. Pico je povezan preko USB kabela")
        print("2. Držite BOOTSEL taster dok povezujete USB")
        print("3. Pico je u bootloader modu (pojavi se kao USB storage)")
        return None
    
    return pico_ports[0].device if len(pico_ports) == 1 else pico_ports

def flash_firmware(port=None):
    """Flash MicroPython firmware na Pico"""
    try:
        import subprocess
        
        # Download MicroPython firmware za Pico
        firmware_url = "https://micropython.org/download/rp2-pico/rp2-pico-latest.uf2"
        firmware_file = "rp2-pico-latest.uf2"
        
        print("Download MicroPython firmware...")
        subprocess.run(["wget", "-O", firmware_file, firmware_url], check=True)
        
        # Pronađi Pico kao storage device
        pico_drive = None
        for drive in ["/media", "/mnt"]:
            if os.path.exists(drive):
                for item in os.listdir(drive):
                    if "RPI-RP2" in item or "PICO" in item:
                        pico_drive = os.path.join(drive, item)
                        break
        
        if not pico_drive:
            print("Pico storage nije pronađen. Uverite se da je Pico u BOOTSEL modu!")
            return False
        
        print(f"Flash firmware na {pico_drive}...")
        firmware_path = os.path.join(pico_drive, firmware_file)
        
        # Kopiraj firmware
        subprocess.run(["cp", firmware_file, firmware_path], check=True)
        
        print("Firmware uspešno flash-ovan!")
        print("Sačekajte 5 sekundi da se Pico restartuje...")
        time.sleep(5)
        
        # Očisti
        os.remove(firmware_file)
        
        return True
        
    except Exception as e:
        print(f"Greška pri flash-ovanju: {str(e)}")
        return False

def upload_code(port):
    """Upload Python kod na Pico"""
    try:
        import subprocess
        
        print(f"Upload koda na Pico (port: {port})...")
        
        # Koristi rshell za upload
        pico_dir = Path("pico_firmware")
        
        # Upload main.py
        subprocess.run([
            "rshell", "--port", port, "cp", 
            str(pico_dir / "main.py"), "/pyboard/main.py"
        ], check=True)
        
        # Upload servo_driver.py
        subprocess.run([
            "rshell", "--port", port, "cp", 
            str(pico_dir / "servo_driver.py"), "/pyboard/servo_driver.py"
        ], check=True)
        
        # Upload boot.py
        subprocess.run([
            "rshell", "--port", port, "cp", 
            str(pico_dir / "boot.py"), "/pyboard/boot.py"
        ], check=True)
        
        print("Kod uspešno upload-ovan na Pico!")
        return True
        
    except Exception as e:
        print(f"Greška pri upload-u koda: {str(e)}")
        return False

def main():
    """Glavna funkcija"""
    print("=== Raspberry Pi Pico Upload Tool ===")
    
    # Proveri da li postoji pico_firmware direktorijum
    if not os.path.exists("pico_firmware"):
        print("Greška: pico_firmware direktorijum ne postoji!")
        sys.exit(1)
    
    # Pronađi Pico port
    pico_port = find_pico_port()
    if not pico_port:
        print("Pico nije pronađen. Pokušajte ponovo.")
        sys.exit(1)
    
    # Preskoči flash firmware - već imate MicroPython
    print("MicroPython firmware već postoji, preskačem flash...")
    
    # Upload koda
    if isinstance(pico_port, list):
        pico_port = pico_port[0]  # Uzmi prvi port ako ih je više
    
    if not upload_code(pico_port):
        print("Upload koda nije uspeo.")
        sys.exit(1)
    
    print("\n=== Uspešno završeno! ===")
    print("Vaš kod je upload-ovan na Pico.")
    print("Sada možete pokrenuti aplikaciju: make debug")

if __name__ == "__main__":
    main()
