#!/usr/bin/env python3
"""
Script za automatsko azuriranje firmware-a kada se fajlove promene
Koristi: python scripts/watch_firmware.py
Autor: AI Assistant
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FirmwareWatcher(FileSystemEventHandler):
    """Handler za promene firmware fajlova"""
    
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.last_update = 0
        self.debounce_time = 2  # sekunde
        
    def on_modified(self, event):
        """Kada se fajl modifikuje"""
        if event.is_directory:
            return
            
        # Proveri da li je firmware fajl
        firmware_files = ["boot.py", "main.py", "servo_driver.py", "pin_config.py"]
        filename = os.path.basename(event.src_path)
        
        if filename in firmware_files:
            current_time = time.time()
            
            # Debounce - spreci dupliranje update-a
            if current_time - self.last_update < self.debounce_time:
                return
                
            self.last_update = current_time
            
            print(f"\nDetektovana promena: {filename}")
            print("Azuriram firmware...")
            
            # Pokreni update script
            try:
                result = subprocess.run(
                    [sys.executable, "scripts/update_firmware.py"],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print("Firmware uspesno azuriran!")
                else:
                    print(f"Greska pri azuriranju: {result.stderr}")
                    
            except Exception as e:
                print(f"Greska: {e}")

def main():
    """Glavna funkcija"""
    base_dir = Path(__file__).parent.parent
    firmware_dir = base_dir / "pico_firmware"
    
    if not firmware_dir.exists():
        print(f"Greska: Firmware direktorijum ne postoji: {firmware_dir}")
        sys.exit(1)
    
    print("=== Pico Firmware Watcher ===")
    print(f"Pratim promene u: {firmware_dir}")
    print("Ctrl+C za prekid")
    print()
    
    # Kreiraj observer
    event_handler = FirmwareWatcher(base_dir)
    observer = Observer()
    observer.schedule(event_handler, str(firmware_dir), recursive=False)
    
    # Pokreni observer
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nWatcher zaustavljen")
    
    observer.join()

if __name__ == "__main__":
    main()
