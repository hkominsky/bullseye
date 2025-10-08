import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ReserveList } from '../reserve-list.tsx';
import { Stock } from '../../utils/types.ts';

// Mock child components
jest.mock('../stock-card.tsx', () => ({
  StockCard: ({ stock, onRemove, onMoveToWatchlist, isReserveList }: any) => (
    <div data-testid={`stock-card-${stock.symbol}`}>
      <span>{stock.symbol}</span>
      <span>{stock.name}</span>
      <button onClick={() => onRemove(stock.symbol)}>Remove</button>
      <button onClick={() => onMoveToWatchlist(stock.symbol)}>Move to Watchlist</button>
      <span data-testid="is-reserve">{isReserveList ? 'reserve' : 'watchlist'}</span>
    </div>
  )
}));

jest.mock('../add-stock-form.tsx', () => ({
  AddStockForm: ({ onAddStock, onCancel, existingStocks, targetList }: any) => (
    <div data-testid="add-stock-form">
      <span data-testid="target-list">{targetList}</span>
      <span data-testid="existing-stocks">{existingStocks.join(',')}</span>
      <button onClick={() => onAddStock('NEWSTOCK')}>Add</button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  )
}));

const mockStocks: Stock[] = [
  {
    symbol: 'AAPL',
    name: 'Apple Inc.',
    price: 150.25,
    priceChange: 2.5,
    percentChange: 1.69,
    priceHistory: [
      { timestamp: '2025-10-01T00:00:00Z', price: 148.00 },
      { timestamp: '2025-10-02T00:00:00Z', price: 149.50 },
      { timestamp: '2025-10-03T00:00:00Z', price: 150.25 }
    ],
    marketCap: 2400000000000,
    volume: 52000000,
    avgVolume: 50000000,
    relativeVolume: 1.04,
    nextEarningsDate: '2025-11-01',
    peRatio: 28.5,
    trailingEPS: 5.67,
    forwardEPS: 6.12,
    recommendation: 'Buy'
  },
  {
    symbol: 'GOOGL',
    name: 'Alphabet Inc.',
    price: 2800.50,
    priceChange: -15.75,
    percentChange: -0.56,
    priceHistory: [
      { timestamp: '2025-10-01T00:00:00Z', price: 2820.00 },
      { timestamp: '2025-10-02T00:00:00Z', price: 2815.25 },
      { timestamp: '2025-10-03T00:00:00Z', price: 2800.50 }
    ],
    marketCap: 1800000000000,
    volume: 28000000,
    avgVolume: 30000000,
    relativeVolume: 0.93,
    nextEarningsDate: '2025-10-28',
    peRatio: 24.8,
    trailingEPS: 112.35,
    forwardEPS: 118.50,
    recommendation: 'Hold'
  },
  {
    symbol: 'MSFT',
    name: 'Microsoft Corporation',
    price: 305.00,
    priceChange: 5.25,
    percentChange: 1.75,
    priceHistory: [
      { timestamp: '2025-10-01T00:00:00Z', price: 300.00 },
      { timestamp: '2025-10-02T00:00:00Z', price: 302.50 },
      { timestamp: '2025-10-03T00:00:00Z', price: 305.00 }
    ],
    marketCap: 2300000000000,
    volume: 24000000,
    avgVolume: 25000000,
    relativeVolume: 0.96,
    nextEarningsDate: '2025-10-25',
    peRatio: 32.1,
    trailingEPS: 9.50,
    forwardEPS: 10.25,
    recommendation: 'Strong Buy'
  }
];

const renderReserveList = (props = {}) => {
  const defaultProps = {
    stocks: [],
    onRemoveStock: jest.fn(),
    onAddStock: jest.fn(),
    showAddForm: false,
    existingStocks: [],
    onCancelAddForm: jest.fn(),
    onToggleAddForm: jest.fn(),
    onMoveToWatchlist: jest.fn(),
    ...props
  };

  return {
    ...render(<ReserveList {...defaultProps} />),
    ...defaultProps
  };
};

