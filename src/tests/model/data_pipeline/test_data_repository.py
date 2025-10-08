import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.model.data_pipeline.database.data_repository import DataRepository


class TestDataRepository:
    
    @pytest.fixture
    def mock_db_manager(self):
        manager = Mock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        manager.get_connection.return_value = mock_conn
        return manager
    
    @pytest.fixture
    def repository(self, mock_db_manager):
        with patch('src.model.data_pipeline.database.data_repository.LoggerSetup'):
            return DataRepository(mock_db_manager)
    
    @pytest.fixture
    def sample_data_package(self):
        return {
            'sector_performance_data': {
                'company_name': 'Apple Inc.',
                'sector': 'Technology',
                'sector_etf': 'XLK',
                'ticker_1y_performance_pct': 25.5,
                'sector_1y_performance_pct': 15.3
            },
            'corporate_sentiment': 0.65,
            'retail_sentiment': 0.45,
            'ticker_news_df': pd.DataFrame({
                'headline': ['News 1', 'News 2'],
                'summary': ['Summary 1', 'Summary 2'],
                'url': ['http://url1.com', 'http://url2.com'],
                'published_at': [datetime(2024, 1, 1), datetime(2024, 1, 2)]
            }),
            'earnings_df': pd.DataFrame({
                'fiscalDateEnding': ['2024-01-01', '2024-04-01'],
                'reportedEPS': [1.5, 1.6],
                'estimatedEPS': [1.4, 1.5],
                'surprisePercentage': [7.14, 6.67],
                'oneDayReturn': [2.5, 3.0],
                'fiveDayReturn': [5.0, 6.0]
            }),
            'earnings_estimate': {
                'nextEarningsDate': '2024-07-01',
                'estimatedEPS': 1.7,
                'forwardPE': 25.5,
                'pegRatio': 1.8
            },
            'raw_df': pd.DataFrame({
                'date': ['2024-01-01'],
                'period': ['Q1 2024'],
                'form_type': ['10-Q'],
                'revenue': [100000],
                'cost_of_revenue': [60000],
                'gross_profit': [40000],
                'operating_income': [25000],
                'net_income': [20000],
                'total_assets': [300000],
                'current_assets': [150000],
                'cash_and_equivalents': [50000],
                'total_liabilities': [120000],
                'current_liabilities': [80000],
                'shareholders_equity': [180000]
            }),
            'metrics_df': pd.DataFrame({
                'period': ['Q1 2024'],
                'working_capital': [70000],
                'asset_turnover': [0.33],
                'altman_z_score': [3.5],
                'piotroski_f_score': [7],
                'gross_margin': [40.0],
                'operating_margin': [25.0],
                'net_margin': [20.0],
                'current_ratio': [1.875],
                'quick_ratio': [1.75],
                'debt_to_equity': [0.67],
                'return_on_assets': [6.67],
                'return_on_equity': [11.11],
                'free_cash_flow': [25000],
                'earnings_per_share': [20.0]
            })
        }
    
    def test_init(self, mock_db_manager):
        with patch('src.model.data_pipeline.database.data_repository.LoggerSetup'):
            repo = DataRepository(mock_db_manager)
            assert repo.db_manager == mock_db_manager
            assert repo.validator is not None
    
    def test_save_complete_ticker_data_success(self, repository, mock_db_manager, sample_data_package):
        success, error_msg = repository.save_complete_ticker_data('AAPL', sample_data_package)
        
        assert success == True
        assert error_msg == ""
        mock_db_manager.get_connection.assert_called_once()
    
    def test_save_complete_ticker_data_failure(self, repository, mock_db_manager, sample_data_package):
        mock_conn = mock_db_manager.get_connection.return_value.__enter__.return_value
        mock_conn.cursor.return_value.__enter__.return_value.execute.side_effect = Exception("DB Error")
        
        success, error_msg = repository.save_complete_ticker_data('AAPL', sample_data_package)
        
        assert success == False
        assert "Failed to save complete ticker data" in error_msg
    
    def test_save_ticker_info(self, repository, sample_data_package):
        mock_cursor = Mock()
        
        repository._save_ticker_info(mock_cursor, 'AAPL', sample_data_package)
        
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        assert 'INSERT INTO tickers' in call_args[0]
        assert call_args[1][0] == 'AAPL'
    
    def test_save_sentiment_data(self, repository, sample_data_package):
        mock_cursor = Mock()
        
        repository._save_sentiment_data(mock_cursor, 'AAPL', sample_data_package)
        
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        assert 'INSERT INTO sentiment_data' in call_args[0]
        assert call_args[1][0] == 'AAPL'
    
    def test_save_sector_performance(self, repository, sample_data_package):
        mock_cursor = Mock()
        
        repository._save_sector_performance(mock_cursor, 'AAPL', sample_data_package)
        
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        assert 'INSERT INTO sector_performance' in call_args[0]
    
    def test_save_news_articles_with_data(self, repository, sample_data_package):
        mock_cursor = Mock()
        
        with patch('src.model.data_pipeline.database.data_repository.execute_values') as mock_execute:
            repository._save_news_articles(mock_cursor, 'AAPL', sample_data_package)
            mock_execute.assert_called_once()
    
    def test_save_news_articles_empty_dataframe(self, repository):
        mock_cursor = Mock()
        data_package = {'ticker_news_df': pd.DataFrame()}
        
        repository._save_news_articles(mock_cursor, 'AAPL', data_package)
        
        mock_cursor.execute.assert_not_called()
    
    def test_save_earnings_data_with_data(self, repository, sample_data_package):
        mock_cursor = Mock()
        
        with patch('src.model.data_pipeline.database.data_repository.execute_values') as mock_execute:
            repository._save_earnings_data(mock_cursor, 'AAPL', sample_data_package)
            mock_execute.assert_called_once()
    
    def test_save_earnings_data_empty_dataframe(self, repository):
        mock_cursor = Mock()
        data_package = {'earnings_df': pd.DataFrame()}
        
        repository._save_earnings_data(mock_cursor, 'AAPL', data_package)
        
        mock_cursor.execute.assert_not_called()
    
    def test_save_earnings_estimates_with_data(self, repository, sample_data_package):
        mock_cursor = Mock()
        
        repository._save_earnings_estimates(mock_cursor, 'AAPL', sample_data_package)
        
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        assert 'INSERT INTO earnings_estimates' in call_args[0]
    
    def test_save_earnings_estimates_no_data(self, repository):
        mock_cursor = Mock()
        data_package = {'earnings_estimate': {}}
        
        repository._save_earnings_estimates(mock_cursor, 'AAPL', data_package)
        
        mock_cursor.execute.assert_not_called()
    
    def test_save_earnings_estimates_no_date(self, repository):
        mock_cursor = Mock()
        data_package = {'earnings_estimate': {'estimatedEPS': 1.5}}
        
        repository._save_earnings_estimates(mock_cursor, 'AAPL', data_package)
        
        mock_cursor.execute.assert_not_called()
    
    def test_save_raw_financial_data_with_data(self, repository, sample_data_package):
        mock_cursor = Mock()
        
        with patch('src.model.data_pipeline.database.data_repository.execute_values') as mock_execute:
            repository._save_raw_financial_data(mock_cursor, 'AAPL', sample_data_package)
            mock_execute.assert_called_once()
    
    def test_save_raw_financial_data_empty_dataframe(self, repository):
        mock_cursor = Mock()
        data_package = {'raw_df': pd.DataFrame()}
        
        repository._save_raw_financial_data(mock_cursor, 'AAPL', data_package)
        
        mock_cursor.execute.assert_not_called()
    
    def test_save_financial_metrics_with_data(self, repository, sample_data_package):
        mock_cursor = Mock()
        
        with patch('src.model.data_pipeline.database.data_repository.execute_values') as mock_execute:
            repository._save_financial_metrics(mock_cursor, 'AAPL', sample_data_package)
            mock_execute.assert_called_once()
    
    def test_save_financial_metrics_empty_dataframe(self, repository):
        mock_cursor = Mock()
        data_package = {'metrics_df': pd.DataFrame()}
        
        repository._save_financial_metrics(mock_cursor, 'AAPL', data_package)
        
        mock_cursor.execute.assert_not_called()
    
    def test_log_processing_result_success(self, repository, mock_db_manager):
        result = repository.log_processing_result(
            'AAPL', 'test@example.com', 60, 'abc123', 'SUCCESS'
        )
        
        assert result == True
        mock_db_manager.get_connection.assert_called()
    
    def test_log_processing_result_with_error(self, repository, mock_db_manager):
        result = repository.log_processing_result(
            'AAPL', 'test@example.com', 60, 'abc123', 'FAILED', 'Error message'
        )
        
        assert result == True
    
    def test_log_processing_result_failure(self, repository, mock_db_manager):
        mock_conn = mock_db_manager.get_connection.return_value.__enter__.return_value
        mock_conn.cursor.return_value.__enter__.return_value.execute.side_effect = Exception("DB Error")
        
        result = repository.log_processing_result(
            'AAPL', 'test@example.com', 60, 'abc123', 'SUCCESS'
        )
        
        assert result == False
    
    def test_get_latest_data_summary_success(self, repository, mock_db_manager):
        mock_cursor = mock_db_manager.get_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {
            'ticker': 'AAPL',
            'company_name': 'Apple Inc.',
            'sector': 'Technology',
            'corporate_sentiment': 0.65,
            'news_count': 5,
            'historical_earnings_count': 4,
            'financial_periods': 8,
            'metrics_periods': 8
        }
        
        result = repository.get_latest_data_summary('AAPL')
        
        assert result['ticker'] == 'AAPL'
        assert 'data_completeness' in result
    
    def test_get_latest_data_summary_not_found(self, repository, mock_db_manager):
        mock_cursor = mock_db_manager.get_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = None
        
        result = repository.get_latest_data_summary('INVALID')
        
        assert result['ticker'] == 'INVALID'
        assert result['status'] == 'not_found'
    
    def test_get_latest_data_summary_error(self, repository, mock_db_manager):
        mock_db_manager.get_connection.side_effect = Exception("DB Error")
        
        result = repository.get_latest_data_summary('AAPL')
        
        assert result['status'] == 'error'
        assert 'error' in result
    
    def test_calculate_completeness_all_complete(self, repository):
        summary = {
            'company_name': 'Apple Inc.',
            'corporate_sentiment': 0.65,
            'ticker_1y_performance_pct': 25.5,
            'news_count': 5,
            'historical_earnings_count': 4,
            'financial_periods': 8,
            'metrics_periods': 8,
            'last_email_sent': datetime.now()
        }
        
        result = repository._calculate_completeness(summary)
        
        assert result['has_ticker_info'] == True
        assert result['has_sentiment'] == True
        assert result['has_performance'] == True
        assert result['has_news'] == True
        assert result['has_earnings'] == True
        assert result['has_financials'] == True
        assert result['has_metrics'] == True
        assert result['recent_processing'] == True
    
    def test_calculate_completeness_partial(self, repository):
        summary = {
            'company_name': 'Apple Inc.',
            'corporate_sentiment': None,
            'news_count': 0,
            'historical_earnings_count': 4
        }
        
        result = repository._calculate_completeness(summary)
        
        assert result['has_ticker_info'] == True
        assert result['has_sentiment'] == False
        assert result['has_news'] == False
        assert result['has_earnings'] == True
    
    def test_generate_data_hash_simple(self):
        components = ['AAPL', 100, 'test']
        
        hash1 = DataRepository.generate_data_hash(components)
        hash2 = DataRepository.generate_data_hash(components)
        
        assert hash1 == hash2
        assert len(hash1) == 64
    
    def test_generate_data_hash_with_dataframe(self):
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        components = ['AAPL', df]
        
        hash_result = DataRepository.generate_data_hash(components)
        
        assert len(hash_result) == 64
    
    def test_generate_data_hash_with_dict(self):
        data = {'key1': 'value1', 'key2': 'value2'}
        components = ['AAPL', data]
        
        hash_result = DataRepository.generate_data_hash(components)
        
        assert len(hash_result) == 64
    
    def test_generate_data_hash_empty_dataframe(self):
        df = pd.DataFrame()
        components = ['AAPL', df]
        
        hash_result = DataRepository.generate_data_hash(components)
        
        assert len(hash_result) == 64
    
    def test_generate_data_hash_deterministic(self):
        df = pd.DataFrame({'b': [1, 2], 'a': [3, 4]})
        components1 = ['AAPL', df]
        components2 = ['AAPL', df.copy()]
        
        hash1 = DataRepository.generate_data_hash(components1)
        hash2 = DataRepository.generate_data_hash(components2)
        
        assert hash1 == hash2
    
    def test_generate_data_hash_exception_handling(self):
        class UnserializableObject:
            pass
        
        components = [UnserializableObject()]
        
        hash_result = DataRepository.generate_data_hash(components)
        
        assert len(hash_result) == 64
    
    def test_normalize_data_components_dataframe(self):
        df = pd.DataFrame({'b': [1], 'a': [2]})
        components = [df]
        
        result = DataRepository._normalize_data_components(components)
        
        assert isinstance(result[0], list)
    
    def test_normalize_data_components_dict(self):
        data = {'z': 1, 'a': 2}
        components = [data]
        
        result = DataRepository._normalize_data_components(components)
        
        assert list(result[0].keys()) == ['a', 'z']
    
    def test_normalize_data_components_mixed(self):
        df = pd.DataFrame({'a': [1]})
        data = {'key': 'value'}
        components = ['AAPL', df, data, 123]
        
        result = DataRepository._normalize_data_components(components)
        
        assert len(result) == 4
        assert result[0] == 'AAPL'
        assert result[3] == 123
    
    def test_fetch_ticker_summary(self, repository):
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {'ticker': 'AAPL', 'company_name': 'Apple Inc.'}
        
        result = repository._fetch_ticker_summary(mock_cursor, 'AAPL')
        
        mock_cursor.execute.assert_called_once()
        assert result['ticker'] == 'AAPL'