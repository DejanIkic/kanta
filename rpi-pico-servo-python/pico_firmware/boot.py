"""
Boot skripta za Raspberry Pi Pico
Automatsko pokretanje servo kontrolera
Autor: AI Assistant
"""

import time
import machine

# Inicijalizacija internog LED-a
led = machine.Pin(25, machine.Pin.OUT)

# Blink LED 3 puta na startup
for i in range(3):
    led.on()
    time.sleep(0.2)
    led.off()
    time.sleep(0.2)

# Import i pokreni main.py
try:
    import main
except Exception as e:
    print(f"Boot error: {str(e)}")
    # Brzo blinkanje ako greška
    while True:
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)