describe('ReserveList Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render reserve section with title', () => {
      renderReserveList();

      expect(screen.getByRole('heading', { name: 'Reserve' })).toBeInTheDocument();
    });

    it('should render add button', () => {
      renderReserveList();

      expect(screen.getByRole('button', { name: '+' })).toBeInTheDocument();
    });

    it('should render empty state when no stocks', () => {
      renderReserveList();

      expect(screen.getByText('Your reserve list is empty')).toBeInTheDocument();
      expect(screen.getByText('Add stocks to your reserve list to keep track without email notifications')).toBeInTheDocument();
    });

    it('should render empty state icon', () => {
      renderReserveList();

      expect(screen.getByText('📈')).toBeInTheDocument();
    });

    it('should not render add form initially', () => {
      renderReserveList();

      expect(screen.queryByTestId('add-stock-form')).not.toBeInTheDocument();
    });

    it('should render add form when showAddForm is true', () => {
      renderReserveList({ showAddForm: true });

      expect(screen.getByTestId('add-stock-form')).toBeInTheDocument();
    });

    it('should not render empty state when stocks exist', () => {
      renderReserveList({ stocks: mockStocks });

      expect(screen.queryByText('Your reserve list is empty')).not.toBeInTheDocument();
    });
  });

  describe('Stock Display', () => {
    it('should render all stocks in the list', () => {
      renderReserveList({ stocks: mockStocks });

      expect(screen.getByTestId('stock-card-AAPL')).toBeInTheDocument();
      expect(screen.getByTestId('stock-card-GOOGL')).toBeInTheDocument();
      expect(screen.getByTestId('stock-card-MSFT')).toBeInTheDocument();
    });

    it('should render stocks in a grid with proper ARIA labels', () => {
      renderReserveList({ stocks: mockStocks });

      const stocksGrid = screen.getByRole('list', { name: 'Reserve stocks' });
      expect(stocksGrid).toBeInTheDocument();
      expect(stocksGrid).toHaveClass('stocks-grid');
    });

    it('should render each stock with listitem role', () => {
      renderReserveList({ stocks: mockStocks });

      const listItems = screen.getAllByRole('listitem');
      expect(listItems).toHaveLength(3);
    });

    it('should pass correct props to StockCard', () => {
      renderReserveList({ stocks: [mockStocks[0]] });

      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
      expect(screen.getByTestId('is-reserve')).toHaveTextContent('reserve');
    });

    it('should pass isReserveList as true to all StockCards', () => {
      renderReserveList({ stocks: mockStocks });

      const reserveFlags = screen.getAllByTestId('is-reserve');
      reserveFlags.forEach(flag => {
        expect(flag).toHaveTextContent('reserve');
      });
    });
  });

  describe('Add Stock Form', () => {
    it('should show add form when toggle button is clicked', () => {
      const { onToggleAddForm } = renderReserveList();
      const addButton = screen.getByRole('button', { name: '+' });

      fireEvent.click(addButton);

      expect(onToggleAddForm).toHaveBeenCalled();
    });

    it('should pass correct targetList to AddStockForm', () => {
      renderReserveList({ showAddForm: true });

      expect(screen.getByTestId('target-list')).toHaveTextContent('reserve');
    });

    it('should pass existing stocks to AddStockForm', () => {
      const existingStocks = ['AAPL', 'GOOGL', 'MSFT'];
      renderReserveList({ showAddForm: true, existingStocks });

      expect(screen.getByTestId('existing-stocks')).toHaveTextContent('AAPL,GOOGL,MSFT');
    });

    it('should call onAddStock when adding through form', () => {
      const { onAddStock } = renderReserveList({ showAddForm: true });
      const addButton = screen.getByRole('button', { name: 'Add' });

      fireEvent.click(addButton);

      expect(onAddStock).toHaveBeenCalledWith('NEWSTOCK');
    });

    it('should call onCancelAddForm when cancelling form', () => {
      const { onCancelAddForm } = renderReserveList({ showAddForm: true });
      const cancelButton = screen.getByRole('button', { name: 'Cancel' });

      fireEvent.click(cancelButton);

      expect(onCancelAddForm).toHaveBeenCalled();
    });

    it('should show add form alongside stocks when both exist', () => {
      renderReserveList({ 
        stocks: mockStocks, 
        showAddForm: true 
      });

      expect(screen.getByTestId('add-stock-form')).toBeInTheDocument();
      expect(screen.getByTestId('stock-card-AAPL')).toBeInTheDocument();
    });
  });

  describe('Stock Removal', () => {
    it('should call onRemoveStock with correct symbol', () => {
      const { onRemoveStock } = renderReserveList({ stocks: [mockStocks[0]] });
      const removeButton = screen.getByRole('button', { name: 'Remove' });

      fireEvent.click(removeButton);

      expect(onRemoveStock).toHaveBeenCalledWith('AAPL');
    });

    it('should handle removal for multiple different stocks', () => {
      const { onRemoveStock } = renderReserveList({ stocks: mockStocks });
      const removeButtons = screen.getAllByRole('button', { name: 'Remove' });

      fireEvent.click(removeButtons[0]);
      expect(onRemoveStock).toHaveBeenCalledWith('AAPL');

      fireEvent.click(removeButtons[1]);
      expect(onRemoveStock).toHaveBeenCalledWith('GOOGL');

      fireEvent.click(removeButtons[2]);
      expect(onRemoveStock).toHaveBeenCalledWith('MSFT');
    });
  });

  describe('Move to Watchlist', () => {
    it('should call onMoveToWatchlist with correct symbol', () => {
      const { onMoveToWatchlist } = renderReserveList({ stocks: [mockStocks[0]] });
      const moveButton = screen.getByRole('button', { name: 'Move to Watchlist' });

      fireEvent.click(moveButton);

      expect(onMoveToWatchlist).toHaveBeenCalledWith('AAPL');
    });

    it('should handle moving multiple different stocks', () => {
      const { onMoveToWatchlist } = renderReserveList({ stocks: mockStocks });
      const moveButtons = screen.getAllByRole('button', { name: 'Move to Watchlist' });

      fireEvent.click(moveButtons[0]);
      expect(onMoveToWatchlist).toHaveBeenCalledWith('AAPL');

      fireEvent.click(moveButtons[1]);
      expect(onMoveToWatchlist).toHaveBeenCalledWith('GOOGL');

      fireEvent.click(moveButtons[2]);
      expect(onMoveToWatchlist).toHaveBeenCalledWith('MSFT');
    });
  });

  describe('Empty State', () => {
    it('should display correct empty state title', () => {
      renderReserveList();

      const title = screen.getByText('Your reserve list is empty');
      expect(title).toHaveClass('empty-state-title');
    });

    it('should display correct empty state description', () => {
      renderReserveList();

      const description = screen.getByText('Add stocks to your reserve list to keep track without email notifications');
      expect(description).toHaveClass('empty-state-description');
    });

    it('should display empty state icon with correct class', () => {
      renderReserveList();

      const icon = screen.getByText('📈');
      expect(icon).toHaveClass('empty-state-icon');
    });

    it('should not show empty state when at least one stock exists', () => {
      renderReserveList({ stocks: [mockStocks[0]] });

      expect(screen.queryByText('Your reserve list is empty')).not.toBeInTheDocument();
    });
  });

  describe('Component Structure', () => {
    it('should have correct main element class', () => {
      const { container } = renderReserveList();

      expect(container.querySelector('.reserve-section')).toBeInTheDocument();
    });

    it('should have correct section header structure', () => {
      const { container } = renderReserveList();

      const header = container.querySelector('.section-header');
      expect(header).toBeInTheDocument();
      expect(header?.querySelector('.section-title')).toBeInTheDocument();
      expect(header?.querySelector('.watchlist-buttons')).toBeInTheDocument();
    });

    it('should render as main landmark', () => {
      renderReserveList();

      expect(screen.getByRole('main')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      renderReserveList();

      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('Reserve');
    });

    it('should have accessible list structure when stocks present', () => {
      renderReserveList({ stocks: mockStocks });

      const list = screen.getByRole('list', { name: 'Reserve stocks' });
      expect(list).toBeInTheDocument();
      
      const listItems = screen.getAllByRole('listitem');
      expect(listItems).toHaveLength(mockStocks.length);
    });

    it('should have accessible button', () => {
      renderReserveList();

      const button = screen.getByRole('button', { name: '+' });
      expect(button).toHaveAttribute('type', 'button');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty stocks array', () => {
      renderReserveList({ stocks: [] });

      expect(screen.getByText('Your reserve list is empty')).toBeInTheDocument();
      expect(screen.queryByRole('list', { name: 'Reserve stocks' })).not.toBeInTheDocument();
    });

    it('should handle single stock', () => {
      renderReserveList({ stocks: [mockStocks[0]] });

      expect(screen.getByTestId('stock-card-AAPL')).toBeInTheDocument();
      expect(screen.queryByText('Your reserve list is empty')).not.toBeInTheDocument();
    });

    it('should handle large number of stocks', () => {
      const manyStocks = Array.from({ length: 50 }, (_, i) => ({
        symbol: `STOCK${i}`,
        name: `Company ${i}`,
        price: 100 + i,
        priceChange: i % 2 === 0 ? 1 : -1,
        percentChange: i % 2 === 0 ? 0.5 : -0.5,
        priceHistory: [{ timestamp: '2025-10-01T00:00:00Z', price: 100 + i }],
        marketCap: 1000000000 * i,
        volume: 1000000 * i,
        avgVolume: 1000000 * i,
        relativeVolume: 1.0,
        nextEarningsDate: '2025-11-01',
        peRatio: 20.0,
        trailingEPS: 5.0,
        forwardEPS: 5.5,
        recommendation: 'Hold'
      }));

      renderReserveList({ stocks: manyStocks });

      const listItems = screen.getAllByRole('listitem');
      expect(listItems).toHaveLength(50);
    });

    it('should handle empty existingStocks array', () => {
      renderReserveList({ showAddForm: true, existingStocks: [] });

      expect(screen.getByTestId('existing-stocks')).toHaveTextContent('');
    });
  });
});