"""
Glavna MicroPython skripta za Raspberry Pi Pico
Čita UART komande i kontroliše SG90 servo motor
Autor: AI Assistant
"""

from machine import UART, Pin
import time
from servo_driver import SG90Servo
from pin_config import PinConfig

class PicoServoController:
    """Kontroler za servo preko UART komunikacije"""
    
    def __init__(self, uart_tx=None, uart_rx=None, baudrate=115200):
        """
        Inicijalizacija UART i serva
        :param uart_tx: TX pin broj (default iz PinConfig)
        :param uart_rx: RX pin broj (default iz PinConfig)
        :param baudrate: UART baud rate
        """
        # Dobavi UART pinove iz konfiguracije
        if uart_tx is None or uart_rx is None:
            uart_tx, uart_rx = PinConfig.get_uart_pins()
            
        # UART inicijalizacija
        self.uart = UART(uart_tx, uart_rx, baudrate=baudrate)
        
        # Servo inicijalizacija sa pinom iz konfiguracije
        self.servo = SG90Servo()
        
        # Status LED sa pina iz konfiguracije
        self.led = Pin(PinConfig.get_status_led_pin(), Pin.OUT)
        
        print("Pico Servo Controller - Ready")
        PinConfig.print_pin_mapping()
        self.led_on()
        
    def led_on(self):
        """Uključi internu LED"""
        self.led.value(1)
        
    def led_off(self):
        """Isključi internu LED"""
        self.led.value(0)
        
    def parse_command(self, command):
        """
        Parsira UART komandu
        Format: "ANGLE:{value}" gde je value 0-180
        :param command: String komanda
        :return: Tuple (success, angle ili error_message)
        """
        try:
            if command.startswith("ANGLE:"):
                angle_str = command.split(":")[1].strip()
                angle = int(angle_str)
                
                if 0 <= angle <= 180:
                    return True, angle
                else:
                    return False, "Angle out of range (0-180)"
            else:
                return False, "Invalid command format"
                
        except (ValueError, IndexError) as e:
            return False, f"Parse error: {str(e)}"
    
    def send_response(self, success, message):
        """
        Šalje odgovor preko UART-a
        :param success: True/False
        :param message: Poruka
        """
        if success:
            response = f"OK:{message}\n"
        else:
            response = f"ERROR:{message}\n"
            
        self.uart.write(response.encode())
    
    def run(self):
        """Glavna petlja programa"""
        print("Starting main loop...")
        
        while True:
            try:
                # Čekaj UART podatke
                if self.uart.any():
                    # Čitaj liniju (do newline)
                    command = self.uart.readline()
                    
                    if command:
                        # Dekodiraj i očisti komandu
                        command_str = command.decode().strip()
                        print(f"Received: {command_str}")
                        
                        # Blink LED za indikaciju prijema
                        self.led_off()
                        time.sleep(0.1)
                        self.led_on()
                        
                        # Parsiraj komandu
                        success, result = self.parse_command(command_str)
                        
                        if success:
                            # Postavi servo ugao
                            angle = result
                            self.servo.set_angle(angle)
                            print(f"Servo set to angle: {angle}°")
                            
                            # Pošalji potvrdu
                            self.send_response(True, f"Angle set to {angle}")
                        else:
                            # Greška u parsiranju
                            error_msg = result
                            print(f"Error: {error_msg}")
                            self.send_response(False, error_msg)
                
                # Malo kašnjenje da ne opterećujemo CPU
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Main loop error: {str(e)}")
                self.send_response(False, f"System error: {str(e)}")
                time.sleep(1)  # Čekaj preko ponovnim pokušajem

if __name__ == "__main__":
    try:
        controller = PicoServoController()
        controller.run()
    except KeyboardInterrupt:
        print("Program stopped by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
    finally:
        # Čišćenje resursa
        if 'controller' in locals():
            controller.servo.cleanup()
        print("Program ended")
