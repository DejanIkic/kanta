"""
Glavna MicroPython skripta za Raspberry Pi Pico
Cita komande preko USB serijske veze i kontrolise SG90 servo motor
Autor: AI Assistant
"""

import sys
import select
import time
from machine import Pin
from servo_driver import SG90Servo
from pin_config import PinConfig


class PicoServoController:

    def __init__(self):
        self.servo = SG90Servo()
        self.led = Pin(PinConfig.get_status_led_pin(), Pin.OUT)
        self.poller = select.poll()
        self.poller.register(sys.stdin, select.POLLIN)
        print("Pico Servo Controller - Ready")
        PinConfig.print_pin_mapping()
        self.led_on()

    def led_on(self):
        self.led.value(1)

    def led_off(self):
        self.led.value(0)

    def parse_command(self, command):
        try:
            if command.startswith("ANGLE:"):
                angle = int(command.split(":")[1].strip())
                if 0 <= angle <= 180:
                    return True, angle
                else:
                    return False, "Angle out of range (0-180)"
            else:
                return False, "Invalid command format"
        except (ValueError, IndexError) as e:
            return False, "Parse error: " + str(e)

    def send_response(self, success, message):
        if success:
            sys.stdout.write("OK:" + message + "\n")
        else:
            sys.stdout.write("ERROR:" + message + "\n")

    def run(self):
        print("Starting main loop...")
        buf = ""
        while True:
            try:
                if self.poller.poll(0):
                    char = sys.stdin.read(1)
                    if char in ('\n', '\r'):
                        cmd = buf.strip()
                        buf = ""
                        if cmd:
                            self.led_off()
                            time.sleep(0.05)
                            self.led_on()
                            success, result = self.parse_command(cmd)
                            if success:
                                self.servo.set_angle(result)
                                self.send_response(True, "Angle set to " + str(result))
                            else:
                                self.send_response(False, result)
                    else:
                        buf += char
                time.sleep(0.001)
            except Exception as e:
                self.send_response(False, "System error: " + str(e))
                time.sleep(1)


if __name__ == "__main__":
    try:
        controller = PicoServoController()
        controller.run()
    except KeyboardInterrupt:
        print("Program stopped by user")
    except Exception as e:
        print("Fatal error: " + str(e))
    finally:
        if "controller" in locals():
            controller.servo.cleanup()
        print("Program ended")
