import { StockService } from '../stocks.ts';
import { HttpClient } from '../http-client.ts';
import { Stock } from '../../components/dashboard/utils/types.ts';
import { StockSearchResponse, StockValidationResponse } from '../utils/types.ts';

// Mocks
jest.mock('../http-client.ts');

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

const mockSearchResponse: StockSearchResponse = {
  suggestions: [
    { symbol: 'AAPL', name: 'Apple Inc.' },
    { symbol: 'AMD', name: 'Advanced Micro Devices' },
    { symbol: 'AMZN', name: 'Amazon.com Inc.' }
  ]
};

const mockValidationResponse: StockValidationResponse = {
  valid: true,
  symbol: 'AAPL',
  name: 'Apple Inc.'
};

describe('StockService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getStockInfo', () => {
    it('should fetch stock info successfully', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockStock);

      const result = await StockService.getStockInfo('AAPL');

      expect(HttpClient.request).toHaveBeenCalledWith('/api/stocks/info/AAPL');
      expect(result).toEqual(mockStock);
    });

    it('should return all stock properties', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockStock);

      const result = await StockService.getStockInfo('AAPL');

      expect(result.symbol).toBe('AAPL');
      expect(result.name).toBe('Apple Inc.');
      expect(result.price).toBe(150.25);
      expect(result.priceChange).toBe(2.5);
      expect(result.percentChange).toBe(1.69);
      expect(result.marketCap).toBe(2400000000000);
      expect(result.volume).toBe(52000000);
      expect(result.avgVolume).toBe(50000000);
      expect(result.relativeVolume).toBe(1.04);
      expect(result.nextEarningsDate).toBe('2025-11-01');
      expect(result.peRatio).toBe(28.5);
      expect(result.trailingEPS).toBe(5.67);
      expect(result.forwardEPS).toBe(6.12);
      expect(result.recommendation).toBe('Buy');
    });

    it('should return price history array', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockStock);

      const result = await StockService.getStockInfo('AAPL');

      expect(result.priceHistory).toHaveLength(3);
      expect(result.priceHistory[0].timestamp).toBe('2025-10-01T00:00:00Z');
      expect(result.priceHistory[0].price).toBe(148.00);
    });

    it('should handle different ticker symbols', async () => {
      const tslaStock = { ...mockStock, symbol: 'TSLA', name: 'Tesla Inc.' };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(tslaStock);

      const result = await StockService.getStockInfo('TSLA');

      expect(HttpClient.request).toHaveBeenCalledWith('/api/stocks/info/TSLA');
      expect(result.symbol).toBe('TSLA');
    });

    it('should handle special characters in ticker', async () => {
      const brkStock = { ...mockStock, symbol: 'BRK.B', name: 'Berkshire Hathaway' };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(brkStock);

      await StockService.getStockInfo('BRK.B');

      expect(HttpClient.request).toHaveBeenCalledWith('/api/stocks/info/BRK.B');
    });

    it('should throw error when stock not found', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Stock not found')
      );

      await expect(StockService.getStockInfo('INVALID')).rejects.toThrow(
        'Stock not found'
      );
    });

    it('should throw error on API failure', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('API error')
      );

      await expect(StockService.getStockInfo('AAPL')).rejects.toThrow('API error');
    });
  });

  describe('searchStocks', () => {
    it('should search stocks successfully', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockSearchResponse);

      const result = await StockService.searchStocks('AA');

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/search?q=AA&limit=5'
      );
      expect(result).toEqual(mockSearchResponse);
    });

    it('should return array of suggestions', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockSearchResponse);

      const result = await StockService.searchStocks('AA');

      expect(result.suggestions).toHaveLength(3);
      expect(result.suggestions[0].symbol).toBe('AAPL');
      expect(result.suggestions[0].name).toBe('Apple Inc.');
    });

    it('should use custom limit', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockSearchResponse);

      await StockService.searchStocks('AA', 10);

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/search?q=AA&limit=10'
      );
    });

    it('should use default limit of 5', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockSearchResponse);

      await StockService.searchStocks('AA');

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/search?q=AA&limit=5'
      );
    });

    it('should encode special characters in query', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockSearchResponse);

      await StockService.searchStocks('BRK.B');

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/search?q=BRK.B&limit=5'
      );
    });

    it('should handle empty search results', async () => {
      const emptyResponse: StockSearchResponse = { suggestions: [] };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(emptyResponse);

      const result = await StockService.searchStocks('INVALID');

      expect(result.suggestions).toEqual([]);
    });

    it('should throw error on search failure', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Search failed')
      );

      await expect(StockService.searchStocks('AA')).rejects.toThrow('Search failed');
    });

    it('should handle spaces in query', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockSearchResponse);

      await StockService.searchStocks('Apple Inc');

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/search?q=Apple%20Inc&limit=5'
      );
    });
  });

  describe('validateTicker', () => {
    it('should validate ticker successfully', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockValidationResponse);

      const result = await StockService.validateTicker('AAPL');

      expect(HttpClient.request).toHaveBeenCalledWith('/api/stocks/validate/AAPL');
      expect(result).toEqual(mockValidationResponse);
    });

    it('should return valid true for valid ticker', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockValidationResponse);

      const result = await StockService.validateTicker('AAPL');

      expect(result.valid).toBe(true);
      expect(result.symbol).toBe('AAPL');
      expect(result.name).toBe('Apple Inc.');
    });

    it('should return valid false for invalid ticker', async () => {
      const invalidResponse: StockValidationResponse = {
        valid: false,
        symbol: 'INVALID',
        error: 'Ticker not found'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(invalidResponse);

      const result = await StockService.validateTicker('INVALID');

      expect(result.valid).toBe(false);
      expect(result.error).toBe('Ticker not found');
    });

    it('should encode special characters in ticker', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockValidationResponse);

      await StockService.validateTicker('BRK.B');

      expect(HttpClient.request).toHaveBeenCalledWith('/api/stocks/validate/BRK.B');
    });

    it('should throw error on validation failure', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Validation failed')
      );

      await expect(StockService.validateTicker('AAPL')).rejects.toThrow(
        'Validation failed'
      );
    });
  });

  describe('getUserWatchlist', () => {
    it('should get user watchlist successfully', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce({
        tickers: ['AAPL', 'GOOGL', 'MSFT']
      });

      const result = await StockService.getUserWatchlist();

      expect(HttpClient.request).toHaveBeenCalledWith('/api/stocks/user/watchlist');
      expect(result).toEqual(['AAPL', 'GOOGL', 'MSFT']);
    });

    it('should return empty array for empty watchlist', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce({ tickers: [] });

      const result = await StockService.getUserWatchlist();

      expect(result).toEqual([]);
    });

    it('should throw error on failure', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Failed to fetch watchlist')
      );

      await expect(StockService.getUserWatchlist()).rejects.toThrow(
        'Failed to fetch watchlist'
      );
    });
  });

  describe('addToWatchlist', () => {
    it('should add ticker to watchlist successfully', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(undefined);

      await StockService.addToWatchlist('AAPL');

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/user/watchlist/AAPL',
        { method: 'POST' }
      );
    });

    it('should use POST method', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(undefined);

      await StockService.addToWatchlist('AAPL');

      expect(HttpClient.request).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ method: 'POST' })
      );
    });

    it('should throw error on failure', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Failed to add to watchlist')
      );

      await expect(StockService.addToWatchlist('AAPL')).rejects.toThrow(
        'Failed to add to watchlist'
      );
    });
  });

  describe('removeFromWatchlist', () => {
    it('should remove ticker from watchlist successfully', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(undefined);

      await StockService.removeFromWatchlist('AAPL');

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/user/watchlist/AAPL',
        { method: 'DELETE' }
      );
    });

    it('should use DELETE method', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(undefined);

      await StockService.removeFromWatchlist('AAPL');

      expect(HttpClient.request).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ method: 'DELETE' })
      );
    });

    it('should throw error on failure', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Failed to remove from watchlist')
      );

      await expect(StockService.removeFromWatchlist('AAPL')).rejects.toThrow(
        'Failed to remove from watchlist'
      );
    });
  });

  describe('getUserReserve', () => {
    it('should get user reserve list successfully', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce({
        tickers: ['TSLA', 'NVDA']
      });

      const result = await StockService.getUserReserve();

      expect(HttpClient.request).toHaveBeenCalledWith('/api/stocks/user/reserve');
      expect(result).toEqual(['TSLA', 'NVDA']);
    });

    it('should return empty array for empty reserve list', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce({ tickers: [] });

      const result = await StockService.getUserReserve();

      expect(result).toEqual([]);
    });

    it('should throw error on failure', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Failed to fetch reserve list')
      );

      await expect(StockService.getUserReserve()).rejects.toThrow(
        'Failed to fetch reserve list'
      );
    });
  });

  describe('addToReserve', () => {
    it('should add ticker to reserve list successfully', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(undefined);

      await StockService.addToReserve('TSLA');

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/user/reserve/TSLA',
        { method: 'POST' }
      );
    });

    it('should use POST method', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(undefined);

      await StockService.addToReserve('TSLA');

      expect(HttpClient.request).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ method: 'POST' })
      );
    });

    it('should throw error on failure', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Failed to add to reserve')
      );

      await expect(StockService.addToReserve('TSLA')).rejects.toThrow(
        'Failed to add to reserve'
      );
    });
  });

  describe('removeFromReserve', () => {
    it('should remove ticker from reserve list successfully', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(undefined);

      await StockService.removeFromReserve('TSLA');

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/user/reserve/TSLA',
        { method: 'DELETE' }
      );
    });

    it('should use DELETE method', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(undefined);

      await StockService.removeFromReserve('TSLA');

      expect(HttpClient.request).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ method: 'DELETE' })
      );
    });

    it('should throw error on failure', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Failed to remove from reserve')
      );

      await expect(StockService.removeFromReserve('TSLA')).rejects.toThrow(
        'Failed to remove from reserve'
      );
    });
  });

  describe('moveToReserve', () => {
    it('should move ticker to reserve successfully', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(undefined);

      await StockService.moveToReserve('AAPL');

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/user/watchlist/AAPL/move-to-reserve',
        { method: 'POST' }
      );
    });

    it('should use POST method', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(undefined);

      await StockService.moveToReserve('AAPL');

      expect(HttpClient.request).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ method: 'POST' })
      );
    });

    it('should throw error on failure', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Failed to move to reserve')
      );

      await expect(StockService.moveToReserve('AAPL')).rejects.toThrow(
        'Failed to move to reserve'
      );
    });
  });

  describe('moveToWatchlist', () => {
    it('should move ticker to watchlist successfully', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(undefined);

      await StockService.moveToWatchlist('TSLA');

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/user/reserve/TSLA/move-to-watchlist',
        { method: 'POST' }
      );
    });

    it('should use POST method', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(undefined);

      await StockService.moveToWatchlist('TSLA');

      expect(HttpClient.request).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ method: 'POST' })
      );
    });

    it('should throw error on failure', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Failed to move to watchlist')
      );

      await expect(StockService.moveToWatchlist('TSLA')).rejects.toThrow(
        'Failed to move to watchlist'
      );
    });
  });

  describe('Static Class Behavior', () => {
    it('should be a static class with all methods defined', () => {
      expect(StockService.getStockInfo).toBeDefined();
      expect(StockService.searchStocks).toBeDefined();
      expect(StockService.validateTicker).toBeDefined();
      expect(StockService.getUserWatchlist).toBeDefined();
      expect(StockService.addToWatchlist).toBeDefined();
      expect(StockService.removeFromWatchlist).toBeDefined();
      expect(StockService.getUserReserve).toBeDefined();
      expect(StockService.addToReserve).toBeDefined();
      expect(StockService.removeFromReserve).toBeDefined();
      expect(StockService.moveToReserve).toBeDefined();
      expect(StockService.moveToWatchlist).toBeDefined();
    });

    it('should not require instantiation', () => {
      expect(() => StockService.getStockInfo('AAPL')).not.toThrow(TypeError);
    });
  });

  describe('Edge Cases', () => {
    it('should handle ticker with lowercase letters', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockStock);

      await StockService.getStockInfo('aapl');

      expect(HttpClient.request).toHaveBeenCalledWith('/api/stocks/info/aapl');
    });

    it('should handle very long ticker symbols', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockStock);

      await StockService.getStockInfo('VERYLONGTICKER');

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/info/VERYLONGTICKER'
      );
    });

    it('should handle tickers with numbers', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockStock);

      await StockService.getStockInfo('BF.B');

      expect(HttpClient.request).toHaveBeenCalledWith('/api/stocks/info/BF.B');
    });

    it('should handle empty search query', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce({ suggestions: [] });

      await StockService.searchStocks('');

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/search?q=&limit=5'
      );
    });

    it('should handle limit of 0', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce({ suggestions: [] });

      await StockService.searchStocks('AA', 0);

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/search?q=AA&limit=0'
      );
    });

    it('should handle large limit value', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockSearchResponse);

      await StockService.searchStocks('AA', 100);

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/stocks/search?q=AA&limit=100'
      );
    });
  });
});