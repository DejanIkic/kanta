"""
Testovi za FastAPI endpointe
Autor: AI Assistant
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

from rpi_api.main import app
from rpi_api.models import ServoMovement

# Test client
client = TestClient(app)

@pytest.fixture
def mock_servo_controller():
    """Mock za servo kontroler"""
    with patch('rpi_api.main.servo_controller') as mock:
        yield mock

@pytest.fixture
def mock_db():
    """Mock za database session"""
    with patch('rpi_api.main.get_db') as mock:
        yield mock

class TestRootEndpoint:
    """Testovi za root endpoint"""
    
    def test_root_endpoint(self):
        """Test root endpoint vraća osnovne informacije"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "RPi Pico Servo Control API"
        assert "version" in data
        assert data["status"] == "running"

class TestHealthEndpoint:
    """Testovi za health check endpoint"""
    
    def test_health_check_healthy(self):
        """Test health check kad je sve healthy"""
        with patch('rpi_api.main.check_db_health', return_value=True), \
             patch('rpi_api.main.servo_controller') as mock_controller:
            
            mock_controller.get_status.return_value = (True, None, 0)
            
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database"] == "healthy"
            assert data["pico_connected"] == True
    
    def test_health_check_unhealthy(self):
        """Test health check kad nije sve healthy"""
        with patch('rpi_api.main.check_db_health', return_value=False), \
             patch('rpi_api.main.servo_controller') as mock_controller:
            
            mock_controller.get_status.return_value = (False, None, 3)
            
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database"] == "unhealthy"
            assert data["pico_connected"] == False

class TestServoEndpoints:
    """Testovi za servo kontrolne endpointe"""
    
    def test_set_servo_angle_success(self, mock_servo_controller, mock_db):
        """Test uspešnog postavljanja ugla serva"""
        # Mock servo controller response
        mock_servo_controller.set_angle.return_value = (True, None, 150)
        
        # Mock database session
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        # Mock database operations
        mock_movement = ServoMovement(
            id=1,
            angle=20,
            timestamp=datetime.now(),
            success=True,
            response_time_ms=150
        )
        mock_db_instance.add.return_value = None
        mock_db_instance.commit.return_value = None
        mock_db_instance.refresh.return_value = None
        
        response = client.post("/api/servo/right")
        assert response.status_code == 200
        
        data = response.json()
        assert data["angle"] == 20
        assert data["success"] == True
        assert data["response_time_ms"] == 150
        
        # Proveri da je servo controller pozvan
        mock_servo_controller.set_angle.assert_called_once_with(20)
    
    def test_set_servo_angle_failure(self, mock_servo_controller, mock_db):
        """Test neuspešnog postavljanja ugla serva"""
        # Mock servo controller response
        mock_servo_controller.set_angle.return_value = (False, "Pico not connected", None)
        
        # Mock database session
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_movement = ServoMovement(
            id=1,
            angle=90,
            timestamp=datetime.now(),
            success=False,
            error_message="Pico not connected"
        )
        mock_db_instance.add.return_value = None
        mock_db_instance.commit.return_value = None
        mock_db_instance.refresh.return_value = None
        
        response = client.post("/api/servo/ltrs")
        assert response.status_code == 422
        
        data = response.json()
        assert "left" in data["detail"]
    
    def test_set_servo_angle_invalid_angle(self, mock_servo_controller, mock_db):
        """Test nevalidnog ugla serva"""
        # Mock servo controller to avoid actual serial calls
        mock_servo_controller.set_angle.return_value = (False, "Side must be left or right", None)

        response = client.post("/api/servo/rrr")  # Ugao pogresan
        assert response.status_code == 422  # Validation error
    
    def test_get_servo_status(self, mock_servo_controller, mock_db):
        """Test dobijanja statusa serva"""
        # Mock servo controller
        mock_servo_controller.get_status.return_value = (True, datetime.now(), 0)
        
        # Mock database
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.query.return_value.count.return_value = 10
        mock_db_instance.query.return_value.filter.return_value.count.return_value = 1
        
        response = client.get("/api/servo/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["connected"] == True
        assert data["total_movements"] == 10
        assert data["error_rate"] == 10.0  # 1/10 * 100
    
    def test_get_servo_history(self, mock_db):
        """Test dobijanja istorije pokreta"""
        # Mock database
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        # Mock query chain
        mock_query = Mock()
        mock_db_instance.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db_instance.query.return_value.count.return_value = 5
        
        response = client.get("/api/servo/history")
        assert response.status_code == 200
        
        data = response.json()
        assert "movements" in data
        assert data["total_count"] == 5
    
    def test_get_servo_history_limit(self, mock_db):
        """Test dobijanja istorije sa limitom"""
        # Mock database
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_query = Mock()
        mock_db_instance.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db_instance.query.return_value.count.return_value = 3
        
        response = client.get("/api/servo/history/50")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_count"] == 3
    
    def test_get_servo_history_invalid_limit(self):
        """Test istorije sa nevalidnim limitom"""
        response = client.get("/api/servo/history/1500")  # Preko maksimuma
        assert response.status_code == 400
        
        response = client.get("/api/servo/history/0")  # Ispod minimuma
        assert response.status_code == 400

class TestErrorHandling:
    """Testovi za error handling"""
    
    def test_global_exception_handler(self):
        """Test global exception handler"""
        with patch('rpi_api.main.check_db_health', side_effect=Exception("Test error")):
            response = client.get("/health")
            assert response.status_code == 500

if __name__ == "__main__":
    pytest.main([__file__])
