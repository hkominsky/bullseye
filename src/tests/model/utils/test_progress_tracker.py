import pytest
from io import StringIO
from unittest.mock import patch
from src.model.utils.progress_tracker import ProgressTracker


class TestProgressTracker:
    
    def test_init_with_total_steps(self):
        tracker = ProgressTracker(total_steps=10)
        
        assert tracker.total_steps == 10
        assert tracker.current_step == 0
    
    def test_init_without_total_steps(self):
        tracker = ProgressTracker()
        
        assert tracker.total_steps is None
        assert tracker.current_step == 0
    
    def test_start_prints_message(self):
        tracker = ProgressTracker()
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.start('AAPL')
            output = fake_out.getvalue()
        
        assert 'Processing started for AAPL' in output
    
    def test_step_with_total_steps_shows_percentage(self):
        tracker = ProgressTracker(total_steps=10)
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.step('First step')
            output = fake_out.getvalue()
        
        assert '[10%]' in output
        assert 'First step' in output
    
    def test_step_without_total_steps_shows_count(self):
        tracker = ProgressTracker()
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.step('First step')
            output = fake_out.getvalue()
        
        assert '[1]' in output
        assert 'First step' in output
        assert '%' not in output
    
    def test_step_increments_current_step(self):
        tracker = ProgressTracker(total_steps=10)
        
        assert tracker.current_step == 0
        tracker.step('Step 1')
        assert tracker.current_step == 1
        tracker.step('Step 2')
        assert tracker.current_step == 2
    
    def test_step_percentage_calculation(self):
        tracker = ProgressTracker(total_steps=4)
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.step('Step 1')
            output1 = fake_out.getvalue()
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.step('Step 2')
            output2 = fake_out.getvalue()
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.step('Step 3')
            output3 = fake_out.getvalue()
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.step('Step 4')
            output4 = fake_out.getvalue()
        
        assert '[25%]' in output1
        assert '[50%]' in output2
        assert '[75%]' in output3
        assert '[100%]' in output4
    
    def test_complete_prints_message(self):
        tracker = ProgressTracker()
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.complete('AAPL')
            output = fake_out.getvalue()
        
        assert 'AAPL market brief complete' in output
    
    def test_multiple_steps_count_correctly(self):
        tracker = ProgressTracker()
        
        for i in range(5):
            tracker.step(f'Step {i+1}')
        
        assert tracker.current_step == 5
    
    def test_start_with_different_tickers(self):
        tracker = ProgressTracker()
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.start('MSFT')
            output = fake_out.getvalue()
        
        assert 'Processing started for MSFT' in output
    
    def test_complete_with_different_tickers(self):
        tracker = ProgressTracker()
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.complete('GOOGL')
            output = fake_out.getvalue()
        
        assert 'GOOGL market brief complete' in output
    
    def test_full_workflow(self):
        tracker = ProgressTracker(total_steps=3)
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.start('AAPL')
            tracker.step('Fetching data')
            tracker.step('Processing data')
            tracker.step('Sending email')
            tracker.complete('AAPL')
            output = fake_out.getvalue()
        
        assert 'Processing started for AAPL' in output
        assert '[33%] Fetching data' in output
        assert '[67%] Processing data' in output
        assert '[100%] Sending email' in output
        assert 'AAPL market brief complete' in output
    
    def test_percentage_rounds_correctly(self):
        tracker = ProgressTracker(total_steps=3)
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.step('Step 1')
            output = fake_out.getvalue()
        
        assert '[33%]' in output
    
    def test_step_with_empty_message(self):
        tracker = ProgressTracker(total_steps=1)
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            tracker.step('')
            output = fake_out.getvalue()
        
        assert '[100%]' in output
    
    def test_zero_total_steps_edge_case(self):
        tracker = ProgressTracker(total_steps=0)
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with pytest.raises(ZeroDivisionError):
                tracker.step('Step')