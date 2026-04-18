"""
Servo driver za SG90 servo motor
PWM kontrola na GP0 pinu sa 50Hz frekvencijom
Autor: AI Assistant
"""

from machine import Pin, PWM
import time
import math
from pin_config import PinConfig

class SG90Servo:
    """Klasa za kontrolu SG90 servo motora"""
    
    def __init__(self, pin_number=None, angle_range=(-90, 90), center_angle=0):
        """
        Inicijalizacija serva na odabranom pinu
        :param pin_number: GPIO pin broj
        :param angle_range: Tuple (min_angle, max_angle) 
        :param center_angle: Center position angle
        """
        if pin_number is None:
            raise ValueError("Pin number must be specified")
            
        self.pin = Pin(pin_number)
        self.pwm = PWM(self.pin)
        self.angle_range = angle_range
        self.center_angle = center_angle
        
        # PWM konfiguracija za SG90
        self.pwm.freq(50)  # 50Hz = 20ms period
        
        # Pulse width range: 1ms (0°) to 2ms (180°)
        # Duty cycle: 5% to 10% (50Hz = 20000us period)
        self.min_duty = 65536 * 0.05  # 1ms pulse
        self.max_duty = 65536 * 0.10  # 2ms pulse
        
        # Postavi servo na centar na pochetku
        self.current_angle = center_angle
        self.set_angle(center_angle, smooth=False)
        
    def angle_to_duty(self, angle):
        """
        Konvertuje custom ugao u PWM duty cycle (0-180)
        :param angle: Ugao u stepenima (unutar angle_range)
        :return: Duty cycle vrednost
        """
        # Validacija ugla unutar definisanog opsega
        min_angle, max_angle = self.angle_range
        if angle < min_angle:
            angle = min_angle
        elif angle > max_angle:
            angle = max_angle
        
        # Konverzija custom opsega u 0-180 opseg za PWM
        angle_range_size = max_angle - min_angle
        if angle_range_size == 0:
            pwm_angle = 90  # Default to center if range is zero
        else:
            # Mapiranje: min_angle -> 0, max_angle -> 180
            normalized_angle = (angle - min_angle) / angle_range_size
            pwm_angle = normalized_angle * 180
            
        # Linearna interpolacija izmeðu min i max duty
        duty_range = self.max_duty - self.min_duty
        duty = self.min_duty + (pwm_angle / 180) * duty_range
        
        return int(duty)
    
    def set_angle(self, angle, smooth=True):
        """
        Postavi servo na zadati ugao
        :param angle: Ugao u stepenima (unutar angle_range)
        :param smooth: Da li da koristi glatko kretanje
        """
        # uvijek je smooth, bez else grane
        current_angle = self.current_angle  # koristi praćenu poziciju
        self.move_smooth_ease(current_angle, angle, steps=30, delay=0.05)
        self.current_angle = angle  # ažuriraj trenutnu poziciju
        
    def move_smooth_ease(self, start_angle, end_angle, steps=30, delay=0.05):
        """
        Glatko pomeranje serva između dva ugla sa easing funkcijom (ease-in-out).
        :param start_angle: Početni ugao
        :param end_angle: Krajnji ugao
        :param steps: Broj koraka
        :param delay: Kašnjenje između koraka
        """
        for i in range(steps + 1):
            t = i / steps  # t in [0, 1]
            
            # Ease-in-out (slično CSS easing easing(0.4, 0, 0.6, 1))
            eased = (1 - math.cos(t * math.pi)) * 0.5
            
            current_angle = start_angle + (end_angle - start_angle) * eased
            duty = self.angle_to_duty(current_angle)
            self.pwm.duty_u16(duty)
            time.sleep(delay)

    def cleanup(self):
        """Čišćenje resursa"""
        self.pwm.deinit()
        self.pin.init()
