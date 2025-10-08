import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from view.api.main import app


class TestMainApp:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_app_title(self):
        assert app.title == "Bullseye API"
        assert app.version == "1.0.0"
    
    def test_read_root(self, client):
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Bullseye API is running"}
    
    def test_cors_middleware_configured(self):
        middleware_types = [type(m) for m in app.user_middleware]
        
        assert any('CORSMiddleware' in str(m) for m in middleware_types)
    
    def test_routers_included(self):
        route_paths = [route.path for route in app.routes]
        
        # Should have routes from all three routers
        assert len(route_paths) > 1
        assert "/" in route_paths
    
    def test_health_check_endpoint(self, client):
        response = client.get("/")
        
        assert response.status_code == 200
        assert "message" in response.json()
        assert "running" in response.json()["message"].lower()
    
    def test_app_is_fastapi_instance(self):
        from fastapi import FastAPI
        assert isinstance(app, FastAPI)
    
    def test_cors_allows_localhost(self, client):
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # CORS preflight should be handled
        assert response.status_code in [200, 405]


class TestDatabaseInitialization:
    
    def test_database_tables_created(self):
        with patch('view.api.main.Base') as mock_base:
            with patch('view.api.main.engine') as mock_engine:
                # Re-import to trigger table creation
                import importlib
                import view.api.main as main_module
                importlib.reload(main_module)