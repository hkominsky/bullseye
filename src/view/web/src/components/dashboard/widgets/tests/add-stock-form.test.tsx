import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AddStockForm } from '../add-stock-form.tsx';
import { StockService } from '../../../../services/stocks.ts';
import { useToast } from '../toast-context.tsx';

// Mocks
jest.mock('../../../../services/stocks.ts');
jest.mock('../toast-context.tsx');

const mockShowToast = jest.fn();

const renderAddStockForm = (props = {}) => {
  const defaultProps = {
    onAddStock: jest.fn(),
    onCancel: jest.fn(),
    existingStocks: [],
    targetList: 'watchlist' as const,
    ...props
  };

  jest.mocked(useToast).mockReturnValue({
    showToast: mockShowToast
  });

  return {
    ...render(<AddStockForm {...defaultProps} />),
    ...defaultProps
  };
};

describe('AddStockForm Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Rendering', () => {
    it('should render form with input and buttons', () => {
      renderAddStockForm();

      expect(screen.getByPlaceholderText('Enter ticker')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Add Stock' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    });

    it('should focus input on mount', () => {
      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');

      expect(input).toHaveFocus();
    });

    it('should disable Add Stock button initially', () => {
      renderAddStockForm();
      const addButton = screen.getByRole('button', { name: 'Add Stock' });

      expect(addButton).toBeDisabled();
    });

    it('should apply secondary class to Add Stock button when disabled', () => {
      renderAddStockForm();
      const addButton = screen.getByRole('button', { name: 'Add Stock' });

      expect(addButton).toHaveClass('secondary');
      expect(addButton).not.toHaveClass('primary');
    });
  });

  describe('Input Interactions', () => {
    it('should update input value on change', () => {
      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker') as HTMLInputElement;

      fireEvent.change(input, { target: { value: 'aapl' } });

      expect(input.value).toBe('AAPL');
    });

    it('should convert input to uppercase', () => {
      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker') as HTMLInputElement;

      fireEvent.change(input, { target: { value: 'tsla' } });

      expect(input.value).toBe('TSLA');
    });

    it('should clear error when typing after error is displayed', () => {
      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');
      const addButton = screen.getByRole('button', { name: 'Add Stock' });

      fireEvent.click(addButton);
      expect(screen.getByRole('alert')).toHaveTextContent('Please enter a stock ticker');

      fireEvent.change(input, { target: { value: 'AAPL' } });

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('should handle Escape key to cancel', () => {
      const { onCancel } = renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');

      fireEvent.keyDown(input, { key: 'Escape' });

      expect(onCancel).toHaveBeenCalled();
    });
  });

  describe('Stock Suggestions', () => {
    it('should not fetch suggestions for input less than 2 characters', async () => {
      const mockSearchStocks = jest.fn();
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');

      fireEvent.change(input, { target: { value: 'A' } });
      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(mockSearchStocks).not.toHaveBeenCalled();
      });
    });

    it('should fetch suggestions with debouncing', async () => {
      const mockSearchStocks = jest.fn().mockResolvedValue({
        suggestions: [
          { symbol: 'AAPL', name: 'Apple Inc.' },
          { symbol: 'AMD', name: 'Advanced Micro Devices' }
        ]
      });
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');

      fireEvent.change(input, { target: { value: 'AA' } });
      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(mockSearchStocks).toHaveBeenCalledWith('AA', 5);
      });
    });

    it('should display suggestions dropdown when results are available', async () => {
      const mockSearchStocks = jest.fn().mockResolvedValue({
        suggestions: [
          { symbol: 'AAPL', name: 'Apple Inc.' },
          { symbol: 'AMD', name: 'Advanced Micro Devices' }
        ]
      });
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');

      fireEvent.change(input, { target: { value: 'AA' } });
      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
        expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
        expect(screen.getByText('AMD')).toBeInTheDocument();
        expect(screen.getByText('Advanced Micro Devices')).toBeInTheDocument();
      });
    });

    it('should select suggestion on click', async () => {
      const mockSearchStocks = jest.fn().mockResolvedValue({
        suggestions: [
          { symbol: 'AAPL', name: 'Apple Inc.' }
        ]
      });
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker') as HTMLInputElement;

      fireEvent.change(input, { target: { value: 'AA' } });
      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });

      const suggestion = screen.getByText('AAPL').closest('button');
      fireEvent.click(suggestion!);

      expect(input.value).toBe('AAPL');
      expect(screen.queryByText('Apple Inc.')).not.toBeInTheDocument();
    });

    it('should close suggestions when clicking outside', async () => {
      const mockSearchStocks = jest.fn().mockResolvedValue({
        suggestions: [
          { symbol: 'AAPL', name: 'Apple Inc.' }
        ]
      });
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');

      fireEvent.change(input, { target: { value: 'AA' } });
      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });

      fireEvent.mouseDown(document.body);

      await waitFor(() => {
        expect(screen.queryByText('Apple Inc.')).not.toBeInTheDocument();
      });
    });

    it('should show toast on search service error', async () => {
      const mockSearchStocks = jest.fn().mockRejectedValue(
        new Error('Search service temporarily unavailable')
      );
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');

      fireEvent.change(input, { target: { value: 'AA' } });
      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(mockShowToast).toHaveBeenCalledWith(
          'Search service temporarily unavailable',
          'error'
        );
      });
    });

    it('should not show toast for non-service errors', async () => {
      const mockSearchStocks = jest.fn().mockRejectedValue(
        new Error('Network error')
      );
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');

      fireEvent.change(input, { target: { value: 'AA' } });
      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(mockSearchStocks).toHaveBeenCalled();
      });

      expect(mockShowToast).not.toHaveBeenCalled();
    });
  });

  describe('Form Validation', () => {
    it('should show error when submitting empty ticker', async () => {
      renderAddStockForm();
      const addButton = screen.getByRole('button', { name: 'Add Stock' });

      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Please enter a stock ticker');
      });
    });

    it('should show error when ticker is only whitespace', async () => {
      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');
      const addButton = screen.getByRole('button', { name: 'Add Stock' });

      fireEvent.change(input, { target: { value: '   ' } });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Please enter a stock ticker');
      });
    });

    it('should show error when ticker already exists in watchlist', async () => {
      renderAddStockForm({ existingStocks: ['AAPL', 'TSLA'] });
      const input = screen.getByPlaceholderText('Enter ticker');
      const addButton = screen.getByRole('button', { name: 'Add Stock' });

      fireEvent.change(input, { target: { value: 'AAPL' } });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(
          'AAPL is already in your watchlist'
        );
      });
    });

    it('should show error with custom target list name', async () => {
      renderAddStockForm({ 
        existingStocks: ['AAPL'], 
        targetList: 'reserve' 
      });
      const input = screen.getByPlaceholderText('Enter ticker');
      const addButton = screen.getByRole('button', { name: 'Add Stock' });

      fireEvent.change(input, { target: { value: 'AAPL' } });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(
          'AAPL is already in your reserve'
        );
      });
    });

    it('should apply error class to input when error is present', async () => {
      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');
      const addButton = screen.getByRole('button', { name: 'Add Stock' });

      fireEvent.click(addButton);

      await waitFor(() => {
        expect(input).toHaveClass('error');
      });
    });
  });

  describe('Ticker Validation', () => {
    it('should validate ticker before adding', async () => {
      const mockValidateTicker = jest.fn().mockResolvedValue({ valid: true });
      (StockService.validateTicker as jest.Mock) = mockValidateTicker;

      const { onAddStock } = renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');

      fireEvent.change(input, { target: { value: 'AAPL' } });
      
      // Select from suggestions to mark as validated
      const mockSearchStocks = jest.fn().mockResolvedValue({
        suggestions: [{ symbol: 'AAPL', name: 'Apple Inc.' }]
      });
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;
      
      jest.advanceTimersByTime(300);
      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });
      
      const suggestion = screen.getByText('AAPL').closest('button');
      fireEvent.click(suggestion!);

      const addButton = screen.getByRole('button', { name: 'Add Stock' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockValidateTicker).toHaveBeenCalledWith('AAPL');
      });
    });

    it('should show error for invalid ticker', async () => {
      const mockValidateTicker = jest.fn().mockResolvedValue({ 
        valid: false, 
        error: 'Ticker not found' 
      });
      (StockService.validateTicker as jest.Mock) = mockValidateTicker;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');
      const addButton = screen.getByRole('button', { name: 'Add Stock' });

      fireEvent.change(input, { target: { value: 'INVALID' } });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Ticker not found');
      });
    });

    it('should show generic error when validation fails without message', async () => {
      const mockValidateTicker = jest.fn().mockResolvedValue({ valid: false });
      (StockService.validateTicker as jest.Mock) = mockValidateTicker;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');
      const addButton = screen.getByRole('button', { name: 'Add Stock' });

      fireEvent.change(input, { target: { value: 'INVALID' } });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Invalid stock ticker.');
      });
    });

    it('should show network error on validation failure', async () => {
      const mockValidateTicker = jest.fn().mockRejectedValue(new Error('Network error'));
      (StockService.validateTicker as jest.Mock) = mockValidateTicker;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');
      const addButton = screen.getByRole('button', { name: 'Add Stock' });

      fireEvent.change(input, { target: { value: 'AAPL' } });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Network error. Please try again.');
      });
    });
  });

  describe('Form Submission', () => {
    it('should call onAddStock with valid ticker', async () => {
      const mockValidateTicker = jest.fn().mockResolvedValue({ valid: true });
      (StockService.validateTicker as jest.Mock) = mockValidateTicker;

      const { onAddStock } = renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');

      fireEvent.change(input, { target: { value: 'AAPL' } });
      
      // Select from suggestions
      const mockSearchStocks = jest.fn().mockResolvedValue({
        suggestions: [{ symbol: 'AAPL', name: 'Apple Inc.' }]
      });
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;
      
      jest.advanceTimersByTime(300);
      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });
      
      const suggestion = screen.getByText('AAPL').closest('button');
      fireEvent.click(suggestion!);

      const addButton = screen.getByRole('button', { name: 'Add Stock' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(onAddStock).toHaveBeenCalledWith('AAPL');
      });
    });

    it('should trim whitespace from ticker before submitting', async () => {
      const mockValidateTicker = jest.fn().mockResolvedValue({ valid: true });
      (StockService.validateTicker as jest.Mock) = mockValidateTicker;

      const { onAddStock } = renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');

      fireEvent.change(input, { target: { value: '  AAPL  ' } });
      
      const mockSearchStocks = jest.fn().mockResolvedValue({
        suggestions: [{ symbol: 'AAPL', name: 'Apple Inc.' }]
      });
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;
      
      jest.advanceTimersByTime(300);
      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });
      
      const suggestion = screen.getByText('AAPL').closest('button');
      fireEvent.click(suggestion!);

      const addButton = screen.getByRole('button', { name: 'Add Stock' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(onAddStock).toHaveBeenCalledWith('AAPL');
      });
    });

    it('should clear form after successful submission', async () => {
      const mockValidateTicker = jest.fn().mockResolvedValue({ valid: true });
      (StockService.validateTicker as jest.Mock) = mockValidateTicker;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker') as HTMLInputElement;

      fireEvent.change(input, { target: { value: 'AAPL' } });
      
      const mockSearchStocks = jest.fn().mockResolvedValue({
        suggestions: [{ symbol: 'AAPL', name: 'Apple Inc.' }]
      });
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;
      
      jest.advanceTimersByTime(300);
      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });
      
      const suggestion = screen.getByText('AAPL').closest('button');
      fireEvent.click(suggestion!);

      const addButton = screen.getByRole('button', { name: 'Add Stock' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(input.value).toBe('');
      });
    });

    it('should handle Enter key for submission', async () => {
      const mockValidateTicker = jest.fn().mockResolvedValue({ valid: true });
      (StockService.validateTicker as jest.Mock) = mockValidateTicker;

      const { onAddStock } = renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');

      fireEvent.change(input, { target: { value: 'AAPL' } });
      
      const mockSearchStocks = jest.fn().mockResolvedValue({
        suggestions: [{ symbol: 'AAPL', name: 'Apple Inc.' }]
      });
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;
      
      jest.advanceTimersByTime(300);
      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });
      
      const suggestion = screen.getByText('AAPL').closest('button');
      fireEvent.click(suggestion!);

      fireEvent.keyDown(input, { key: 'Enter' });

      await waitFor(() => {
        expect(onAddStock).toHaveBeenCalledWith('AAPL');
      });
    });

    it('should disable Add Stock button while loading', async () => {
      const mockValidateTicker = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      (StockService.validateTicker as jest.Mock) = mockValidateTicker;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');

      fireEvent.change(input, { target: { value: 'AAPL' } });
      
      const mockSearchStocks = jest.fn().mockResolvedValue({
        suggestions: [{ symbol: 'AAPL', name: 'Apple Inc.' }]
      });
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;
      
      jest.advanceTimersByTime(300);
      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });
      
      const suggestion = screen.getByText('AAPL').closest('button');
      fireEvent.click(suggestion!);

      const addButton = screen.getByRole('button', { name: 'Add Stock' }) as HTMLButtonElement;
      fireEvent.click(addButton);

      expect(addButton.disabled).toBe(true);
    });
  });

  describe('Button State Management', () => {
    it('should enable Add Stock button when ticker is validated through suggestion', async () => {
      const mockSearchStocks = jest.fn().mockResolvedValue({
        suggestions: [{ symbol: 'AAPL', name: 'Apple Inc.' }]
      });
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');
      const addButton = screen.getByRole('button', { name: 'Add Stock' }) as HTMLButtonElement;

      fireEvent.change(input, { target: { value: 'AA' } });
      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });

      const suggestion = screen.getByText('AAPL').closest('button');
      fireEvent.click(suggestion!);

      expect(addButton.disabled).toBe(false);
      expect(addButton).toHaveClass('primary');
    });

    it('should disable Add Stock button when ticker is modified after validation', async () => {
      const mockSearchStocks = jest.fn().mockResolvedValue({
        suggestions: [{ symbol: 'AAPL', name: 'Apple Inc.' }]
      });
      (StockService.searchStocks as jest.Mock) = mockSearchStocks;

      renderAddStockForm();
      const input = screen.getByPlaceholderText('Enter ticker');
      const addButton = screen.getByRole('button', { name: 'Add Stock' }) as HTMLButtonElement;

      fireEvent.change(input, { target: { value: 'AA' } });
      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });

      const suggestion = screen.getByText('AAPL').closest('button');
      fireEvent.click(suggestion!);

      expect(addButton.disabled).toBe(false);

      fireEvent.change(input, { target: { value: 'AAPL2' } });

      expect(addButton.disabled).toBe(true);
    });

    it('should disable Add Stock button when ticker exists in list', async () => {
      renderAddStockForm({ existingStocks: ['AAPL'] });
      const input = screen.getByPlaceholderText('Enter ticker');
      const addButton = screen.getByRole('button', { name: 'Add Stock' }) as HTMLButtonElement;

      fireEvent.change(input, { target: { value: 'AAPL' } });

      expect(addButton.disabled).toBe(true);
    });
  });

  describe('Cancel Button', () => {
    it('should call onCancel when Cancel button is clicked', () => {
      const { onCancel } = renderAddStockForm();
      const cancelButton = screen.getByRole('button', { name: 'Cancel' });

      fireEvent.click(cancelButton);

      expect(onCancel).toHaveBeenCalled();
    });
  });
});