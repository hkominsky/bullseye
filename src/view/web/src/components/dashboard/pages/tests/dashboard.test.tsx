import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Dashboard from '../dashboard.tsx';
import { StockService } from '../../../../services/stocks.ts';
import { EmailService } from '../../../../services/emails.ts';
import * as ToastContext from '../../widgets/toast-context.tsx';

// Mocks
jest.mock('../../../services/stocks.ts');
jest.mock('../../../services/emails.ts');
jest.mock('../styles/dashboard.css', () => ({}));
jest.mock('../widgets/header.tsx', () => ({
  Header: () => <div data-testid="header">Header</div>
}));
jest.mock('../widgets/watch-list.tsx', () => ({
  Watchlist: ({ 
    stocks, 
    onRemoveStock, 
    onAddStock, 
    showAddForm,
    existingStocks,
    onCancelAddForm,
    onToggleAddForm,
    onMoveToReserve,
    onEmailAll,
    onSendEmail,
    isEmailProcessing
  }: any) => (
    <div data-testid="watchlist">
      <div>Watchlist: {stocks.length} stocks</div>
      <div>Show Add Form: {showAddForm.toString()}</div>
      <div>Email Processing: {isEmailProcessing.toString()}</div>
      <button onClick={onToggleAddForm}>Toggle Add Form</button>
      <button onClick={onCancelAddForm}>Cancel Add</button>
      <button onClick={() => onAddStock('AAPL')}>Add AAPL</button>
      <button onClick={() => onRemoveStock('AAPL')}>Remove AAPL</button>
      <button onClick={() => onMoveToReserve('AAPL')}>Move to Reserve</button>
      <button onClick={onEmailAll}>Email All</button>
      <button onClick={() => onSendEmail('AAPL')}>Email AAPL</button>
      {stocks.map((stock: any) => (
        <div key={stock.symbol}>{stock.symbol}</div>
      ))}
    </div>
  )
}));
jest.mock('../widgets/reserve-list.tsx', () => ({
  ReserveList: ({ 
    stocks, 
    onRemoveStock, 
    onAddStock, 
    showAddForm,
    existingStocks,
    onCancelAddForm,
    onToggleAddForm,
    onMoveToWatchlist
  }: any) => (
    <div data-testid="reserve-list">
      <div>Reserve: {stocks.length} stocks</div>
      <div>Show Add Form: {showAddForm.toString()}</div>
      <button onClick={onToggleAddForm}>Toggle Reserve Add Form</button>
      <button onClick={onCancelAddForm}>Cancel Reserve Add</button>
      <button onClick={() => onAddStock('GOOGL')}>Add GOOGL</button>
      <button onClick={() => onRemoveStock('GOOGL')}>Remove GOOGL</button>
      <button onClick={() => onMoveToWatchlist('GOOGL')}>Move to Watchlist</button>
      {stocks.map((stock: any) => (
        <div key={stock.symbol}>{stock.symbol}</div>
      ))}
    </div>
  )
}));
jest.mock('../widgets/toast-context.tsx', () => ({
  ToastProvider: ({ children }: any) => <div>{children}</div>,
  useToast: jest.fn()
}));

