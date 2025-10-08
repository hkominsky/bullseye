import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.model.data_pipeline.data_manager import DataManager


class TestDataManager:
    
    @pytest.fixture
    def mock_dependencies(self):
        with patch('src.model.data_pipeline.data_manager.HttpClient'), \
             patch('src.model.data_pipeline.data_manager.FileCache'), \
             patch('src.model.data_pipeline.data_manager.TickerMappingService'), \
             patch('src.model.data_pipeline.data_manager.SECDataExtractor'), \
             patch('src.model.data_pipeline.data_manager.SECDataCleaner'), \
             patch('src.model.data_pipeline.data_manager.SECDataProcessor'), \
             patch('src.model.data_pipeline.data_manager.CorporateSentimentAnalyzer'), \
             patch('src.model.data_pipeline.data_manager.RetailSentimentAnalyzer'), \
             patch('src.model.data_pipeline.data_manager.TickerNews'), \
             patch('src.model.data_pipeline.data_manager.EarningsFetcher'), \
             patch('src.model.data_pipeline.data_manager.SectorPerformance'), \
             patch('src.model.data_pipeline.data_manager.EmailNotifier'), \
             patch('src.model.data_pipeline.data_manager.DataValidator'), \
             patch('src.model.data_pipeline.data_manager.DatabaseManager'), \
             patch('src.model.data_pipeline.data_manager.DataRepository'), \
             patch('src.model.data_pipeline.data_manager.LoggerSetup'), \
             patch('src.model.data_pipeline.data_manager.config'):
            yield
    
    @pytest.fixture
    def data_manager(self, mock_dependencies):
        return DataManager("TestAgent/1.0")
    
    def test_init(self, mock_dependencies):
        manager = DataManager("TestAgent/1.0")
        assert manager.http_client is not None
        assert manager.extractor is not None
        assert manager.cleaner is not None
        assert manager.processor is not None
    
    def test_extract_raw_data(self, data_manager):
        data_manager.extractor.extract_raw_financial_data = Mock(return_value=[{'revenue': 100000}])
        
        result = data_manager._extract_raw_data('AAPL', 8)
        
        assert len(result) == 1
        assert result[0]['revenue'] == 100000
    
    def test_extract_raw_data_empty(self, data_manager):
        data_manager.extractor.extract_raw_financial_data = Mock(return_value=[])
        
        result = data_manager._extract_raw_data('AAPL', 8)
        
        assert result == []
    
    def test_process_raw_records(self, data_manager):
        raw_records = [Mock()]
        data_manager.cleaner.clean_financial_records = Mock(return_value=raw_records)
        data_manager.processor.process_records_with_metrics = Mock(return_value=raw_records)
        
        result = data_manager._process_raw_records(raw_records, 'AAPL')
        
        assert 'AAPL' in result
        assert result['AAPL'] == raw_records
    
    def test_create_dataframes(self, data_manager):
        processed_records = {'AAPL': [Mock()]}
        raw_df = pd.DataFrame({'revenue': [100000]})
        metrics_df = pd.DataFrame({'margin': [25.0]})
        
        data_manager.processor.create_split_dataframes = Mock(return_value=(raw_df, metrics_df))
        data_manager.validator.clean_dataframe = Mock(side_effect=lambda x: x)
        
        result_raw, result_metrics = data_manager._create_dataframes(processed_records)
        
        assert not result_raw.empty
        assert not result_metrics.empty
    
    def test_get_cleaned_financial_data_success(self, data_manager):
        data_manager.extractor.extract_raw_financial_data = Mock(return_value=[{'revenue': 100000}])
        data_manager.cleaner.clean_financial_records = Mock(return_value=[Mock()])
        data_manager.processor.process_records_with_metrics = Mock(return_value=[Mock()])
        data_manager.processor.create_split_dataframes = Mock(return_value=(
            pd.DataFrame({'revenue': [100000]}),
            pd.DataFrame({'margin': [25.0]})
        ))
        data_manager.validator.clean_dataframe = Mock(side_effect=lambda x: x)
        
        raw_df, metrics_df = data_manager._get_cleaned_financial_data('AAPL', 8)
        
        assert not raw_df.empty
        assert not metrics_df.empty
    
    def test_get_cleaned_financial_data_no_records(self, data_manager):
        data_manager.extractor.extract_raw_financial_data = Mock(return_value=[])
        
        raw_df, metrics_df = data_manager._get_cleaned_financial_data('AAPL', 8)
        
        assert raw_df.empty
        assert metrics_df.empty
    
    def test_get_cleaned_financial_data_exception(self, data_manager):
        data_manager.extractor.extract_raw_financial_data = Mock(side_effect=Exception("API Error"))
        
        raw_df, metrics_df = data_manager._get_cleaned_financial_data('AAPL', 8)
        
        assert raw_df.empty
        assert metrics_df.empty
    
    def test_fetch_corporate_sentiment(self, data_manager):
        data_manager.corporate_sentiment_analyzer.fetch_sentiment = Mock(return_value=0.65)
        
        result = data_manager._fetch_corporate_sentiment('AAPL')
        
        assert result == 0.65
    
    def test_fetch_retail_sentiment(self, data_manager):
        result = data_manager._fetch_retail_sentiment('AAPL')
        
        assert result == -0.15
    
    def test_get_sentiment_data_success(self, data_manager):
        data_manager.corporate_sentiment_analyzer.fetch_sentiment = Mock(return_value=0.65)
        
        corporate, retail = data_manager._get_sentiment_data('AAPL')
        
        assert corporate == 0.65
        assert retail == -0.15
    
    def test_get_sentiment_data_exception(self, data_manager):
        data_manager.corporate_sentiment_analyzer.fetch_sentiment = Mock(side_effect=Exception("API Error"))
        
        corporate, retail = data_manager._get_sentiment_data('AAPL')
        
        assert corporate == 0.0
        assert retail == 0.0
    
    def test_create_default_sector_data(self, data_manager):
        result = data_manager._create_default_sector_data('AAPL')
        
        assert result['ticker'] == 'AAPL'
        assert result['sector'] == 'Unknown'
        assert result['sector_etf'] == 'N/A'
    
    def test_get_sector_performance_success(self, data_manager):
        mock_analyzer = Mock()
        mock_analyzer.get_sector_performance = Mock(return_value={'ticker': 'AAPL', 'sector': 'Technology'})
        data_manager.sector_analyzer = Mock(return_value=mock_analyzer)
        
        result = data_manager._get_sector_performance('AAPL')
        
        assert result['ticker'] == 'AAPL'
        assert result['sector'] == 'Technology'
    
    def test_get_sector_performance_exception(self, data_manager):
        data_manager.sector_analyzer = Mock(side_effect=Exception("API Error"))
        
        result = data_manager._get_sector_performance('AAPL')
        
        assert result['sector'] == 'Unknown'
    
    def test_collect_all_ticker_data_success(self, data_manager):
        progress_tracker = Mock()
        progress_tracker.step = Mock()
        
        data_manager.corporate_sentiment_analyzer.fetch_sentiment = Mock(return_value=0.65)
        data_manager.ticker_news.get_ticker_news = Mock(return_value=pd.DataFrame({'headline': ['test']}))
        
        mock_analyzer = Mock()
        mock_analyzer.get_sector_performance = Mock(return_value={'sector': 'Technology'})
        data_manager.sector_analyzer = Mock(return_value=mock_analyzer)
        
        data_manager.quarterly_earnings.fetch_earnings = Mock(return_value=pd.DataFrame({'eps': [1.5]}))
        data_manager.quarterly_earnings.fetch_next_earnings = Mock(return_value={'nextEarningsDate': '2024-07-01'})
        data_manager.extractor.extract_raw_financial_data = Mock(return_value=[{'revenue': 100000}])
        data_manager.cleaner.clean_financial_records = Mock(return_value=[Mock()])
        data_manager.processor.process_records_with_metrics = Mock(return_value=[Mock()])
        data_manager.processor.create_split_dataframes = Mock(return_value=(
            pd.DataFrame({'revenue': [100000]}),
            pd.DataFrame({'margin': [25.0]})
        ))
        data_manager.validator.clean_dataframe = Mock(side_effect=lambda x: x)
        
        data_package, success = data_manager.collect_all_ticker_data('AAPL', progress_tracker)
        
        assert success == True
        assert 'corporate_sentiment' in data_package
        assert 'raw_df' in data_package
    
    def test_collect_all_ticker_data_exception(self, data_manager):
        progress_tracker = Mock()
        data_manager.corporate_sentiment_analyzer.fetch_sentiment = Mock(side_effect=Exception("Error"))
        
        data_package, success = data_manager.collect_all_ticker_data('AAPL', progress_tracker)
        
        assert success == False
        assert data_package == {}
    
    def test_validate_data_package(self, data_manager):
        data_package = {
            'corporate_sentiment': 0.5,
            'retail_sentiment': 0.3,
            'ticker_news_df': pd.DataFrame({'headline': ['test']}),
            'sector_performance_data': {'sector': 'Technology'},
            'earnings_df': pd.DataFrame({'eps': [1.5]}),
            'raw_df': pd.DataFrame({'revenue': [100000]}),
            'metrics_df': pd.DataFrame({'margin': [25.0]})
        }
        
        data_manager.validator.validate_ticker_data_package = Mock(return_value=(True, ""))
        
        is_valid, msg = data_manager._validate_data_package('AAPL', data_package)
        
        assert is_valid == True
    
    def test_save_ticker_data(self, data_manager):
        data_package = {}
        data_manager.repository.save_complete_ticker_data = Mock(return_value=(True, ""))
        
        success, msg = data_manager._save_ticker_data('AAPL', data_package)
        
        assert success == True
    
    def test_generate_notification_data_hash(self, data_manager):
        data_package = {
            'corporate_sentiment': 0.5,
            'retail_sentiment': 0.3,
            'ticker_news_df': pd.DataFrame(),
            'sector_performance_data': {},
            'earnings_df': pd.DataFrame(),
            'earnings_estimate': {},
            'raw_df': pd.DataFrame(),
            'metrics_df': pd.DataFrame()
        }
        
        data_manager.repository.generate_data_hash = Mock(return_value='abc123')
        
        hash_result = data_manager._generate_notification_data_hash('AAPL', data_package)
        
        assert hash_result == 'abc123'
    
    def test_send_notification(self, data_manager):
        data_package = {
            'corporate_sentiment': 0.5,
            'retail_sentiment': 0.3,
            'ticker_news_df': pd.DataFrame(),
            'sector_performance_data': {},
            'raw_df': pd.DataFrame(),
            'metrics_df': pd.DataFrame(),
            'earnings_df': pd.DataFrame(),
            'earnings_estimate': {}
        }
        
        data_manager.notifier.send_email = Mock()
        
        data_manager._send_notification('AAPL', data_package)
        
        data_manager.notifier.send_email.assert_called_once()
    
    def test_log_success(self, data_manager):
        data_manager.repository.log_processing_result = Mock(return_value=True)
        
        with patch('src.model.data_pipeline.data_manager.config', return_value='test@example.com'):
            data_manager._log_success('AAPL', 60, 'abc123')
        
        data_manager.repository.log_processing_result.assert_called_once()
    
    def test_get_processing_steps(self, data_manager):
        steps = data_manager.get_processing_steps()
        
        assert len(steps) == 9
        assert "Retrieving sentiment data" in steps
        assert "Sending email notification" in steps
    
    def test_get_latest_data_summary(self, data_manager):
        data_manager.repository.get_latest_data_summary = Mock(return_value={'ticker': 'AAPL'})
        
        result = data_manager.get_latest_data_summary('AAPL')
        
        assert result['ticker'] == 'AAPL'
    
    def test_del_closes_db_connection(self, data_manager):
        data_manager.db_manager.close_pool = Mock()
        
        data_manager.__del__()
        
        data_manager.db_manager.close_pool.assert_called_once()
    
    def test_del_handles_exception(self, data_manager):
        data_manager.db_manager.close_pool = Mock(side_effect=Exception("Error"))
        
        data_manager.__del__()