"""
Pin konfiguracija za SG90 servo motor
Mapiranje žica na Pico pinove prema specifikaciji
Autor: AI Assistant
"""


class PinConfig:
    """Konfiguracija pinova za servo motor"""

    # Servo žice → Pico pinovi mapiranje
    SERVO_PINS = {
        "VCC": {
            "wire_color": "Crvena",
            "description": "VCC (3.3V)",
            "pin_number": 36,
            "pin_name": "VBUS",
            "voltage": "3.3V",
        },
        "GND": {
            "wire_color": "Crna/smeđa",
            "description": "GND",
            "pin_number": 38,
            "pin_name": "GND",
            "voltage": "0V",
        },
        "SIGNAL": {
            "wire_color": "Žuta/naranđa",
            "description": "Servo signal",
            "pin_number": 1,
            "pin_name": "GP0",
            "gpio": 0,
        },
    }

    # UART pinovi za komunikaciju
    UART_PINS = {
        "TX": {"pin_number": 0, "pin_name": "GP0", "gpio": 0},
        "RX": {"pin_number": 1, "pin_name": "GP1", "gpio": 1},
    }

    # Status LED
    STATUS_LED = {"pin_number": 25, "pin_name": "GPIO25", "description": "Interni LED"}

    @classmethod
    def get_servo_signal_pin(cls):
        """Vrati GPIO broj za servo signal"""
        return cls.SERVO_PINS["SIGNAL"]["gpio"]

    @classmethod
    def get_uart_pins(cls):
        """Vrati UART TX i RX GPIO brojeve"""
        return (cls.UART_PINS["TX"]["gpio"], cls.UART_PINS["RX"]["gpio"])

    @classmethod
    def get_status_led_pin(cls):
        """Vrati GPIO broj za status LED"""
        return cls.STATUS_LED["pin_number"]

    @classmethod
    def print_pin_mapping(cls):
        """Ispiši mapiranje pinova"""
        print("Servo žice → Pico pinovi")
        print("-" * 30)
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


if __name__ == "__main__":
    PinConfig.print_pin_mapping()