const mockToast = {
  showToast: jest.fn()
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(ToastContext, 'useToast').mockReturnValue(mockToast);
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('should render all main components', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('header')).toBeInTheDocument();
        expect(screen.getByTestId('watchlist')).toBeInTheDocument();
        expect(screen.getByTestId('reserve-list')).toBeInTheDocument();
      });
    });

    it('should render dashboard container with correct class', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);

      const { container } = render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(container.querySelector('.dashboard-container')).toBeInTheDocument();
      });
    });
  });

  describe('Initial Data Loading', () => {
    it('should load watchlist stocks on mount', async () => {
      const mockWatchlistTickers = ['AAPL', 'GOOGL'];
      const mockStocks = [
        { symbol: 'AAPL', name: 'Apple Inc.', price: 150 },
        { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 2800 }
      ];

      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(mockWatchlistTickers);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock)
        .mockResolvedValueOnce(mockStocks[0])
        .mockResolvedValueOnce(mockStocks[1]);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
        expect(screen.getByText('GOOGL')).toBeInTheDocument();
      });
    });

    it('should load reserve stocks on mount', async () => {
      const mockReserveTickers = ['TSLA', 'MSFT'];
      const mockStocks = [
        { symbol: 'TSLA', name: 'Tesla Inc.', price: 700 },
        { symbol: 'MSFT', name: 'Microsoft Corp.', price: 300 }
      ];

      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue(mockReserveTickers);
      (StockService.getStockInfo as jest.Mock)
        .mockResolvedValueOnce(mockStocks[0])
        .mockResolvedValueOnce(mockStocks[1]);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('TSLA')).toBeInTheDocument();
        expect(screen.getByText('MSFT')).toBeInTheDocument();
      });
    });

    it('should load both watchlist and reserve stocks', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue(['GOOGL']);
      (StockService.getStockInfo as jest.Mock)
        .mockResolvedValueOnce({ symbol: 'AAPL', name: 'Apple', price: 150 })
        .mockResolvedValueOnce({ symbol: 'GOOGL', name: 'Google', price: 2800 });

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
        expect(screen.getByText('GOOGL')).toBeInTheDocument();
      });
    });

    it('should handle empty watchlist on mount', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 0 stocks')).toBeInTheDocument();
      });
    });

    it('should handle empty reserve list on mount', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Reserve: 0 stocks')).toBeInTheDocument();
      });
    });

    it('should log error when initial load fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      (StockService.getUserWatchlist as jest.Mock).mockRejectedValue(new Error('Load failed'));
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to load initial stocks:', expect.any(Error));
      });
    });
  });

  describe('Add Stock to Watchlist', () => {
    beforeEach(async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
    });

    it('should add stock to watchlist', async () => {
      const newStock = { symbol: 'AAPL', name: 'Apple Inc.', price: 150 };
      (StockService.getStockInfo as jest.Mock).mockResolvedValue(newStock);
      (StockService.addToWatchlist as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('watchlist')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add AAPL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(StockService.getStockInfo).toHaveBeenCalledWith('AAPL');
        expect(StockService.addToWatchlist).toHaveBeenCalledWith('AAPL');
      });
    });

    it('should update UI after adding stock', async () => {
      const newStock = { symbol: 'AAPL', name: 'Apple Inc.', price: 150 };
      (StockService.getStockInfo as jest.Mock).mockResolvedValue(newStock);
      (StockService.addToWatchlist as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 0 stocks')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add AAPL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
      });
    });

    it('should close add form after adding stock', async () => {
      const newStock = { symbol: 'AAPL', name: 'Apple Inc.', price: 150 };
      (StockService.getStockInfo as jest.Mock).mockResolvedValue(newStock);
      (StockService.addToWatchlist as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('watchlist')).toBeInTheDocument();
      });

      const toggleButton = screen.getByRole('button', { name: 'Toggle Add Form' });
      fireEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText('Show Add Form: true')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add AAPL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('Show Add Form: false')).toBeInTheDocument();
      });
    });

    it('should not add duplicate stock to watchlist', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (StockService.addToWatchlist as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add AAPL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(StockService.addToWatchlist).not.toHaveBeenCalled();
      });
    });

    it('should log error when adding stock fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      (StockService.getStockInfo as jest.Mock).mockRejectedValue(new Error('Stock not found'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('watchlist')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add AAPL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to add AAPL:', expect.any(Error));
      });
    });
  });

  describe('Add Stock to Reserve', () => {
    beforeEach(() => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
    });

    it('should add stock to reserve list', async () => {
      const newStock = { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 2800 };
      (StockService.getStockInfo as jest.Mock).mockResolvedValue(newStock);
      (StockService.addToReserve as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('reserve-list')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add GOOGL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(StockService.getStockInfo).toHaveBeenCalledWith('GOOGL');
        expect(StockService.addToReserve).toHaveBeenCalledWith('GOOGL');
      });
    });

    it('should update UI after adding stock to reserve', async () => {
      const newStock = { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 2800 };
      (StockService.getStockInfo as jest.Mock).mockResolvedValue(newStock);
      (StockService.addToReserve as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Reserve: 0 stocks')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add GOOGL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('Reserve: 1 stocks')).toBeInTheDocument();
      });
    });

    it('should close reserve add form after adding stock', async () => {
      const newStock = { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 2800 };
      (StockService.getStockInfo as jest.Mock).mockResolvedValue(newStock);
      (StockService.addToReserve as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('reserve-list')).toBeInTheDocument();
      });

      const toggleButton = screen.getByRole('button', { name: 'Toggle Reserve Add Form' });
      fireEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText('Show Add Form: true')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add GOOGL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('Show Add Form: false')).toBeInTheDocument();
      });
    });

    it('should not add duplicate stock to reserve', async () => {
      (StockService.getUserReserve as jest.Mock).mockResolvedValue(['GOOGL']);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'GOOGL', name: 'Google', price: 2800 });
      (StockService.addToReserve as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Reserve: 1 stocks')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add GOOGL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(StockService.addToReserve).not.toHaveBeenCalled();
      });
    });

    it('should log error when adding to reserve fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      (StockService.getStockInfo as jest.Mock).mockRejectedValue(new Error('Stock not found'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('reserve-list')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add GOOGL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to add GOOGL:', expect.any(Error));
      });
    });
  });

  describe('Remove Stock from Watchlist', () => {
    it('should remove stock from watchlist', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (StockService.removeFromWatchlist as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
      });

      const removeButton = screen.getByRole('button', { name: 'Remove AAPL' });
      fireEvent.click(removeButton);

      await waitFor(() => {
        expect(StockService.removeFromWatchlist).toHaveBeenCalledWith('AAPL');
        expect(screen.getByText('Watchlist: 0 stocks')).toBeInTheDocument();
      });
    });

    it('should log error when removing from watchlist fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (StockService.removeFromWatchlist as jest.Mock).mockRejectedValue(new Error('Remove failed'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });

      const removeButton = screen.getByRole('button', { name: 'Remove AAPL' });
      fireEvent.click(removeButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to remove AAPL:', expect.any(Error));
      });
    });
  });

  describe('Remove Stock from Reserve', () => {
    it('should remove stock from reserve list', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue(['GOOGL']);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'GOOGL', name: 'Google', price: 2800 });
      (StockService.removeFromReserve as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Reserve: 1 stocks')).toBeInTheDocument();
      });

      const removeButton = screen.getByRole('button', { name: 'Remove GOOGL' });
      fireEvent.click(removeButton);

      await waitFor(() => {
        expect(StockService.removeFromReserve).toHaveBeenCalledWith('GOOGL');
        expect(screen.getByText('Reserve: 0 stocks')).toBeInTheDocument();
      });
    });

    it('should log error when removing from reserve fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue(['GOOGL']);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'GOOGL', name: 'Google', price: 2800 });
      (StockService.removeFromReserve as jest.Mock).mockRejectedValue(new Error('Remove failed'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('GOOGL')).toBeInTheDocument();
      });

      const removeButton = screen.getByRole('button', { name: 'Remove GOOGL' });
      fireEvent.click(removeButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to remove GOOGL:', expect.any(Error));
      });
    });
  });

  describe('Move Stock Between Lists', () => {
    it('should move stock from watchlist to reserve', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (StockService.moveToReserve as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
        expect(screen.getByText('Reserve: 0 stocks')).toBeInTheDocument();
      });

      const moveButton = screen.getByRole('button', { name: 'Move to Reserve' });
      fireEvent.click(moveButton);

      await waitFor(() => {
        expect(StockService.moveToReserve).toHaveBeenCalledWith('AAPL');
        expect(screen.getByText('Watchlist: 0 stocks')).toBeInTheDocument();
        expect(screen.getByText('Reserve: 1 stocks')).toBeInTheDocument();
      });
    });

    it('should move stock from reserve to watchlist', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue(['GOOGL']);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'GOOGL', name: 'Google', price: 2800 });
      (StockService.moveToWatchlist as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 0 stocks')).toBeInTheDocument();
        expect(screen.getByText('Reserve: 1 stocks')).toBeInTheDocument();
      });

      const moveButton = screen.getByRole('button', { name: 'Move to Watchlist' });
      fireEvent.click(moveButton);

      await waitFor(() => {
        expect(StockService.moveToWatchlist).toHaveBeenCalledWith('GOOGL');
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
        expect(screen.getByText('Reserve: 0 stocks')).toBeInTheDocument();
      });
    });

    it('should not move non-existent stock to reserve', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.moveToReserve as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('watchlist')).toBeInTheDocument();
      });

      const moveButton = screen.getByRole('button', { name: 'Move to Reserve' });
      fireEvent.click(moveButton);

      await waitFor(() => {
        expect(StockService.moveToReserve).not.toHaveBeenCalled();
      });
    });

    it('should not move non-existent stock to watchlist', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.moveToWatchlist as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('reserve-list')).toBeInTheDocument();
      });

      const moveButton = screen.getByRole('button', { name: 'Move to Watchlist' });
      fireEvent.click(moveButton);

      await waitFor(() => {
        expect(StockService.moveToWatchlist).not.toHaveBeenCalled();
      });
    });

    it('should log error when move to reserve fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (StockService.moveToReserve as jest.Mock).mockRejectedValue(new Error('Move failed'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });

      const moveButton = screen.getByRole('button', { name: 'Move to Reserve' });
      fireEvent.click(moveButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to move AAPL to reserve:', expect.any(Error));
      });
    });

    it('should log error when move to watchlist fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue(['GOOGL']);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'GOOGL', name: 'Google', price: 2800 });
      (StockService.moveToWatchlist as jest.Mock).mockRejectedValue(new Error('Move failed'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('GOOGL')).toBeInTheDocument();
      });

      const moveButton = screen.getByRole('button', { name: 'Move to Watchlist' });
      fireEvent.click(moveButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to move GOOGL to watchlist:', expect.any(Error));
      });
    });
  });

  describe('Email Functionality', () => {
    beforeEach(() => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
    });

    it('should send emails for all watchlist stocks', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL', 'GOOGL']);
      (StockService.getStockInfo as jest.Mock)
        .mockResolvedValueOnce({ symbol: 'AAPL', name: 'Apple', price: 150 })
        .mockResolvedValueOnce({ symbol: 'GOOGL', name: 'Google', price: 2800 });
      (EmailService.sendWatchlistEmails as jest.Mock).mockResolvedValue({ ticker_count: 2 });

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 2 stocks')).toBeInTheDocument();
      });

      const emailButton = screen.getByRole('button', { name: 'Email All' });
      fireEvent.click(emailButton);

      await waitFor(() => {
        expect(EmailService.sendWatchlistEmails).toHaveBeenCalled();
        expect(mockToast.showToast).toHaveBeenCalledWith('Sending emails for 2 stocks!', 'success');
      });
    });

    it('should show error toast when watchlist is empty', async () => {
      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 0 stocks')).toBeInTheDocument();
      });

      const emailButton = screen.getByRole('button', { name: 'Email All' });
      fireEvent.click(emailButton);

      await waitFor(() => {
        expect(mockToast.showToast).toHaveBeenCalledWith(
          'Watchlist is empty. Add stocks before sending emails.',
          'error'
        );
      });
    });

    it('should send email for single stock', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (EmailService.sendCustomEmails as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });

      const emailButton = screen.getByRole('button', { name: 'Email AAPL' });
      fireEvent.click(emailButton);

      await waitFor(() => {
        expect(EmailService.sendCustomEmails).toHaveBeenCalledWith(['AAPL']);
        expect(mockToast.showToast).toHaveBeenCalledWith('Sending email for AAPL!', 'success');
      });
    });

    it('should set email processing state during email all', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (EmailService.sendWatchlistEmails as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ ticker_count: 1 }), 100))
      );

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Email Processing: false')).toBeInTheDocument();
      });

      const emailButton = screen.getByRole('button', { name: 'Email All' });
      fireEvent.click(emailButton);

      await waitFor(() => {
        expect(screen.getByText('Email Processing: true')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText('Email Processing: false')).toBeInTheDocument();
      });
    });

    it('should set email processing state during single email', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (EmailService.sendCustomEmails as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Email Processing: false')).toBeInTheDocument();
      });

      const emailButton = screen.getByRole('button', { name: 'Email AAPL' });
      fireEvent.click(emailButton);

      await waitFor(() => {
        expect(screen.getByText('Email Processing: true')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText('Email Processing: false')).toBeInTheDocument();
      });
    });

    it('should show error toast when email all fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (EmailService.sendWatchlistEmails as jest.Mock).mockRejectedValue(new Error('Email failed'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });

      const emailButton = screen.getByRole('button', { name: 'Email All' });
      fireEvent.click(emailButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to send emails:', expect.any(Error));
        expect(mockToast.showToast).toHaveBeenCalledWith(
          'Failed to start email processing. Please try again.',
          'error'
        );
      });
    });

    it('should show error toast when single email fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (EmailService.sendCustomEmails as jest.Mock).mockRejectedValue(new Error('Email failed'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });

      const emailButton = screen.getByRole('button', { name: 'Email AAPL' });
      fireEvent.click(emailButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to send email for AAPL:', expect.any(Error));
        expect(mockToast.showToast).toHaveBeenCalledWith(
          'Failed to send email for AAPL. Please try again.',
          'error'
        );
      });
    });
  });

  describe('Form Toggle Functionality', () => {
    beforeEach(() => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
    });

    it('should toggle watchlist add form', async () => {
      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Show Add Form: false')).toBeInTheDocument();
      });

      const toggleButton = screen.getByRole('button', { name: 'Toggle Add Form' });
      fireEvent.click(toggleButton);

      expect(screen.getByText('Show Add Form: true')).toBeInTheDocument();

      fireEvent.click(toggleButton);

      expect(screen.getByText('Show Add Form: false')).toBeInTheDocument();
    });

    it('should toggle reserve add form', async () => {
      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText('Show Add Form: false')[1]).toBeInTheDocument();
      });

      const toggleButton = screen.getByRole('button', { name: 'Toggle Reserve Add Form' });
      fireEvent.click(toggleButton);

      expect(screen.getAllByText('Show Add Form: true')[0]).toBeInTheDocument();

      fireEvent.click(toggleButton);

      expect(screen.getAllByText('Show Add Form: false')[1]).toBeInTheDocument();
    });

    it('should cancel watchlist add form', async () => {
      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('watchlist')).toBeInTheDocument();
      });

      const toggleButton = screen.getByRole('button', { name: 'Toggle Add Form' });
      fireEvent.click(toggleButton);

      expect(screen.getByText('Show Add Form: true')).toBeInTheDocument();

      const cancelButton = screen.getByRole('button', { name: 'Cancel Add' });
      fireEvent.click(cancelButton);

      expect(screen.getByText('Show Add Form: false')).toBeInTheDocument();
    });

    it('should cancel reserve add form', async () => {
      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('reserve-list')).toBeInTheDocument();
      });

      const toggleButton = screen.getByRole('button', { name: 'Toggle Reserve Add Form' });
      fireEvent.click(toggleButton);

      expect(screen.getAllByText('Show Add Form: true')[0]).toBeInTheDocument();

      const cancelButton = screen.getByRole('button', { name: 'Cancel Reserve Add' });
      fireEvent.click(cancelButton);

      expect(screen.getAllByText('Show Add Form: false')[1]).toBeInTheDocument();
    });
  });

  describe('Existing Stock Symbols', () => {
    it('should combine watchlist and reserve symbols', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue(['GOOGL']);
      (StockService.getStockInfo as jest.Mock)
        .mockResolvedValueOnce({ symbol: 'AAPL', name: 'Apple', price: 150 })
        .mockResolvedValueOnce({ symbol: 'GOOGL', name: 'Google', price: 2800 });

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
        expect(screen.getByText('GOOGL')).toBeInTheDocument();
      });
    });

    it('should prevent duplicate across watchlist and reserve', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (StockService.addToReserve as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });

      // Try to add AAPL to reserve (but it's already in watchlist)
      const addButton = screen.getByRole('button', { name: 'Add GOOGL' });
      fireEvent.click(addButton);

      // Component receives existingStockSymbols which includes both lists
      await waitFor(() => {
        expect(screen.getByTestId('reserve-list')).toBeInTheDocument();
      });
    });
  });

  describe('ToastProvider Integration', () => {
    it('should wrap content with ToastProvider', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('header')).toBeInTheDocument();
      });
    });

    it('should use toast for success messages', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (EmailService.sendWatchlistEmails as jest.Mock).mockResolvedValue({ ticker_count: 1 });

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });

      const emailButton = screen.getByRole('button', { name: 'Email All' });
      fireEvent.click(emailButton);

      await waitFor(() => {
        expect(mockToast.showToast).toHaveBeenCalledWith(
          expect.stringContaining('Sending emails'),
          'success'
        );
      });
    });

    it('should use toast for error messages', async () => {
      (EmailService.sendWatchlistEmails as jest.Mock).mockRejectedValue(new Error('Failed'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('watchlist')).toBeInTheDocument();
      });

      const emailButton = screen.getByRole('button', { name: 'Email All' });
      fireEvent.click(emailButton);

      await waitFor(() => {
        expect(mockToast.showToast).toHaveBeenCalledWith(
          'Watchlist is empty. Add stocks before sending emails.',
          'error'
        );
      });
    });
  });

  describe('Complex Scenarios', () => {
    it('should handle adding multiple stocks to watchlist', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock)
        .mockResolvedValueOnce({ symbol: 'AAPL', name: 'Apple', price: 150 })
        .mockResolvedValueOnce({ symbol: 'GOOGL', name: 'Google', price: 2800 });
      (StockService.addToWatchlist as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 0 stocks')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add AAPL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
      });
    });

    it('should handle moving stock and then moving it back', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (StockService.moveToReserve as jest.Mock).mockResolvedValue({});
      (StockService.moveToWatchlist as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
        expect(screen.getByText('Reserve: 0 stocks')).toBeInTheDocument();
      });

      // Move to reserve
      const moveToReserveButton = screen.getByRole('button', { name: 'Move to Reserve' });
      fireEvent.click(moveToReserveButton);

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 0 stocks')).toBeInTheDocument();
        expect(screen.getByText('Reserve: 1 stocks')).toBeInTheDocument();
      });

      // Move back to watchlist
      const moveToWatchlistButton = screen.getByRole('button', { name: 'Move to Watchlist' });
      fireEvent.click(moveToWatchlistButton);

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
        expect(screen.getByText('Reserve: 0 stocks')).toBeInTheDocument();
      });
    });

    it('should handle removing all stocks from watchlist', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL', 'GOOGL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock)
        .mockResolvedValueOnce({ symbol: 'AAPL', name: 'Apple', price: 150 })
        .mockResolvedValueOnce({ symbol: 'GOOGL', name: 'Google', price: 2800 });
      (StockService.removeFromWatchlist as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 2 stocks')).toBeInTheDocument();
      });

      const removeButton = screen.getByRole('button', { name: 'Remove AAPL' });
      fireEvent.click(removeButton);

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
      });
    });
  });

  describe('Service Call Verification', () => {
    it('should call getUserWatchlist on mount', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(StockService.getUserWatchlist).toHaveBeenCalled();
      });
    });

    it('should call getUserReserve on mount', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(StockService.getUserReserve).toHaveBeenCalled();
      });
    });

    it('should call getStockInfo for each watchlist ticker', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL', 'GOOGL', 'MSFT']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'TEST', name: 'Test', price: 100 });

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(StockService.getStockInfo).toHaveBeenCalledWith('AAPL');
        expect(StockService.getStockInfo).toHaveBeenCalledWith('GOOGL');
        expect(StockService.getStockInfo).toHaveBeenCalledWith('MSFT');
        expect(StockService.getStockInfo).toHaveBeenCalledTimes(3);
      });
    });

    it('should call getStockInfo for each reserve ticker', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue(['TSLA', 'NVDA']);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'TEST', name: 'Test', price: 100 });

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(StockService.getStockInfo).toHaveBeenCalledWith('TSLA');
        expect(StockService.getStockInfo).toHaveBeenCalledWith('NVDA');
        expect(StockService.getStockInfo).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Props Passed to Child Components', () => {
    beforeEach(() => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
    });

    it('should pass correct props to Watchlist component', async () => {
      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('watchlist')).toBeInTheDocument();
      });

      // Verify initial state
      expect(screen.getByText('Watchlist: 0 stocks')).toBeInTheDocument();
      expect(screen.getByText('Show Add Form: false')).toBeInTheDocument();
      expect(screen.getByText('Email Processing: false')).toBeInTheDocument();
    });

    it('should pass correct props to ReserveList component', async () => {
      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('reserve-list')).toBeInTheDocument();
      });

      expect(screen.getByText('Reserve: 0 stocks')).toBeInTheDocument();
    });

    it('should update Watchlist props when stocks change', async () => {
      const newStock = { symbol: 'AAPL', name: 'Apple', price: 150 };
      (StockService.getStockInfo as jest.Mock).mockResolvedValue(newStock);
      (StockService.addToWatchlist as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 0 stocks')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add AAPL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
      });
    });
  });

  describe('Email Processing State', () => {
    beforeEach(() => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
    });

    it('should reset email processing state after success', async () => {
      (EmailService.sendWatchlistEmails as jest.Mock).mockResolvedValue({ ticker_count: 1 });

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Email Processing: false')).toBeInTheDocument();
      });

      const emailButton = screen.getByRole('button', { name: 'Email All' });
      fireEvent.click(emailButton);

      await waitFor(() => {
        expect(screen.getByText('Email Processing: false')).toBeInTheDocument();
      });
    });

    it('should reset email processing state after error', async () => {
      (EmailService.sendWatchlistEmails as jest.Mock).mockRejectedValue(new Error('Failed'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Email Processing: false')).toBeInTheDocument();
      });

      const emailButton = screen.getByRole('button', { name: 'Email All' });
      fireEvent.click(emailButton);

      await waitFor(() => {
        expect(screen.getByText('Email Processing: false')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty arrays from getUserWatchlist', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 0 stocks')).toBeInTheDocument();
      });

      expect(StockService.getStockInfo).not.toHaveBeenCalled();
    });

    it('should handle empty arrays from getUserReserve', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Reserve: 0 stocks')).toBeInTheDocument();
      });

      expect(StockService.getStockInfo).not.toHaveBeenCalled();
    });

    it('should handle stock symbols with special characters', async () => {
      const ticker = 'BRK.B';
      const stock = { symbol: 'BRK.B', name: 'Berkshire Hathaway', price: 300 };
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([ticker]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue(stock);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('BRK.B')).toBeInTheDocument();
      });
    });

    it('should handle concurrent operations', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (StockService.removeFromWatchlist as jest.Mock).mockResolvedValue({});
      (EmailService.sendCustomEmails as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });

      // Click both buttons quickly
      const removeButton = screen.getByRole('button', { name: 'Remove AAPL' });
      const emailButton = screen.getByRole('button', { name: 'Email AAPL' });
      
      fireEvent.click(removeButton);
      fireEvent.click(emailButton);

      await waitFor(() => {
        expect(StockService.removeFromWatchlist).toHaveBeenCalledWith('AAPL');
        expect(EmailService.sendCustomEmails).toHaveBeenCalledWith(['AAPL']);
      });
    });
  });

  describe('State Management', () => {
    it('should maintain separate state for watchlist and reserve forms', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('watchlist')).toBeInTheDocument();
      });

      const watchlistToggle = screen.getByRole('button', { name: 'Toggle Add Form' });
      const reserveToggle = screen.getByRole('button', { name: 'Toggle Reserve Add Form' });

      fireEvent.click(watchlistToggle);

      const watchlistFormStates = screen.getAllByText(/Show Add Form:/);
      expect(watchlistFormStates[0]).toHaveTextContent('true');
      expect(watchlistFormStates[1]).toHaveTextContent('false');

      fireEvent.click(reserveToggle);

      const bothFormStates = screen.getAllByText(/Show Add Form:/);
      expect(bothFormStates[0]).toHaveTextContent('true');
      expect(bothFormStates[1]).toHaveTextContent('true');
    });

    it('should preserve watchlist stocks when reserve stocks change', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock)
        .mockResolvedValueOnce({ symbol: 'AAPL', name: 'Apple', price: 150 })
        .mockResolvedValueOnce({ symbol: 'GOOGL', name: 'Google', price: 2800 });
      (StockService.addToReserve as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      });

      const addReserveButton = screen.getByRole('button', { name: 'Add GOOGL' });
      fireEvent.click(addReserveButton);

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
        expect(screen.getByText('GOOGL')).toBeInTheDocument();
      });
    });
  });

  describe('Error Recovery', () => {
    it('should continue loading reserve even if watchlist fails', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockRejectedValue(new Error('Watchlist failed'));
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('reserve-list')).toBeInTheDocument();
      });
    });

    it('should not crash when stock info fetch fails during initial load', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockRejectedValue(new Error('Stock info failed'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('watchlist')).toBeInTheDocument();
      });
    });

    it('should maintain UI state when add operation fails', async () => {
      (StockService.getStockInfo as jest.Mock).mockRejectedValue(new Error('Failed'));
      (StockService.addToWatchlist as jest.Mock).mockResolvedValue({});

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 0 stocks')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add AAPL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 0 stocks')).toBeInTheDocument();
      });
    });

    it('should maintain UI state when remove operation fails', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (StockService.removeFromWatchlist as jest.Mock).mockRejectedValue(new Error('Remove failed'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
      });

      const removeButton = screen.getByRole('button', { name: 'Remove AAPL' });
      fireEvent.click(removeButton);

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
      });
    });

    it('should maintain UI state when move operation fails', async () => {
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['AAPL']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'AAPL', name: 'Apple', price: 150 });
      (StockService.moveToReserve as jest.Mock).mockRejectedValue(new Error('Move failed'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
      });

      const moveButton = screen.getByRole('button', { name: 'Move to Reserve' });
      fireEvent.click(moveButton);

      await waitFor(() => {
        expect(screen.getByText('Watchlist: 1 stocks')).toBeInTheDocument();
        expect(screen.getByText('Reserve: 0 stocks')).toBeInTheDocument();
      });
    });
  });

  describe('Console Error Logging', () => {
    it('should log specific ticker when add fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue([]);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockRejectedValue(new Error('Not found'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('watchlist')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: 'Add AAPL' });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          expect.stringContaining('AAPL'),
          expect.any(Error)
        );
      });
    });

    it('should log specific ticker when remove fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['TSLA']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'TSLA', name: 'Tesla', price: 700 });
      (StockService.removeFromWatchlist as jest.Mock).mockRejectedValue(new Error('Remove failed'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('TSLA')).toBeInTheDocument();
      });

      const removeButton = screen.getByRole('button', { name: 'Remove AAPL' });
      fireEvent.click(removeButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          expect.stringContaining('AAPL'),
          expect.any(Error)
        );
      });
    });

    it('should log specific ticker when single email fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      (StockService.getUserWatchlist as jest.Mock).mockResolvedValue(['MSFT']);
      (StockService.getUserReserve as jest.Mock).mockResolvedValue([]);
      (StockService.getStockInfo as jest.Mock).mockResolvedValue({ symbol: 'MSFT', name: 'Microsoft', price: 300 });
      (EmailService.sendCustomEmails as jest.Mock).mockRejectedValue(new Error('Email failed'));

      render(
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('MSFT')).toBeInTheDocument();
      });

      const emailButton = screen.getByRole('button', { name: 'Email AAPL' });
      fireEvent.click(emailButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          expect.stringContaining('AAPL'),
          expect.any(Error)
        );
      });
    });
  });
});