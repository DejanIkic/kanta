"""
Servo driver za SG90 servo motor
PWM kontrola na GP0 pinu sa 50Hz frekvencijom
Autor: AI Assistant
"""

from machine import Pin, PWM
import time
from pin_config import PinConfig

class SG90Servo:
    """Klasa za kontrolu SG90 servo motora"""
    
    def __init__(self, pin_number=None):
        """
        Inicijalizacija serva na odabranom pinu
        :param pin_number: GPIO pin broj (default iz PinConfig)
        """
        if pin_number is None:
            pin_number = PinConfig.get_servo_signal_pin()
            
        self.pin = Pin(pin_number)
        self.pwm = PWM(self.pin)
        
        # PWM konfiguracija za SG90
        self.pwm.freq(50)  # 50Hz = 20ms period
        
        # Pulse width range: 1ms (0°) to 2ms (180°)
        # Duty cycle: 5% to 10% (50Hz = 20000us period)
        self.min_duty = 65536 * 0.05  # 1ms pulse
        self.max_duty = 65536 * 0.10  # 2ms pulse
        
        # Postavi servo na sredinu (90°) na početku
        self.set_angle(90)
        
    def angle_to_duty(self, angle):
        """
        Konvertuje ugao (0-180) u PWM duty cycle
        :param angle: Ugao u stepenima
        :return: Duty cycle vrednost
        """
        if angle < 0:
            angle = 0
        elif angle > 180:
            angle = 180
            
        # Linearna interpolacija između min i max duty
        duty_range = self.max_duty - self.min_duty
        duty = self.min_duty + (angle / 180) * duty_range
        
        return int(duty)
    
    def set_angle(self, angle):
        """
        Postavi servo na zadati ugao
        :param angle: Ugao u stepenima (0-180)
        """
        duty = self.angle_to_duty(angle)
        self.pwm.duty_u16(duty)
        
    def move_smooth(self, start_angle, end_angle, steps=20, delay=0.05):
        """
        Glatko pomeranje serva između dva ugla
        :param start_angle: Početni ugao
        :param end_angle: Krajnji ugao
        :param steps: Broj koraka
        :param delay: Kašnjenje između koraka
        """
        angle_step = (end_angle - start_angle) / steps
        
        for i in range(steps + 1):
            current_angle = start_angle + (angle_step * i)
            self.set_angle(int(current_angle))
            time.sleep(delay)
    
    def cleanup(self):
        """Čišćenje resursa"""
        self.pwm.deinit()
        self.pin.init()
