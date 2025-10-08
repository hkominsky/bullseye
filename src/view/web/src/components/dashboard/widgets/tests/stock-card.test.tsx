import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { StockCard } from '../stock-card.tsx';
import { Stock } from '../../utils/types.ts';

// Mocks
jest.mock('../stock-chart.tsx', () => ({
  StockChart: ({ data, changePercent }: any) => (
    <div data-testid="stock-chart">
      <span data-testid="chart-data-length">{data.length}</span>
      <span data-testid="chart-change-percent">{changePercent}</span>
    </div>
  )
}));

const mockStock: Stock = {
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
};

const mockNegativeStock: Stock = {
  ...mockStock,
  symbol: 'TSLA',
  name: 'Tesla Inc.',
  price: 200.00,
  priceChange: -5.25,
  percentChange: -2.56,
  priceHistory: [
    { timestamp: '2025-10-01T00:00:00Z', price: 205.25 },
    { timestamp: '2025-10-02T00:00:00Z', price: 202.50 },
    { timestamp: '2025-10-03T00:00:00Z', price: 200.00 }
  ]
};

const renderStockCard = (props = {}) => {
  const defaultProps = {
    stock: mockStock,
    onRemove: jest.fn(),
    onMoveToReserve: jest.fn(),
    onMoveToWatchlist: jest.fn(),
    onSendEmail: jest.fn(),
    isReserveList: false,
    ...props
  };

  return {
    ...render(<StockCard {...defaultProps} />),
    ...defaultProps
  };
};

