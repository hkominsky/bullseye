import pytest
import requests
from unittest.mock import Mock, patch
from datetime import datetime
from src.model.data_pipeline.sec_data_extractor import SECDataExtractor
from src.model.utils.models import FinancialRecord


class TestSECDataExtractor:
    
    @pytest.fixture
    def mock_http_client(self):
        return Mock()
    
    @pytest.fixture
    def ticker_mapping(self):
        return {
            'AAPL': '0000320193',
            'MSFT': '0000789019',
            'GOOGL': '0001652044'
        }
    
    @pytest.fixture
    def extractor(self, mock_http_client, ticker_mapping):
        with patch('src.model.data_pipeline.sec_data_extractor.LoggerSetup'):
            return SECDataExtractor(mock_http_client, ticker_mapping)
    
    @pytest.fixture
    def sample_sec_response(self):
        return {
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {
                                    "end": "2024-01-01",
                                    "val": 100000000,
                                    "form": "10-Q",
                                    "frame": "CY2024Q1"
                                }
                            ]
                        }
                    },
                    "NetIncomeLoss": {
                        "units": {
                            "USD": [
                                {
                                    "end": "2024-01-01",
                                    "val": 20000000,
                                    "form": "10-Q",
                                    "frame": "CY2024Q1"
                                }
                            ]
                        }
                    },
                    "Assets": {
                        "units": {
                            "USD": [
                                {
                                    "end": "2024-01-01",
                                    "val": 500000000,
                                    "form": "10-Q",
                                    "frame": "CY2024Q1"
                                }
                            ]
                        }
                    }
                }
            }
        }
    
    def test_init(self, mock_http_client, ticker_mapping):
        with patch('src.model.data_pipeline.sec_data_extractor.LoggerSetup'):
            extractor = SECDataExtractor(mock_http_client, ticker_mapping)
            assert extractor.http_client == mock_http_client
            assert extractor.ticker_mapping == ticker_mapping
    
    def test_get_cik_valid_ticker(self, extractor):
        cik = extractor._get_cik('AAPL')
        assert cik == '0000320193'
    
    def test_get_cik_invalid_ticker(self, extractor):
        with pytest.raises(ValueError, match="Unknown ticker"):
            extractor._get_cik('INVALID')
    
    def test_extract_raw_financial_data_success(self, extractor, mock_http_client, sample_sec_response):
        mock_response = Mock()
        mock_response.json.return_value = sample_sec_response
        mock_http_client.get.return_value = mock_response
        
        records = extractor.extract_raw_financial_data('AAPL', limit=8)
        
        assert len(records) == 1
        assert records[0].ticker == 'AAPL'
        assert records[0].revenue == 100000000
        assert records[0].net_income == 20000000
        mock_http_client.get.assert_called_once()
    
    def test_extract_raw_financial_data_http_error(self, extractor, mock_http_client):
        mock_http_client.get.side_effect = requests.RequestException("API Error")
        
        records = extractor.extract_raw_financial_data('AAPL')
        
        assert records == []
    
    def test_extract_raw_financial_data_invalid_ticker(self, extractor):
        records = extractor.extract_raw_financial_data('INVALID')
        assert records == []
    
    def test_extract_raw_financial_data_parsing_error(self, extractor, mock_http_client):
        mock_response = Mock()
        mock_response.json.return_value = {"invalid": "data"}
        mock_http_client.get.return_value = mock_response
        
        records = extractor.extract_raw_financial_data('AAPL')
        
        assert records == []
    
    def test_parse_facts_to_records_no_us_gaap(self, extractor):
        facts = {"facts": {}}
        records = extractor._parse_facts_to_records('AAPL', facts, 8)
        assert records == []
    
    def test_parse_facts_to_records_no_facts(self, extractor):
        facts = {}
        records = extractor._parse_facts_to_records('AAPL', facts, 8)
        assert records == []
    
    def test_parse_facts_to_records_with_limit(self, extractor):
        facts = {
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {"end": f"2024-0{i}-01", "val": 100000000 + i, "form": "10-Q", "frame": f"CY2024Q{i}"}
                                for i in range(1, 6)
                            ]
                        }
                    },
                    "Assets": {
                        "units": {
                            "USD": [
                                {"end": f"2024-0{i}-01", "val": 500000000 + i, "form": "10-Q", "frame": f"CY2024Q{i}"}
                                for i in range(1, 6)
                            ]
                        }
                    }
                }
            }
        }
        
        records = extractor._parse_facts_to_records('AAPL', facts, 3)
        assert len(records) == 3
    
    def test_validate_entry_valid(self, extractor):
        entry = {"end": "2024-01-01", "val": 100000, "form": "10-Q"}
        assert extractor._validate_entry(entry) == True
    
    def test_validate_entry_no_end_date(self, extractor):
        entry = {"val": 100000, "form": "10-Q"}
        assert extractor._validate_entry(entry) == False
    
    def test_validate_entry_no_value(self, extractor):
        entry = {"end": "2024-01-01", "form": "10-Q"}
        assert extractor._validate_entry(entry) == False
    
    def test_validate_entry_invalid_value_type(self, extractor):
        entry = {"end": "2024-01-01", "val": "invalid", "form": "10-Q"}
        assert extractor._validate_entry(entry) == False
    
    def test_validate_entry_value_too_large(self, extractor):
        entry = {"end": "2024-01-01", "val": 1e16, "form": "10-Q"}
        assert extractor._validate_entry(entry) == False
    
    def test_validate_entry_invalid_date(self, extractor):
        entry = {"end": "invalid-date", "val": 100000, "form": "10-Q"}
        assert extractor._validate_entry(entry) == False
    
    def test_determine_unit_key_shares_field(self, extractor):
        units = {"shares": [], "USD": []}
        unit_key = extractor._determine_unit_key('shares_outstanding', units)
        assert unit_key == "shares"
    
    def test_determine_unit_key_shares_field_pure_fallback(self, extractor):
        units = {"pure": [], "USD": []}
        unit_key = extractor._determine_unit_key('shares_outstanding', units)
        assert unit_key == "pure"
    
    def test_determine_unit_key_usd_field(self, extractor):
        units = {"USD": [], "shares": []}
        unit_key = extractor._determine_unit_key('revenue', units)
        assert unit_key == "USD"
    
    def test_determine_unit_key_ratio_field(self, extractor):
        units = {"pure": [], "USD": []}
        unit_key = extractor._determine_unit_key('current_ratio', units)
        assert unit_key == "pure"
    
    def test_determine_unit_key_default(self, extractor):
        units = {"EUR": [], "GBP": []}
        unit_key = extractor._determine_unit_key('revenue', units)
        assert unit_key == "EUR"
    
    def test_should_update_metric_10k_over_10q(self, extractor):
        existing_data = {"form_type": "10-Q"}
        new_entry = {"form": "10-K"}
        assert extractor._should_update_metric(existing_data, new_entry) == True
    
    def test_should_update_metric_10q_not_over_10k(self, extractor):
        existing_data = {"form_type": "10-K"}
        new_entry = {"form": "10-Q"}
        assert extractor._should_update_metric(existing_data, new_entry) == False
    
    def test_should_update_metric_same_form(self, extractor):
        existing_data = {"form_type": "10-Q"}
        new_entry = {"form": "10-Q"}
        assert extractor._should_update_metric(existing_data, new_entry) == False
    
    def test_has_sufficient_data_with_revenue(self, extractor):
        data = {"revenue": 100000}
        assert extractor._has_sufficient_data(data) == True
    
    def test_has_sufficient_data_with_assets(self, extractor):
        data = {"total_assets": 500000}
        assert extractor._has_sufficient_data(data) == True
    
    def test_has_sufficient_data_with_both(self, extractor):
        data = {"revenue": 100000, "total_assets": 500000}
        assert extractor._has_sufficient_data(data) == True
    
    def test_has_sufficient_data_neither(self, extractor):
        data = {"net_income": 20000}
        assert extractor._has_sufficient_data(data) == False
    
    def test_extract_period_from_frame_q1(self, extractor):
        assert extractor._extract_period_from_frame("CY2024Q1") == "Q1"
    
    def test_extract_period_from_frame_q2(self, extractor):
        assert extractor._extract_period_from_frame("CY2024Q2") == "Q2"
    
    def test_extract_period_from_frame_q3(self, extractor):
        assert extractor._extract_period_from_frame("CY2024Q3") == "Q3"
    
    def test_extract_period_from_frame_q4(self, extractor):
        assert extractor._extract_period_from_frame("CY2024Q4") == "Q4"
    
    def test_extract_period_from_frame_fy(self, extractor):
        assert extractor._extract_period_from_frame("CY2024") == "FY"
    
    def test_extract_period_from_frame_empty(self, extractor):
        assert extractor._extract_period_from_frame("") == ""
    
    def test_extract_period_from_frame_no_quarter(self, extractor):
        assert extractor._extract_period_from_frame("INVALID") == ""
    
    def test_determine_period_from_form_and_date_10k(self, extractor):
        assert extractor._determine_period_from_form_and_date("10-K", 12) == "FY"
    
    def test_determine_period_from_form_and_date_10q_q1(self, extractor):
        assert extractor._determine_period_from_form_and_date("10-Q", 5) == "Q1"
    
    def test_determine_period_from_form_and_date_10q_q2(self, extractor):
        assert extractor._determine_period_from_form_and_date("10-Q", 8) == "Q2"
    
    def test_determine_period_from_form_and_date_10q_q3(self, extractor):
        assert extractor._determine_period_from_form_and_date("10-Q", 11) == "Q3"
    
    def test_determine_period_from_form_and_date_10q_q4(self, extractor):
        assert extractor._determine_period_from_form_and_date("10-Q", 2) == "Q4"
    
    def test_get_quarter_from_10q_month_january(self, extractor):
        assert extractor._get_quarter_from_10q_month(1) == "Q4"
    
    def test_get_quarter_from_10q_month_march(self, extractor):
        assert extractor._get_quarter_from_10q_month(3) == "Q1"
    
    def test_get_quarter_from_10q_month_june(self, extractor):
        assert extractor._get_quarter_from_10q_month(6) == "Q2"
    
    def test_get_quarter_from_10q_month_september(self, extractor):
        assert extractor._get_quarter_from_10q_month(9) == "Q3"
    
    def test_get_quarter_from_10q_month_december(self, extractor):
        assert extractor._get_quarter_from_10q_month(12) == "Q4"
    
    def test_get_quarter_from_month_q1(self, extractor):
        assert extractor._get_quarter_from_month(1) == "Q1"
        assert extractor._get_quarter_from_month(2) == "Q1"
        assert extractor._get_quarter_from_month(3) == "Q1"
    
    def test_get_quarter_from_month_q2(self, extractor):
        assert extractor._get_quarter_from_month(4) == "Q2"
        assert extractor._get_quarter_from_month(5) == "Q2"
        assert extractor._get_quarter_from_month(6) == "Q2"
    
    def test_get_quarter_from_month_q3(self, extractor):
        assert extractor._get_quarter_from_month(7) == "Q3"
        assert extractor._get_quarter_from_month(8) == "Q3"
        assert extractor._get_quarter_from_month(9) == "Q3"
    
    def test_get_quarter_from_month_q4(self, extractor):
        assert extractor._get_quarter_from_month(10) == "Q4"
        assert extractor._get_quarter_from_month(11) == "Q4"
        assert extractor._get_quarter_from_month(12) == "Q4"
    
    def test_determine_period_with_frame(self, extractor):
        period = extractor._determine_period("2024-03-31", "10-Q", "CY2024Q1")
        assert period == "2024 Q1"
    
    def test_determine_period_without_frame_10k(self, extractor):
        period = extractor._determine_period("2024-12-31", "10-K", "")
        assert period == "2024 FY"
    
    def test_determine_period_without_frame_10q(self, extractor):
        period = extractor._determine_period("2024-03-31", "10-Q", "")
        assert period == "2024 Q1"
    
    def test_determine_period_invalid_date(self, extractor):
        period = extractor._determine_period("invalid", "10-Q", "")
        assert period == "Unknown"
    
    def test_update_period_data_new_period(self, extractor):
        period_data = {}
        entry = {
            "end": "2024-01-01",
            "val": 100000,
            "form": "10-Q",
            "frame": "CY2024Q1"
        }
        
        extractor._update_period_data('AAPL', 'revenue', entry, period_data)
        
        assert "2024-01-01_10-Q" in period_data
        assert period_data["2024-01-01_10-Q"]["revenue"] == 100000
        assert period_data["2024-01-01_10-Q"]["ticker"] == 'AAPL'
    
    def test_update_period_data_existing_period(self, extractor):
        period_data = {
            "2024-01-01_10-Q": {
                "ticker": "AAPL",
                "date": "2024-01-01",
                "form_type": "10-Q",
                "period": "2024 Q1",
                "revenue": 50000
            }
        }
        entry = {
            "end": "2024-01-01",
            "val": 100000,
            "form": "10-K"
        }
        
        extractor._update_period_data('AAPL', 'revenue', entry, period_data)
        
        assert period_data["2024-01-01_10-K"]["revenue"] == 100000
    
    def test_update_period_data_no_end_date(self, extractor):
        period_data = {}
        entry = {"val": 100000, "form": "10-Q"}
        
        extractor._update_period_data('AAPL', 'revenue', entry, period_data)
        
        assert len(period_data) == 0
    
    def test_update_period_data_no_value(self, extractor):
        period_data = {}
        entry = {"end": "2024-01-01", "form": "10-Q"}
        
        extractor._update_period_data('AAPL', 'revenue', entry, period_data)
        
        assert len(period_data) == 0
    
    def test_build_financial_record(self, extractor):
        data = {
            "ticker": "AAPL",
            "date": "2024-01-01",
            "form_type": "10-Q",
            "period": "2024 Q1",
            "revenue": 100000,
            "net_income": 20000,
            "invalid_field": "should_be_ignored"
        }
        
        record = extractor._build_financial_record(data)
        
        assert record.ticker == "AAPL"
        assert record.revenue == 100000
        assert record.net_income == 20000
        assert not hasattr(record, 'invalid_field')
    
    def test_collect_metric_data_no_metric(self, extractor):
        us_gaap_facts = {}
        period_data = {}
        
        extractor._collect_metric_data('AAPL', us_gaap_facts, 'revenue', ['Revenues'], period_data)
        
        assert len(period_data) == 0
    
    def test_collect_metric_data_no_units(self, extractor):
        us_gaap_facts = {"Revenues": {}}
        period_data = {}
        
        extractor._collect_metric_data('AAPL', us_gaap_facts, 'revenue', ['Revenues'], period_data)
        
        assert len(period_data) == 0
    
    def test_collect_metric_data_with_valid_entry(self, extractor):
        us_gaap_facts = {
            "Revenues": {
                "units": {
                    "USD": [
                        {"end": "2024-01-01", "val": 100000, "form": "10-Q", "frame": "CY2024Q1"}
                    ]
                }
            }
        }
        period_data = {}
        
        extractor._collect_metric_data('AAPL', us_gaap_facts, 'revenue', ['Revenues'], period_data)
        
        assert len(period_data) == 1
        assert any(data.get('revenue') == 100000 for data in period_data.values())
    
    def test_collect_metric_data_multiple_metrics(self, extractor):
        us_gaap_facts = {
            "Revenues": {
                "units": {
                    "USD": [
                        {"end": "2024-01-01", "val": 100000, "form": "10-Q", "frame": "CY2024Q1"}
                    ]
                }
            },
            "SalesRevenueNet": {
                "units": {
                    "USD": [
                        {"end": "2024-01-01", "val": 95000, "form": "10-Q", "frame": "CY2024Q1"}
                    ]
                }
            }
        }
        period_data = {}
        
        extractor._collect_metric_data('AAPL', us_gaap_facts, 'revenue', ['Revenues', 'SalesRevenueNet'], period_data)
        
        assert len(period_data) >= 1
    
    def test_records_sorted_by_date_descending(self, extractor, mock_http_client):
        facts = {
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {"end": "2023-01-01", "val": 80000000, "form": "10-Q", "frame": "CY2023Q1"},
                                {"end": "2024-01-01", "val": 100000000, "form": "10-Q", "frame": "CY2024Q1"},
                                {"end": "2023-06-01", "val": 90000000, "form": "10-Q", "frame": "CY2023Q2"}
                            ]
                        }
                    }
                }
            }
        }
        
        mock_response = Mock()
        mock_response.json.return_value = facts
        mock_http_client.get.return_value = mock_response
        
        records = extractor.extract_raw_financial_data('AAPL', limit=10)
        
        assert len(records) >= 2
        assert records[0].date >= records[1].date