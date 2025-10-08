import pytest
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager
from src.model.data_pipeline.database.db_manager import DatabaseManager


class TestDatabaseManager:
    
    @pytest.fixture
    def mock_config(self):
        with patch('src.model.data_pipeline.database.db_manager.config') as mock:
            mock.side_effect = lambda key, default=None, cast=None: {
                'DB_HOST': 'localhost',
                'DB_PORT': 5432,
                'DB_NAME': 'test_db',
                'DB_USER': 'test_user',
                'DB_PASSWORD': 'test_pass',
                'DB_POOL_SIZE': 10
            }.get(key, default)
            yield mock
    
    @pytest.fixture
    def mock_pool(self):
        with patch('src.model.data_pipeline.database.db_manager.ThreadedConnectionPool') as mock:
            pool_instance = Mock()
            mock.return_value = pool_instance
            yield pool_instance
    
    @pytest.fixture
    def db_manager(self, mock_config, mock_pool):
        with patch('src.model.data_pipeline.database.db_manager.LoggerSetup'):
            return DatabaseManager()
    
    def test_init_success(self, mock_config, mock_pool):
        with patch('src.model.data_pipeline.database.db_manager.LoggerSetup'):
            manager = DatabaseManager()
            assert manager._pool is not None
    
    def test_initialize_pool_with_config(self, mock_config, mock_pool):
        with patch('src.model.data_pipeline.database.db_manager.LoggerSetup'):
            with patch('src.model.data_pipeline.database.db_manager.ThreadedConnectionPool') as mock_thread_pool:
                DatabaseManager()
                
                mock_thread_pool.assert_called_once()
                call_kwargs = mock_thread_pool.call_args[1]
                assert call_kwargs['host'] == 'localhost'
                assert call_kwargs['port'] == 5432
                assert call_kwargs['database'] == 'test_db'
                assert call_kwargs['user'] == 'test_user'
                assert call_kwargs['password'] == 'test_pass'
                assert call_kwargs['minconn'] == 1
                assert call_kwargs['maxconn'] == 10
    
    def test_initialize_pool_failure(self, mock_config):
        with patch('src.model.data_pipeline.database.db_manager.LoggerSetup'):
            with patch('src.model.data_pipeline.database.db_manager.ThreadedConnectionPool', side_effect=Exception("Connection failed")):
                with pytest.raises(Exception, match="Connection failed"):
                    DatabaseManager()
    
    def test_get_connection_success(self, db_manager, mock_pool):
        mock_conn = Mock()
        mock_pool.getconn.return_value = mock_conn
        
        with db_manager.get_connection() as conn:
            assert conn == mock_conn
            assert conn.autocommit == False
        
        mock_pool.getconn.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)
    
    def test_get_connection_with_exception(self, db_manager, mock_pool):
        mock_conn = Mock()
        mock_pool.getconn.return_value = mock_conn
        
        with pytest.raises(ValueError):
            with db_manager.get_connection() as conn:
                raise ValueError("Test error")
        
        mock_conn.rollback.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)
    
    def test_get_connection_returns_connection_to_pool(self, db_manager, mock_pool):
        mock_conn = Mock()
        mock_pool.getconn.return_value = mock_conn
        
        with db_manager.get_connection() as conn:
            pass
        
        mock_pool.putconn.assert_called_once_with(mock_conn)
    
    def test_get_connection_no_rollback_on_success(self, db_manager, mock_pool):
        mock_conn = Mock()
        mock_pool.getconn.return_value = mock_conn
        
        with db_manager.get_connection() as conn:
            pass
        
        mock_conn.rollback.assert_not_called()
    
    def test_test_connection_success(self, db_manager, mock_pool):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        mock_pool.getconn.return_value = mock_conn
        
        result = db_manager.test_connection()
        
        assert result == True
        mock_cursor.execute.assert_called_once_with('SELECT 1')
    
    def test_test_connection_failure(self, db_manager, mock_pool):
        mock_pool.getconn.side_effect = Exception("Connection failed")
        
        result = db_manager.test_connection()
        
        assert result == False
    
    def test_test_connection_no_result(self, db_manager, mock_pool):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_pool.getconn.return_value = mock_conn
        
        result = db_manager.test_connection()
        
        assert result == False
    
    def test_close_pool(self, db_manager, mock_pool):
        db_manager.close_pool()
        
        mock_pool.closeall.assert_called_once()
    
    def test_close_pool_when_none(self, db_manager):
        db_manager._pool = None
        db_manager.close_pool()
    
    def test_del_calls_close_pool(self, mock_config, mock_pool):
        with patch('src.model.data_pipeline.database.db_manager.LoggerSetup'):
            manager = DatabaseManager()
            manager.__del__()
            
            mock_pool.closeall.assert_called()
    
    def test_del_handles_exception(self, db_manager, mock_pool):
        mock_pool.closeall.side_effect = Exception("Close failed")
        
        db_manager.__del__()
    
    def test_get_connection_sets_autocommit_false(self, db_manager, mock_pool):
        mock_conn = Mock()
        mock_pool.getconn.return_value = mock_conn
        
        with db_manager.get_connection() as conn:
            assert conn.autocommit == False
    
    def test_multiple_connections(self, db_manager, mock_pool):
        mock_conn1 = Mock()
        mock_conn2 = Mock()
        mock_pool.getconn.side_effect = [mock_conn1, mock_conn2]
        
        with db_manager.get_connection() as conn1:
            assert conn1 == mock_conn1
        
        with db_manager.get_connection() as conn2:
            assert conn2 == mock_conn2
        
        assert mock_pool.getconn.call_count == 2
        assert mock_pool.putconn.call_count == 2
    
    def test_connection_rollback_on_exception_only(self, db_manager, mock_pool):
        mock_conn = Mock()
        mock_pool.getconn.return_value = mock_conn
        
        try:
            with db_manager.get_connection() as conn:
                conn.execute("SOME SQL")
                raise RuntimeError("Error during operation")
        except RuntimeError:
            pass
        
        mock_conn.rollback.assert_called_once()
    
    def test_get_connection_context_manager_protocol(self, db_manager, mock_pool):
        mock_conn = Mock()
        mock_pool.getconn.return_value = mock_conn
        
        ctx = db_manager.get_connection()
        
        entered_conn = ctx.__enter__()
        assert entered_conn == mock_conn
        
        ctx.__exit__(None, None, None)
        mock_pool.putconn.assert_called_once()
    
    def test_config_uses_defaults(self):
        with patch('src.model.data_pipeline.database.db_manager.LoggerSetup'):
            with patch('src.model.data_pipeline.database.db_manager.config') as mock_cfg:
                with patch('src.model.data_pipeline.database.db_manager.ThreadedConnectionPool'):
                    def config_side_effect(key, default=None, cast=None):
                        if key == 'DB_PORT':
                            return 5432
                        elif key == 'DB_POOL_SIZE':
                            return 10
                        return 'test_value'
                    
                    mock_cfg.side_effect = config_side_effect
                    
                    DatabaseManager()
                    
                    assert mock_cfg.call_count >= 5