describe('StockCard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render stock symbol and name', () => {
      renderStockCard();

      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
    });

    it('should render stock symbol with correct class', () => {
      renderStockCard();

      const symbol = screen.getByText('AAPL');
      expect(symbol).toHaveClass('stock-symbol');
    });

    it('should render stock name with correct class', () => {
      renderStockCard();

      const name = screen.getByText('Apple Inc.');
      expect(name).toHaveClass('stock-name');
    });

    it('should render menu button', () => {
      renderStockCard();

      const menuButton = screen.getByTitle('Stock options');
      expect(menuButton).toBeInTheDocument();
      expect(menuButton).toHaveTextContent('⋯');
    });

    it('should not show dropdown menu initially', () => {
      renderStockCard();

      expect(screen.queryByText('✖ Delete')).not.toBeInTheDocument();
    });

    it('should render stock chart', () => {
      renderStockCard();

      expect(screen.getByTestId('stock-chart')).toBeInTheDocument();
    });
  });

  describe('Price Display', () => {
    it('should display current price correctly', () => {
      renderStockCard();

      expect(screen.getByText('150.25')).toBeInTheDocument();
    });

    it('should display price change with plus sign for positive', () => {
      renderStockCard();

      expect(screen.getByText('(+2.50)')).toBeInTheDocument();
    });

    it('should display price change without plus sign for negative', () => {
      renderStockCard({ stock: mockNegativeStock });

      expect(screen.getByText('(-5.25)')).toBeInTheDocument();
    });

    it('should display percent change with plus sign and up arrow for positive', () => {
      renderStockCard();

      expect(screen.getByText('+1.69% 🡩')).toBeInTheDocument();
    });

    it('should display percent change with down arrow for negative', () => {
      renderStockCard({ stock: mockNegativeStock });

      expect(screen.getByText('-2.56% 🡫')).toBeInTheDocument();
    });

    it('should apply positive class for positive change', () => {
      renderStockCard();

      const priceChange = screen.getByText('(+2.50)');
      const percentChange = screen.getByText('+1.69% 🡩');
      
      expect(priceChange).toHaveClass('positive');
      expect(percentChange).toHaveClass('positive');
    });

    it('should apply negative class for negative change', () => {
      renderStockCard({ stock: mockNegativeStock });

      const priceChange = screen.getByText('(-5.25)');
      const percentChange = screen.getByText('-2.56% 🡫');
      
      expect(priceChange).toHaveClass('negative');
      expect(percentChange).toHaveClass('negative');
    });

    it('should display N/A for null price', () => {
      const stockWithNullPrice = { ...mockStock, price: null as any };
      renderStockCard({ stock: stockWithNullPrice });

      expect(screen.getByText('N/A')).toBeInTheDocument();
    });

    it('should display N/A for null price change', () => {
      const stockWithNullChange = { ...mockStock, priceChange: null as any };
      renderStockCard({ stock: stockWithNullChange });

      expect(screen.getByText('N/A')).toBeInTheDocument();
    });

    it('should display N/A for null percent change', () => {
      const stockWithNullPercent = { ...mockStock, percentChange: null as any };
      renderStockCard({ stock: stockWithNullPercent });

      expect(screen.getByText('N/A')).toBeInTheDocument();
    });
  });

  describe('Stock Details', () => {
    it('should display market cap in billions', () => {
      renderStockCard();

      expect(screen.getByText('2400.00B')).toBeInTheDocument();
    });

    it('should display volume in millions', () => {
      renderStockCard();

      expect(screen.getByText('52.00M')).toBeInTheDocument();
    });

    it('should display average volume in millions', () => {
      renderStockCard();

      expect(screen.getByText('50.00M')).toBeInTheDocument();
    });

    it('should display relative volume as percentage', () => {
      renderStockCard();

      expect(screen.getByText('1.04%')).toBeInTheDocument();
    });

    it('should display P/E ratio', () => {
      renderStockCard();

      expect(screen.getByText('28.50')).toBeInTheDocument();
    });

    it('should display trailing EPS', () => {
      renderStockCard();

      expect(screen.getByText('5.67')).toBeInTheDocument();
    });

    it('should display forward EPS', () => {
      renderStockCard();

      expect(screen.getByText('6.12')).toBeInTheDocument();
    });

    it('should display next earnings date formatted', () => {
      renderStockCard();

      const formattedDate = new Date('2025-11-01').toLocaleDateString();
      expect(screen.getByText(formattedDate)).toBeInTheDocument();
    });

    it('should display recommendation', () => {
      renderStockCard();

      expect(screen.getByText('Buy')).toBeInTheDocument();
    });

    it('should display N/A for null market cap', () => {
      const stockWithNullMarketCap = { ...mockStock, marketCap: null as any };
      renderStockCard({ stock: stockWithNullMarketCap });

      const labels = screen.getAllByText('N/A');
      expect(labels.length).toBeGreaterThan(0);
    });

    it('should display N/A for undefined volume', () => {
      const stockWithUndefinedVolume = { ...mockStock, volume: undefined as any };
      renderStockCard({ stock: stockWithUndefinedVolume });

      const labels = screen.getAllByText('N/A');
      expect(labels.length).toBeGreaterThan(0);
    });

    it('should display N/A for NaN relative volume', () => {
      const stockWithNaNRVol = { ...mockStock, relativeVolume: NaN };
      renderStockCard({ stock: stockWithNaNRVol });

      const labels = screen.getAllByText('N/A');
      expect(labels.length).toBeGreaterThan(0);
    });
  });

  describe('Numeric Formatting', () => {
    it('should format trillions with T suffix', () => {
      const stockWithTrillionMarketCap = { 
        ...mockStock, 
        marketCap: 2500000000000 
      };
      renderStockCard({ stock: stockWithTrillionMarketCap });

      expect(screen.getByText('2.50T')).toBeInTheDocument();
    });

    it('should format billions with B suffix', () => {
      const stockWithBillionMarketCap = { 
        ...mockStock, 
        marketCap: 5500000000 
      };
      renderStockCard({ stock: stockWithBillionMarketCap });

      expect(screen.getByText('5.50B')).toBeInTheDocument();
    });

    it('should format millions with M suffix', () => {
      renderStockCard();

      expect(screen.getByText('52.00M')).toBeInTheDocument();
    });

    it('should format thousands with K suffix', () => {
      const stockWithThousandVolume = { 
        ...mockStock, 
        volume: 5500 
      };
      renderStockCard({ stock: stockWithThousandVolume });

      expect(screen.getByText('5.50K')).toBeInTheDocument();
    });

    it('should display small numbers without suffix', () => {
      const stockWithSmallVolume = { 
        ...mockStock, 
        volume: 500 
      };
      renderStockCard({ stock: stockWithSmallVolume });

      expect(screen.getByText('500')).toBeInTheDocument();
    });
  });

  describe('Dropdown Menu', () => {
    it('should open dropdown when menu button is clicked', () => {
      renderStockCard();
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);

      expect(screen.getByText('✖ Delete')).toBeInTheDocument();
    });

    it('should close dropdown when menu button is clicked again', () => {
      renderStockCard();
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);
      expect(screen.getByText('✖ Delete')).toBeInTheDocument();

      fireEvent.click(menuButton);
      expect(screen.queryByText('✖ Delete')).not.toBeInTheDocument();
    });

    it('should show Email option when not in reserve list', () => {
      renderStockCard({ isReserveList: false });
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);

      expect(screen.getByText('✉ Email')).toBeInTheDocument();
    });

    it('should not show Email option when in reserve list', () => {
      renderStockCard({ isReserveList: true });
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);

      expect(screen.queryByText('✉ Email')).not.toBeInTheDocument();
    });

    it('should show Reserve option when in watchlist', () => {
      renderStockCard({ isReserveList: false });
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);

      expect(screen.getByText('🡫 Reserve')).toBeInTheDocument();
    });

    it('should show Watchlist option when in reserve list', () => {
      renderStockCard({ isReserveList: true });
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);

      expect(screen.getByText('🡩 Watchlist')).toBeInTheDocument();
    });

    it('should always show Delete option', () => {
      renderStockCard();
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);

      expect(screen.getByText('✖ Delete')).toBeInTheDocument();
    });

    it('should close dropdown when clicking outside', () => {
      renderStockCard();
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);
      expect(screen.getByText('✖ Delete')).toBeInTheDocument();

      fireEvent.mouseDown(document.body);

      expect(screen.queryByText('✖ Delete')).not.toBeInTheDocument();
    });

    it('should not close dropdown when clicking inside', () => {
      renderStockCard();
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);
      const dropdown = screen.getByText('✖ Delete').closest('.dropdown-menu');
      
      fireEvent.mouseDown(dropdown!);

      expect(screen.getByText('✖ Delete')).toBeInTheDocument();
    });
  });

  describe('Delete Functionality', () => {
    it('should call onRemove with stock symbol when Delete is clicked', () => {
      const { onRemove } = renderStockCard();
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);
      const deleteButton = screen.getByText('✖ Delete');
      fireEvent.click(deleteButton);

      expect(onRemove).toHaveBeenCalledWith('AAPL');
    });

    it('should close dropdown after delete', () => {
      renderStockCard();
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);
      const deleteButton = screen.getByText('✖ Delete');
      fireEvent.click(deleteButton);

      expect(screen.queryByText('✖ Delete')).not.toBeInTheDocument();
    });
  });

  describe('Move Functionality', () => {
    it('should call onMoveToReserve when Reserve is clicked from watchlist', () => {
      const { onMoveToReserve } = renderStockCard({ isReserveList: false });
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);
      const moveButton = screen.getByText('🡫 Reserve');
      fireEvent.click(moveButton);

      expect(onMoveToReserve).toHaveBeenCalledWith('AAPL');
    });

    it('should call onMoveToWatchlist when Watchlist is clicked from reserve', () => {
      const { onMoveToWatchlist } = renderStockCard({ isReserveList: true });
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);
      const moveButton = screen.getByText('🡩 Watchlist');
      fireEvent.click(moveButton);

      expect(onMoveToWatchlist).toHaveBeenCalledWith('AAPL');
    });

    it('should not call onMoveToWatchlist when in watchlist', () => {
      const { onMoveToWatchlist } = renderStockCard({ isReserveList: false });
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);
      const moveButton = screen.getByText('🡫 Reserve');
      fireEvent.click(moveButton);

      expect(onMoveToWatchlist).not.toHaveBeenCalled();
    });

    it('should not call onMoveToReserve when in reserve list', () => {
      const { onMoveToReserve } = renderStockCard({ isReserveList: true });
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);
      const moveButton = screen.getByText('🡩 Watchlist');
      fireEvent.click(moveButton);

      expect(onMoveToReserve).not.toHaveBeenCalled();
    });

    it('should close dropdown after moving', () => {
      renderStockCard({ isReserveList: false });
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);
      const moveButton = screen.getByText('🡫 Reserve');
      fireEvent.click(moveButton);

      expect(screen.queryByText('🡫 Reserve')).not.toBeInTheDocument();
    });
  });

  describe('Email Functionality', () => {
    it('should call onSendEmail when Email is clicked', () => {
      const { onSendEmail } = renderStockCard({ isReserveList: false });
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);
      const emailButton = screen.getByText('✉ Email');
      fireEvent.click(emailButton);

      expect(onSendEmail).toHaveBeenCalledWith('AAPL');
    });

    it('should close dropdown after sending email', () => {
      renderStockCard({ isReserveList: false });
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);
      const emailButton = screen.getByText('✉ Email');
      fireEvent.click(emailButton);

      expect(screen.queryByText('✉ Email')).not.toBeInTheDocument();
    });

    it('should not call onSendEmail when undefined', () => {
      const onSendEmail = undefined;
      renderStockCard({ isReserveList: false, onSendEmail });
      const menuButton = screen.getByTitle('Stock options');

      fireEvent.click(menuButton);
      const emailButton = screen.getByText('✉ Email');
      
      expect(() => fireEvent.click(emailButton)).not.toThrow();
    });
  });

  describe('StockChart Integration', () => {
    it('should pass priceHistory to StockChart', () => {
      renderStockCard();

      expect(screen.getByTestId('chart-data-length')).toHaveTextContent('3');
    });

    it('should pass percentChange to StockChart', () => {
      renderStockCard();

      expect(screen.getByTestId('chart-change-percent')).toHaveTextContent('1.69');
    });

    it('should pass 0 when percentChange is null', () => {
      const stockWithNullPercent = { ...mockStock, percentChange: null as any };
      renderStockCard({ stock: stockWithNullPercent });

      expect(screen.getByTestId('chart-change-percent')).toHaveTextContent('0');
    });

    it('should pass 0 when percentChange is undefined', () => {
      const stockWithUndefinedPercent = { ...mockStock, percentChange: undefined as any };
      renderStockCard({ stock: stockWithUndefinedPercent });

      expect(screen.getByTestId('chart-change-percent')).toHaveTextContent('0');
    });
  });

  describe('Event Listener Cleanup', () => {
    it('should remove event listener on unmount', () => {
      const removeEventListenerSpy = jest.spyOn(document, 'removeEventListener');
      
      const { unmount } = renderStockCard();
      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('mousedown', expect.any(Function));

      removeEventListenerSpy.mockRestore();
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero price change', () => {
      const stockWithZeroChange = { 
        ...mockStock, 
        priceChange: 0, 
        percentChange: 0 
      };
      renderStockCard({ stock: stockWithZeroChange });

      expect(screen.getByText('(+0.00)')).toBeInTheDocument();
      expect(screen.getByText('+0.00% 🡩')).toBeInTheDocument();
    });

    it('should handle very small positive change', () => {
      const stockWithSmallChange = { 
        ...mockStock, 
        priceChange: 0.01, 
        percentChange: 0.01 
      };
      renderStockCard({ stock: stockWithSmallChange });

      expect(screen.getByText('(+0.01)')).toBeInTheDocument();
      expect(screen.getByText('+0.01% 🡩')).toBeInTheDocument();
    });

    it('should handle very large market cap', () => {
      const stockWithLargeMarketCap = { 
        ...mockStock, 
        marketCap: 15000000000000 
      };
      renderStockCard({ stock: stockWithLargeMarketCap });

      expect(screen.getByText('15.00T')).toBeInTheDocument();
    });

    it('should handle missing optional callbacks', () => {
      renderStockCard({ 
        onMoveToReserve: undefined,
        onMoveToWatchlist: undefined,
        onSendEmail: undefined
      });

      const menuButton = screen.getByTitle('Stock options');
      fireEvent.click(menuButton);

      expect(screen.getByText('✖ Delete')).toBeInTheDocument();
    });

    it('should handle empty recommendation', () => {
      const stockWithEmptyRec = { 
        ...mockStock, 
        recommendation: '' 
      };
      renderStockCard({ stock: stockWithEmptyRec });

      expect(screen.getByText('N/A')).toBeInTheDocument();
    });

    it('should handle invalid date for earnings', () => {
      const stockWithInvalidDate = { 
        ...mockStock, 
        nextEarningsDate: '' 
      };
      renderStockCard({ stock: stockWithInvalidDate });

      expect(screen.getByText('N/A')).toBeInTheDocument();
    });
  });
});