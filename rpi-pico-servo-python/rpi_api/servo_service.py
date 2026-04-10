"""
Servo kontrola i serijska komunikacija sa Pico-om
Autor: AI Assistant
"""

import serial
import time
import structlog
from datetime import datetime
from typing import Optional, Tuple
from .config import settings

logger = structlog.get_logger()

class ServoController:
    """Kontroler za servo komunikaciju sa Pico-om"""
    
    def __init__(self):
        """Inicijalizacija serijske konekcije"""
        self.serial_conn: Optional[serial.Serial] = None
        self.last_command_time: Optional[datetime] = None
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        self.serial_port = settings.serial_port
        
    def connect(self) -> bool:
        """
        Povezivanje sa Pico-om preko serijskog porta
        :return: True ako je uspešno, False inače
        """
        try:
            # Ako smo već povezani, vrati True
            if self.serial_conn and self.serial_conn.is_open:
                return True
            
            # Zatvori postojeću konekciju ako postoji
            if self.serial_conn:
                self.serial_conn.close()
                
            logger.info("Connecting to Pico", port=self.serial_port)
            self.serial_conn = serial.Serial(
                port=self.serial_port,
                baudrate=settings.serial_baudrate,
                timeout=settings.serial_timeout,
                write_timeout=settings.serial_timeout
            )
            
            # Čekaj da se konekcija stabilizuje
            time.sleep(2)
            
            # Test komunikacije
            if self._test_connection():
                logger.info("Successfully connected to Pico")
                self.connection_attempts = 0
                return True
            else:
                logger.error("Connection test failed")
                self.disconnect()
                return False
                
        except serial.SerialException as e:
            logger.error("Serial connection failed", error=str(e))
            self.connection_attempts += 1
            return False
        except Exception as e:
            logger.error("Unexpected connection error", error=str(e))
            self.connection_attempts += 1
            return False
    
    def disconnect(self):
        """Prekida konekciju sa Pico-om"""
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                logger.info("Disconnected from Pico")
        except Exception as e:
            logger.error("Error disconnecting", error=str(e))
        finally:
            self.serial_conn = None
    
    def _test_connection(self) -> bool:
        """
        Testira konekciju slanjem test komande
        :return: True ako je odgovor primljen, False inače
        """
        try:
            # Pošalji test komandu
            test_command = "ANGLE:20\n"
            logger.info("Sending test command", command=test_command.strip(), port=self.serial_port)
            self.serial_conn.write(test_command.encode())
            
            # Čekaj odgovor
            start_time = time.time()
            response = ""
            
            while (time.time() - start_time) < settings.serial_timeout:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode().strip()
                    response += data
                    
                    if "OK:" in response:
                        return True
                    elif "ERROR:" in response:
                        return False
                
                time.sleep(0.01)

            
            logger.warning("No response to test command", timeout=settings.serial_timeout)
            return False
            
        except Exception as e:
            logger.error("Connection test error", error=str(e))
            return False
    
    def set_angle(self, angle: int) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Postavi servo na zadati ugao (legacy - horizontal servo)
        :param angle: Ugao u stepenima (-20:20) (-90:90)
        :return: (success, error_message, response_time_ms)
        """
        start_time = time.time()
        
        try:
            # Validacija ugla
            if not (settings.servo_min_angle <= angle <= settings.servo_max_angle):
                return False, f"Angle must be between {settings.servo_min_angle} and {settings.servo_max_angle}", None
            
            # Poveži se ako nismo konektovani
            if not self.connect():
                return False, "Failed to connect to Pico", None
            
            # Pošalji komandu
            command = f"ANGLE:{angle}\n"
            logger.info("Sending servo command", angle=angle, command=command.strip())
            
            self.serial_conn.write(command.encode())
            self.serial_conn.flush()
            
            # Čekaj odgovor
            response = ""
            response_start = time.time()
            
            while (time.time() - response_start) < settings.servo_move_timeout:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode().strip()
                    response += data
                    
                    if response.startswith("OK:"):
                        self.last_command_time = datetime.now()
                        response_time = int((time.time() - start_time) * 1000)
                        logger.info("Servo command successful", 
                                  angle=angle, 
                                  response_time_ms=response_time)
                        return True, None, response_time
                    elif response.startswith("ERROR:"):
                        error_msg = response.replace("ERROR:", "").strip()
                        logger.error("Servo command failed", angle=angle, error=error_msg)
                        return False, error_msg, None
                
                time.sleep(0.01)
            
            # Timeout
            response_time = int((time.time() - start_time) * 1000)
            error_msg = "Timeout waiting for servo response"
            logger.error("Servo command timeout", 
                        angle=angle, 
                        timeout=settings.servo_move_timeout,
                        response_time_ms=response_time)
            return False, error_msg, response_time
            
        except serial.SerialException as e:
            error_msg = f"Serial communication error: {str(e)}"
            logger.error("Serial error", angle=angle, error=str(e))
            self.disconnect()  # Prekini vezu nakon greške
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("Unexpected servo error", angle=angle, error=str(e))
            return False, error_msg, None
    
    def get_status(self) -> Tuple[bool, Optional[datetime], int]:
        """
        Vraæa status konekcije
        :return: (connected, last_command_time, connection_attempts)
        """
        connected = self.connect()
        return connected, self.last_command_time, self.connection_attempts

    def set_vertical_angle(self, angle: int) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Postavi vertical servo na zadati ugao
        :param angle: Ugao u stepenima (-90 to 90)
        :return: (success, error_message, response_time_ms)
        """
        start_time = time.time()
        
        try:
            # Validacija ugla
            if not (-90 <= angle <= 90):
                return False, "Vertical angle must be between -90 and 90", None
            
            # Poveži se ako nismo konektovani
            if not self.connect():
                return False, "Failed to connect to Pico", None
            
            # Pošalji komandu
            command = f"VERTICAL:{angle}\n"
            logger.info("Sending vertical servo command", angle=angle, command=command.strip())
            
            self.serial_conn.write(command.encode())
            self.serial_conn.flush()
            
            # Čekaj odgovor
            response = ""
            response_start = time.time()
            
            while (time.time() - response_start) < settings.servo_move_timeout:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode().strip()
                    response += data
                    
                    if response.startswith("OK:"):
                        self.last_command_time = datetime.now()
                        response_time = int((time.time() - start_time) * 1000)
                        logger.info("Vertical servo command successful", 
                                  angle=angle, 
                                  response_time_ms=response_time)
                        return True, None, response_time
                    elif response.startswith("ERROR:"):
                        error_msg = response.replace("ERROR:", "").strip()
                        logger.error("Vertical servo command failed", angle=angle, error=error_msg)
                        return False, error_msg, None
                
                time.sleep(0.01)
            
            # Timeout
            response_time = int((time.time() - start_time) * 1000)
            error_msg = "Timeout waiting for vertical servo response"
            logger.error("Vertical servo command timeout", 
                        angle=angle, 
                        timeout=settings.servo_move_timeout,
                        response_time_ms=response_time)
            return False, error_msg, response_time
            
        except serial.SerialException as e:
            error_msg = f"Serial communication error: {str(e)}"
            logger.error("Serial error", angle=angle, error=str(e))
            self.disconnect()
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("Unexpected vertical servo error", angle=angle, error=str(e))
            return False, error_msg, None

    def set_horizontal_angle(self, angle: int) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Postavi horizontal servo na zadati ugao
        :param angle: Ugao u stepenima (-20 to 20)
        :return: (success, error_message, response_time_ms)
        """
        start_time = time.time()
        
        try:
            # Validacija ugla
            if not (-20 <= angle <= 20):
                return False, "Horizontal angle must be between -20 and 20", None
            
            # Poveži se ako nismo konektovani
            if not self.connect():
                return False, "Failed to connect to Pico", None
            
            # Pošalji komandu
            command = f"HORIZONTAL:{angle}\n"
            logger.info("Sending horizontal servo command", angle=angle, command=command.strip())
            
            self.serial_conn.write(command.encode())
            self.serial_conn.flush()
            
            # Čekaj odgovor
            response = ""
            response_start = time.time()
            
            while (time.time() - response_start) < settings.servo_move_timeout:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode().strip()
                    response += data
                    
                    if response.startswith("OK:"):
                        self.last_command_time = datetime.now()
                        response_time = int((time.time() - start_time) * 1000)
                        logger.info("Horizontal servo command successful", 
                                  angle=angle, 
                                  response_time_ms=response_time)
                        return True, None, response_time
                    elif response.startswith("ERROR:"):
                        error_msg = response.replace("ERROR:", "").strip()
                        logger.error("Horizontal servo command failed", angle=angle, error=error_msg)
                        return False, error_msg, None
                
                time.sleep(0.01)
            
            # Timeout
            response_time = int((time.time() - start_time) * 1000)
            error_msg = "Timeout waiting for horizontal servo response"
            logger.error("Horizontal servo command timeout", 
                        angle=angle, 
                        timeout=settings.servo_move_timeout,
                        response_time_ms=response_time)
            return False, error_msg, response_time
            
        except serial.SerialException as e:
            error_msg = f"Serial communication error: {str(e)}"
            logger.error("Serial error", angle=angle, error=str(e))
            self.disconnect()
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("Unexpected horizontal servo error", angle=angle, error=str(e))
            return False, error_msg, None

    def set_material_position(self, material: str) -> Tuple[bool, Optional[str], Optional[int], Optional[dict]]:
        """
        Postavi servoe za zadati materijal sa kompletnom sekvencom
        :param material: Tip materijala (plastic, glass, pet, organic)
        :return: (success, error_message, response_time_ms, positions_used)
        """
        from .config import settings
        
        # Mapiranje materijala na pozicije
        material_positions = {
            "plastic": {"vertical": -90, "horizontal": -20},
            "glass": {"vertical": -90, "horizontal": 20},
            "pet": {"vertical": 90, "horizontal": -20},
            "organic": {"vertical": 90, "horizontal": 20}
        }
        
        start_time = time.time()
        
        try:
            # Validacija materijala
            if material not in material_positions:
                return False, f"Unknown material: {material}", None, None
            
            positions = material_positions[material]
            
            # Poveži se ako nismo konektovani
            if not self.connect():
                return False, "Failed to connect to Pico", None, None
            
            # Pošalji MATERIAL komandu
            command = f"MATERIAL:{material.lower()}\n"
            logger.info("Sending material command", material=material, positions=positions, command=command.strip())
            
            self.serial_conn.write(command.encode())
            self.serial_conn.flush()
            
            # Čekaj odgovor (duže zbog sekvencijalnog pokreta - 2.5s total)
            extended_timeout = settings.servo_move_timeout * 4  # 4x duže za kompletnu sekvencu (2.5s)
            response = ""
            response_start = time.time()
            
            while (time.time() - response_start) < extended_timeout:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode().strip()
                    response += data
                    
                    if response.startswith("OK:"):
                        self.last_command_time = datetime.now()
                        response_time = int((time.time() - start_time) * 1000)
                        logger.info("Material command successful", 
                                  material=material, 
                                  positions=positions,
                                  response_time_ms=response_time)
                        return True, None, response_time, positions
                    elif response.startswith("ERROR:"):
                        error_msg = response.replace("ERROR:", "").strip()
                        logger.error("Material command failed", material=material, error=error_msg)
                        return False, error_msg, None, None
                
                time.sleep(0.01)
            
            # Timeout
            response_time = int((time.time() - start_time) * 1000)
            error_msg = "Timeout waiting for material sequence completion"
            logger.error("Material command timeout", 
                        material=material, 
                        timeout=extended_timeout,
                        response_time_ms=response_time)
            return False, error_msg, response_time, None
            
        except serial.SerialException as e:
            error_msg = f"Serial communication error: {str(e)}"
            logger.error("Serial error", material=material, error=str(e))
            self.disconnect()
            return False, error_msg, None, None
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("Unexpected material error", material=material, error=str(e))
            return False, error_msg, None, None

    def return_to_base(self) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Vrati oba serva u baznu poziciju (0, 0)
        :return: (success, error_message, response_time_ms)
        """
        start_time = time.time()
        
        try:
            # Poveži se ako nismo konektovani
            if not self.connect():
                return False, "Failed to connect to Pico", None
            
            # Pošalji BASE komandu
            command = "BASE:0\n"
            logger.info("Sending base command", command=command.strip())
            
            self.serial_conn.write(command.encode())
            self.serial_conn.flush()
            
            # Čekaj odgovor
            response = ""
            response_start = time.time()
            
            while (time.time() - response_start) < settings.servo_move_timeout:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode().strip()
                    response += data
                    
                    if response.startswith("OK:"):
                        self.last_command_time = datetime.now()
                        response_time = int((time.time() - start_time) * 1000)
                        logger.info("Base command successful", response_time_ms=response_time)
                        return True, None, response_time
                    elif response.startswith("ERROR:"):
                        error_msg = response.replace("ERROR:", "").strip()
                        logger.error("Base command failed", error=error_msg)
                        return False, error_msg, None
                
                time.sleep(0.01)
            
            # Timeout
            response_time = int((time.time() - start_time) * 1000)
            error_msg = "Timeout waiting for base command response"
            logger.error("Base command timeout", 
                        timeout=settings.servo_move_timeout,
                        response_time_ms=response_time)
            return False, error_msg, response_time
            
        except serial.SerialException as e:
            error_msg = f"Serial communication error: {str(e)}"
            logger.error("Serial error", error=str(e))
            self.disconnect()
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("Unexpected base error", error=str(e))
            return False, error_msg, None

    def cleanup(self):
        """Čišćenje resursa"""
        self.disconnect()

# Globalna instanca kontrolera
servo_controller = ServoController()
