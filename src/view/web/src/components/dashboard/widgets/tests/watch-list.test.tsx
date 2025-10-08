import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Watchlist } from '../watch-list.tsx';
import { Stock } from '../../utils/types.ts';

// Mocks
jest.mock('../stock-card.tsx', () => ({
  StockCard: ({ stock, onRemove, onMoveToReserve, onSendEmail, isReserveList }: any) => (
    <div data-testid={`stock-card-${stock.symbol}`}>
      <span>{stock.symbol}</span>
      <span>{stock.name}</span>
      <button onClick={() => onRemove(stock.symbol)}>Remove</button>
      <button onClick={() => onMoveToReserve && onMoveToReserve(stock.symbol)}>Move to Reserve</button>
      <button onClick={() => onSendEmail && onSendEmail(stock.symbol)}>Send Email</button>
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

const renderWatchlist = (props = {}) => {
  const defaultProps = {
    stocks: [],
    onRemoveStock: jest.fn(),
    onAddStock: jest.fn(),
    showAddForm: false,
    existingStocks: [],
    onCancelAddForm: jest.fn(),
    onToggleAddForm: jest.fn(),
    onMoveToReserve: jest.fn(),
    onEmailAll: jest.fn(),
    onSendEmail: jest.fn(),
    isEmailProcessing: false,
    ...props
  };

  return {
    ...render(<Watchlist {...defaultProps} />),
    ...defaultProps
  };
};

describe('Watchlist Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render watchlist section with title', () => {
      renderWatchlist();

      expect(screen.getByRole('heading', { name: 'Watchlist' })).toBeInTheDocument();
    });

    it('should render add button with aria-label', () => {
      renderWatchlist();

      const addButton = screen.getByRole('button', { name: 'Add stock to watchlist' });
      expect(addButton).toBeInTheDocument();
      expect(addButton).toHaveTextContent('+');
    });

    it('should render Email All button when onEmailAll is provided', () => {
      renderWatchlist({ onEmailAll: jest.fn(), stocks: mockStocks });

      expect(screen.getByRole('button', { name: '✉ All' })).toBeInTheDocument();
    });

    it('should not render Email All button when onEmailAll is undefined', () => {
      renderWatchlist({ onEmailAll: undefined, stocks: mockStocks });

      expect(screen.queryByRole('button', { name: '✉ All' })).not.toBeInTheDocument();
    });

    it('should render empty state when no stocks', () => {
      renderWatchlist();

      expect(screen.getByText('Your watchlist is empty')).toBeInTheDocument();
      expect(screen.getByText("Add stocks you're interested in to keep track of their performance")).toBeInTheDocument();
    });

    it('should render empty state icon', () => {
      renderWatchlist();

      expect(screen.getByText('📈')).toBeInTheDocument();
    });

    it('should not render add form initially', () => {
      renderWatchlist();

      expect(screen.queryByTestId('add-stock-form')).not.toBeInTheDocument();
    });

    it('should render add form when showAddForm is true', () => {
      renderWatchlist({ showAddForm: true });

      expect(screen.getByTestId('add-stock-form')).toBeInTheDocument();
    });

    it('should not render empty state when stocks exist', () => {
      renderWatchlist({ stocks: mockStocks });

      expect(screen.queryByText('Your watchlist is empty')).not.toBeInTheDocument();
    });

    it('should render as main landmark', () => {
      renderWatchlist();

      expect(screen.getByRole('main')).toBeInTheDocument();
    });
  });

  describe('Stock Display', () => {
    it('should render all stocks in the list', () => {
      renderWatchlist({ stocks: mockStocks });

      expect(screen.getByTestId('stock-card-AAPL')).toBeInTheDocument();
      expect(screen.getByTestId('stock-card-GOOGL')).toBeInTheDocument();
      expect(screen.getByTestId('stock-card-MSFT')).toBeInTheDocument();
    });

    it('should render stocks in a grid with proper ARIA labels', () => {
      renderWatchlist({ stocks: mockStocks });

      const stocksGrid = screen.getByRole('list', { name: 'Stock watchlist' });
      expect(stocksGrid).toBeInTheDocument();
      expect(stocksGrid).toHaveClass('stocks-grid');
    });

    it('should render each stock with listitem role', () => {
      renderWatchlist({ stocks: mockStocks });

      const listItems = screen.getAllByRole('listitem');
      expect(listItems).toHaveLength(3);
    });

    it('should pass correct props to StockCard', () => {
      renderWatchlist({ stocks: [mockStocks[0]] });

      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
      expect(screen.getByTestId('is-reserve')).toHaveTextContent('watchlist');
    });

    it('should pass isReserveList as false to all StockCards', () => {
      renderWatchlist({ stocks: mockStocks });

      const reserveFlags = screen.getAllByTestId('is-reserve');
      reserveFlags.forEach(flag => {
        expect(flag).toHaveTextContent('watchlist');
      });
    });
  });

  describe('Add Stock Form', () => {
    it('should show add form when toggle button is clicked', () => {
      const { onToggleAddForm } = renderWatchlist();
      const addButton = screen.getByRole('button', { name: 'Add stock to watchlist' });

      fireEvent.click(addButton);

      expect(onToggleAddForm).toHaveBeenCalled();
    });

    it('should pass correct targetList to AddStockForm', () => {
      renderWatchlist({ showAddForm: true });

      expect(screen.getByTestId('target-list')).toHaveTextContent('watchlist');
    });

    it('should pass existing stocks to AddStockForm', () => {
      const existingStocks = ['AAPL', 'GOOGL', 'MSFT'];
      renderWatchlist({ showAddForm: true, existingStocks });

      expect(screen.getByTestId('existing-stocks')).toHaveTextContent('AAPL,GOOGL,MSFT');
    });

    it('should call onAddStock when adding through form', () => {
      const { onAddStock } = renderWatchlist({ showAddForm: true });
      const addButton = screen.getByRole('button', { name: 'Add' });

      fireEvent.click(addButton);

      expect(onAddStock).toHaveBeenCalledWith('NEWSTOCK');
    });

    it('should call onCancelAddForm when cancelling form', () => {
      const { onCancelAddForm } = renderWatchlist({ showAddForm: true });
      const cancelButton = screen.getByRole('button', { name: 'Cancel' });

      fireEvent.click(cancelButton);

      expect(onCancelAddForm).toHaveBeenCalled();
    });

    it('should show add form alongside stocks when both exist', () => {
      renderWatchlist({ 
        stocks: mockStocks, 
        showAddForm: true 
      });

      expect(screen.getByTestId('add-stock-form')).toBeInTheDocument();
      expect(screen.getByTestId('stock-card-AAPL')).toBeInTheDocument();
    });
  });

  describe('Stock Removal', () => {
    it('should call onRemoveStock with correct symbol', () => {
      const { onRemoveStock } = renderWatchlist({ stocks: [mockStocks[0]] });
      const removeButton = screen.getByRole('button', { name: 'Remove' });

      fireEvent.click(removeButton);

      expect(onRemoveStock).toHaveBeenCalledWith('AAPL');
    });

    it('should handle removal for multiple different stocks', () => {
      const { onRemoveStock } = renderWatchlist({ stocks: mockStocks });
      const removeButtons = screen.getAllByRole('button', { name: 'Remove' });

      fireEvent.click(removeButtons[0]);
      expect(onRemoveStock).toHaveBeenCalledWith('AAPL');

      fireEvent.click(removeButtons[1]);
      expect(onRemoveStock).toHaveBeenCalledWith('GOOGL');

      fireEvent.click(removeButtons[2]);
      expect(onRemoveStock).toHaveBeenCalledWith('MSFT');
    });
  });

  describe('Move to Reserve', () => {
    it('should call onMoveToReserve with correct symbol', () => {
      const { onMoveToReserve } = renderWatchlist({ stocks: [mockStocks[0]] });
      const moveButton = screen.getByRole('button', { name: 'Move to Reserve' });

      fireEvent.click(moveButton);

      expect(onMoveToReserve).toHaveBeenCalledWith('AAPL');
    });

    it('should handle moving multiple different stocks', () => {
      const { onMoveToReserve } = renderWatchlist({ stocks: mockStocks });
      const moveButtons = screen.getAllByRole('button', { name: 'Move to Reserve' });

      fireEvent.click(moveButtons[0]);
      expect(onMoveToReserve).toHaveBeenCalledWith('AAPL');

      fireEvent.click(moveButtons[1]);
      expect(onMoveToReserve).toHaveBeenCalledWith('GOOGL');

      fireEvent.click(moveButtons[2]);
      expect(onMoveToReserve).toHaveBeenCalledWith('MSFT');
    });
  });

  describe('Email Functionality', () => {
    it('should call onSendEmail with correct symbol', () => {
      const { onSendEmail } = renderWatchlist({ stocks: [mockStocks[0]] });
      const emailButton = screen.getByRole('button', { name: 'Send Email' });

      fireEvent.click(emailButton);

      expect(onSendEmail).toHaveBeenCalledWith('AAPL');
    });

    it('should handle sending emails for multiple different stocks', () => {
      const { onSendEmail } = renderWatchlist({ stocks: mockStocks });
      const emailButtons = screen.getAllByRole('button', { name: 'Send Email' });

      fireEvent.click(emailButtons[0]);
      expect(onSendEmail).toHaveBeenCalledWith('AAPL');

      fireEvent.click(emailButtons[1]);
      expect(onSendEmail).toHaveBeenCalledWith('GOOGL');

      fireEvent.click(emailButtons[2]);
      expect(onSendEmail).toHaveBeenCalledWith('MSFT');
    });

    it('should call onEmailAll when Email All button is clicked', () => {
      const { onEmailAll } = renderWatchlist({ stocks: mockStocks });
      const emailAllButton = screen.getByRole('button', { name: '✉ All' });

      fireEvent.click(emailAllButton);

      expect(onEmailAll).toHaveBeenCalled();
    });

    it('should disable Email All button when isEmailProcessing is true', () => {
      renderWatchlist({ stocks: mockStocks, isEmailProcessing: true });
      const emailAllButton = screen.getByRole('button', { name: '✉ All' });

      expect(emailAllButton).toBeDisabled();
    });

    it('should disable Email All button when stocks list is empty', () => {
      renderWatchlist({ stocks: [], onEmailAll: jest.fn() });
      const emailAllButton = screen.getByRole('button', { name: '✉ All' });

      expect(emailAllButton).toBeDisabled();
    });

    it('should enable Email All button when not processing and stocks exist', () => {
      renderWatchlist({ 
        stocks: mockStocks, 
        isEmailProcessing: false 
      });
      const emailAllButton = screen.getByRole('button', { name: '✉ All' });

      expect(emailAllButton).not.toBeDisabled();
    });

    it('should disable Email All button when processing even with stocks', () => {
      renderWatchlist({ 
        stocks: mockStocks, 
        isEmailProcessing: true 
      });
      const emailAllButton = screen.getByRole('button', { name: '✉ All' });

      expect(emailAllButton).toBeDisabled();
    });
  });

  describe('Empty State', () => {
    it('should display correct empty state title', () => {
      renderWatchlist();

      const title = screen.getByText('Your watchlist is empty');
      expect(title).toHaveClass('empty-state-title');
    });

    it('should display correct empty state description', () => {
      renderWatchlist();

      const description = screen.getByText("Add stocks you're interested in to keep track of their performance");
      expect(description).toHaveClass('empty-state-description');
    });

    it('should display empty state icon with correct class', () => {
      renderWatchlist();

      const icon = screen.getByText('📈');
      expect(icon).toHaveClass('empty-state-icon');
    });

    it('should not show empty state when at least one stock exists', () => {
      renderWatchlist({ stocks: [mockStocks[0]] });

      expect(screen.queryByText('Your watchlist is empty')).not.toBeInTheDocument();
    });
  });

  describe('Component Structure', () => {
    it('should have correct main element class', () => {
      const { container } = renderWatchlist();

      expect(container.querySelector('.stocks-section')).toBeInTheDocument();
    });

    it('should have correct section header structure', () => {
      const { container } = renderWatchlist();

      const header = container.querySelector('.section-header');
      expect(header).toBeInTheDocument();
      expect(header?.querySelector('.section-title')).toBeInTheDocument();
      expect(header?.querySelector('.watchlist-buttons')).toBeInTheDocument();
    });

    it('should contain buttons within watchlist-buttons container', () => {
      const { container } = renderWatchlist({ stocks: mockStocks });

      const buttonsContainer = container.querySelector('.watchlist-buttons');
      const buttons = buttonsContainer?.querySelectorAll('button');
      
      expect(buttons).toBeTruthy();
      expect(buttons!.length).toBeGreaterThan(0);
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      renderWatchlist();

      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('Watchlist');
    });

    it('should have accessible list structure when stocks present', () => {
      renderWatchlist({ stocks: mockStocks });

      const list = screen.getByRole('list', { name: 'Stock watchlist' });
      expect(list).toBeInTheDocument();
      
      const listItems = screen.getAllByRole('listitem');
      expect(listItems).toHaveLength(mockStocks.length);
    });

    it('should have accessible add button', () => {
      renderWatchlist();

      const button = screen.getByRole('button', { name: 'Add stock to watchlist' });
      expect(button).toHaveAttribute('type', 'button');
    });

    it('should have accessible Email All button', () => {
      renderWatchlist({ stocks: mockStocks });

      const button = screen.getByRole('button', { name: '✉ All' });
      expect(button).toHaveAttribute('type', 'button');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty stocks array', () => {
      renderWatchlist({ stocks: [] });

      expect(screen.getByText('Your watchlist is empty')).toBeInTheDocument();
      expect(screen.queryByRole('list', { name: 'Stock watchlist' })).not.toBeInTheDocument();
    });

    it('should handle single stock', () => {
      renderWatchlist({ stocks: [mockStocks[0]] });

      expect(screen.getByTestId('stock-card-AAPL')).toBeInTheDocument();
      expect(screen.queryByText('Your watchlist is empty')).not.toBeInTheDocument();
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

      renderWatchlist({ stocks: manyStocks });

      const listItems = screen.getAllByRole('listitem');
      expect(listItems).toHaveLength(50);
    });

    it('should handle empty existingStocks array', () => {
      renderWatchlist({ showAddForm: true, existingStocks: [] });

      expect(screen.getByTestId('existing-stocks')).toHaveTextContent('');
    });

    it('should handle missing optional callbacks', () => {
      renderWatchlist({ 
        stocks: mockStocks,
        onMoveToReserve: undefined,
        onEmailAll: undefined,
        onSendEmail: undefined
      });

      expect(screen.getByTestId('stock-card-AAPL')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: '✉ All' })).not.toBeInTheDocument();
    });

    it('should disable Email All when processing with empty list', () => {
      renderWatchlist({ 
        stocks: [], 
        isEmailProcessing: true, 
        onEmailAll: jest.fn() 
      });
      const emailAllButton = screen.getByRole('button', { name: '✉ All' });

      expect(emailAllButton).toBeDisabled();
    });
  });
});