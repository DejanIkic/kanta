"""
Pin konfiguracija za SG90 servo motor
Mapiranje žica na Pico pinove prema specifikaciji
Autor: AI Assistant
"""


class PinConfig:
    """Konfiguracija pinova za servo motor"""

    # Servo žice → Pico pinovi mapiranje (SAMO DOZVOLJENI PINOVI)
    SERVO_PINS = {
        "VERTICAL": {
            "wire_color": "Žuta/naranđa",
            "description": "Vertical servo signal (-90 to 90)",
            "pin_number": 2,  # GP2
            "pin_name": "GP2",
            "gpio": 2,
        },
        "HORIZONTAL": {
            "wire_color": "Plava/bela",
            "description": "Horizontal servo signal (-20 to 20)",
            "pin_number": 3,  # GP3
            "pin_name": "GP3",
            "gpio": 3,
        },
        "VCC": {
            "wire_color": "Crvena",
            "description": "VCC (3.3V)",
            "pin_number": 40,  # VBUS
            "pin_name": "VBUS",
            "voltage": "5V",
        },
        "GND": {
            "wire_color": "Crna/smeđa",
            "description": "GND",
            "pin_number": 38,
            "pin_name": "GND",
            "voltage": "0V",
        },
    }

    # Dozvoljeni fizički pinovi - SVE OSTALE PINOVE BLOKIRATI
    ALLOWED_PINS = {2, 3, 25}  # GPIO2, GPIO3, LED (fizički pinovi 4,5,25)

    @classmethod
    def get_blocked_pins(cls):
        """Vrati set blokiranih pinova"""
        return {i for i in range(0, 29) if i not in cls.ALLOWED_PINS}

    # UART pinovi za komunikaciju
    UART_PINS = {
        "TX": {"pin_number": 0, "pin_name": "GP0", "gpio": 0},
        "RX": {"pin_number": 1, "pin_name": "GP1", "gpio": 1},
    }

    # Status LED
    STATUS_LED = {"pin_number": 25, "pin_name": "GPIO25", "description": "Interni LED"}

    @classmethod
    def get_vertical_pin(cls):
        """Vrati GPIO broj za vertical servo"""
        return cls.SERVO_PINS["VERTICAL"]["gpio"]

    @classmethod
    def get_horizontal_pin(cls):
        """Vrati GPIO broj za horizontal servo"""
        return cls.SERVO_PINS["HORIZONTAL"]["gpio"]

    @classmethod
    def get_uart_pins(cls):
        """Vrati UART TX i RX GPIO brojeve"""
        return (cls.UART_PINS["TX"]["gpio"], cls.UART_PINS["RX"]["gpio"])

    @classmethod
    def get_status_led_pin(cls):
        """Vrati GPIO broj za status LED"""
        return cls.STATUS_LED["pin_number"]

    @classmethod
    def block_unused_pins(cls):
        """Blokiraj sve nekoriscene GPIO pinove za sigurnost"""
        from machine import Pin
        print("Blokiram nekoriscene GPIO pinove za sigurnost...")
        blocked_pins = cls.get_blocked_pins()
        for pin_num in blocked_pins:
            try:
                pin = Pin(pin_num, Pin.IN, Pin.PULL_DOWN)
                print(f"  Blokiran GPIO{pin_num}")
            except Exception as e:
                print(f"  Ne mogu da blokiram GPIO{pin_num}: {e}")
        print(f"Dozvoljeni GPIO pinovi: {sorted(cls.ALLOWED_PINS)}")
        print("Fizički pinovi: 4(GPIO2), 5(GPIO3), 25(LED), 38(GND), 40(VBUS)")

    @classmethod
    def print_pin_mapping(cls):
        """Ispiši mapiranje pinova"""
        print("Servo žice → Pico pinovi (SAMO DOZVOLJENI PINOVI)")
        print("-" * 50)
        for pin_type, config in cls.SERVO_PINS.items():
            print(
                f"{config['wire_color']:12} → {config['pin_name']:8} (Pin {config['pin_number']})"
            )
        print()
        print("UART Pinovi:")
        print(
            f"TX → {cls.UART_PINS['TX']['pin_name']} (Pin {cls.UART_PINS['TX']['pin_number']})"
        )
        print(
            f"RX → {cls.UART_PINS['RX']['pin_name']} (Pin {cls.UART_PINS['RX']['pin_number']})"
        )
        print()
        print(f"Dozvoljeni pinovi: {sorted(cls.ALLOWED_PINS)}")
        print(f"Blokirani pinovi: {sorted(cls.get_blocked_pins())}")


if __name__ == "__main__":
    PinConfig.print_pin_mapping()
