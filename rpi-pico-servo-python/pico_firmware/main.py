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
        # Inicijalizacija dva serva sa razlièitim opsezima
        self.vertical_servo = SG90Servo(
            pin_number=PinConfig.get_vertical_pin(),
            angle_range=(-90, 90),
            center_angle=0
        )
        self.horizontal_servo = SG90Servo(
            pin_number=PinConfig.get_horizontal_pin(),
            angle_range=(-20, 20),
            center_angle=0
        )
        
        self.led = Pin(PinConfig.get_status_led_pin(), Pin.OUT)
        self.poller = select.poll()
        self.poller.register(sys.stdin, select.POLLIN)
        
        # Mapiranje materijala na pozicije
        self.material_positions = {
            "plastic": {"vertical": -90, "horizontal": -20},
            "glass": {"vertical": -90, "horizontal": 20},
            "pet": {"vertical": 90, "horizontal": -20},
            "organic": {"vertical": 90, "horizontal": 20}
        }
        
        print("Pico Dual Servo Controller - Ready")
        PinConfig.print_pin_mapping()
        self.led_on()

    def led_on(self):
        self.led.value(1)

    def led_off(self):
        self.led.value(0)

    def parse_command(self, command):
        try:
            if command.startswith("MATERIAL:"):
                material = command.split(":")[1].strip().lower()
                if material in self.material_positions:
                    return True, ("material", material)
                else:
                    return False, f"Unknown material: {material}"
            
            elif command.startswith("VERTICAL:"):
                angle = int(command.split(":")[1].strip())
                if -90 <= angle <= 90:
                    return True, ("vertical", angle)
                else:
                    return False, "Vertical angle out of range (-90 to 90)"
            
            elif command.startswith("HORIZONTAL:"):
                angle = int(command.split(":")[1].strip())
                if -20 <= angle <= 20:
                    return True, ("horizontal", angle)
                else:
                    return False, "Horizontal angle out of range (-20 to 20)"
            
            elif command.startswith("BASE:"):
                # Return to base position
                return True, ("base", 0)
            
            elif command.startswith("ANGLE:"):  # Backward compatibility
                angle = int(command.split(":")[1].strip())
                if 0 <= angle <= 180:
                    return True, ("legacy", angle)
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

    def execute_command(self, command_type, value):
        """Izvrðavanje komandi sa sekvencijalnim pokretom"""
        try:
            if command_type == "material":
                # Materijal komanda: vertical -> delay -> horizontal -> delay -> base
                positions = self.material_positions[value]
                
                # Pokreni vertical servo
                self.vertical_servo.set_angle(positions["vertical"])
                time.sleep(0.5)  # Delay izmeðu serva
                
                # Pokreni horizontal servo
                self.horizontal_servo.set_angle(positions["horizontal"])
                time.sleep(1.5)  # Delay pre povratka (za dropanje otpada)
                
                # Vrati oba serva u baznu poziciju
                self.vertical_servo.set_angle(0)
                self.horizontal_servo.set_angle(0)
                time.sleep(0.5)  # Final delay
                
                response_msg = f"material:{value},vertical:{positions['vertical']},horizontal:{positions['horizontal']},base:0,0"
                return True, response_msg
                
            elif command_type == "vertical":
                self.vertical_servo.set_angle(value)
                return True, f"vertical:{value}"
                
            elif command_type == "horizontal":
                self.horizontal_servo.set_angle(value)
                return True, f"horizontal:{value}"
                
            elif command_type == "base":
                # Vrati oba serva u baznu poziciju
                self.vertical_servo.set_angle(0)
                self.horizontal_servo.set_angle(0)
                return True, "base:0,0"
                
            elif command_type == "legacy":
                # Backward compatibility - koristi horizontal servo
                self.horizontal_servo.set_angle(value)
                return True, f"legacy:{value}"
                
            else:
                return False, f"Unknown command type: {command_type}"
                
        except Exception as e:
            return False, f"Execution error: {str(e)}"

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
                                command_type, value = result
                                exec_success, exec_result = self.execute_command(command_type, value)
                                self.send_response(exec_success, exec_result)
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
            controller.vertical_servo.cleanup()
            controller.horizontal_servo.cleanup()
        print("Program ended")
