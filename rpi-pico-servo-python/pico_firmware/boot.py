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

# Pokreni glavni program
try:
    import main
    # Start the main controller loop
    controller = main.PicoServoController()
    controller.run()
except Exception as e:
    print("Failed to start main:", e)
    # Blink LED 5 puta ako nije uspelo
    for i in range(5):
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)
