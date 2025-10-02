import { HttpClient } from './http-client.ts';
import { Stock } from '../components/dashboard/utils/types.ts';
import { StockSearchResponse, StockValidationResponse } from './utils/types.ts';

/**
 * Service class for stock-related API operations.
 */
export class StockService {
  /**
   * Fetches detailed stock information including current price, changes, and price history chart data.
   * 
   * @param symbol - The stock ticker symbol (e.g., 'AAPL', 'GOOGL').
   * @returns Promise resolving to a Stock object containing price, change data, and historical prices.
   * @throws Error if the API request fails or the stock is not found.
   */
  static async getStockInfo(symbol: string): Promise<Stock> {
    const data = await HttpClient.request<{
      symbol: string;
      name: string;
      price: number;
      priceChange: number;
      percentChange: number;
      priceHistory: Array<{ timestamp: string; price: number }>;
      marketCap: number;
      volume: number;
      avgVolume: number;
      relativeVolume: number;
      nextEarningsDate: string;
      peRatio: number;
      trailingEPS: number;
      forwardEPS: number;
      recommendation: string;
    }>(`/api/stocks/info/${symbol}`);
    
    return {
      symbol: data.symbol,
      name: data.name,
      price: data.price,
      priceChange: data.priceChange,
      percentChange: data.percentChange,
      priceHistory: data.priceHistory,
      marketCap: data.marketCap,
      volume: data.volume,
      avgVolume: data.avgVolume,
      relativeVolume: data.relativeVolume,
      nextEarningsDate: data.nextEarningsDate,
      peRatio: data.peRatio,
      trailingEPS: data.trailingEPS,
      forwardEPS: data.forwardEPS,
      recommendation: data.recommendation,
    };
  }

  /**
   * Searches for stock tickers matching the provided query string.
   * 
   * @param query - The search query string (partial or full ticker symbol).
   * @param limit - Maximum number of results to return. Defaults to 5.
   * @returns Promise resolving to StockSearchResponse containing an array of matching stock suggestions.
   * @throws Error if the API request fails.
   */
  static async searchStocks(query: string, limit = 5): Promise<StockSearchResponse> {
    return HttpClient.request<StockSearchResponse>(
      `/api/stocks/search?q=${encodeURIComponent(query)}&limit=${limit}`
    );
  }

  /**
   * Validates whether a stock ticker symbol exists and is tradeable.
   * 
   * @param ticker - The stock ticker symbol to validate.
   * @returns Promise resolving to StockValidationResponse indicating if the ticker is valid.
   * @throws Error if the API request fails.
   */
  static async validateTicker(ticker: string): Promise<StockValidationResponse> {
    return HttpClient.request<StockValidationResponse>(
      `/api/stocks/validate/${encodeURIComponent(ticker)}`
    );
  }

  /**
   * Get user's saved watchlist tickers from database.
   * 
   * @returns Promise resolving to an array of ticker symbols.
   * @throws Error if the API request fails.
   */
  static async getUserWatchlist(): Promise<string[]> {
    const response = await HttpClient.request<{ tickers: string[] }>(
      '/api/stocks/user/watchlist'
    );
    return response.tickers;
  }

  /**
   * Add ticker to user's watchlist in database.
   * 
   * @param symbol - The stock ticker symbol to add.
   * @returns Promise that resolves when the ticker is added.
   * @throws Error if the API request fails.
   */
  static async addToWatchlist(symbol: string): Promise<void> {
    await HttpClient.request(`/api/stocks/user/watchlist/${symbol}`, {
      method: 'POST'
    });
  }

  /**
   * Remove ticker from user's watchlist in database.
   * 
   * @param symbol - The stock ticker symbol to remove.
   * @returns Promise that resolves when the ticker is removed.
   * @throws Error if the API request fails.
   */
  static async removeFromWatchlist(symbol: string): Promise<void> {
    await HttpClient.request(`/api/stocks/user/watchlist/${symbol}`, {
      method: 'DELETE'
    });
  }

  /**
   * Get user's saved reserve tickers from database.
   * 
   * @returns Promise resolving to an array of ticker symbols.
   * @throws Error if the API request fails.
   */
  static async getUserReserve(): Promise<string[]> {
    const response = await HttpClient.request<{ tickers: string[] }>(
      '/api/stocks/user/reserve'
    );
    return response.tickers;
  }

  /**
   * Add ticker to user's reserve list in database.
   * 
   * @param symbol - The stock ticker symbol to add.
   * @returns Promise that resolves when the ticker is added.
   * @throws Error if the API request fails.
   */
  static async addToReserve(symbol: string): Promise<void> {
    await HttpClient.request(`/api/stocks/user/reserve/${symbol}`, {
      method: 'POST'
    });
  }

  /**
   * Remove ticker from user's reserve list in database.
   * 
   * @param symbol - The stock ticker symbol to remove.
   * @returns Promise that resolves when the ticker is removed.
   * @throws Error if the API request fails.
   */
  static async removeFromReserve(symbol: string): Promise<void> {
    await HttpClient.request(`/api/stocks/user/reserve/${symbol}`, {
      method: 'DELETE'
    });
  }

  /**
   * Move a ticker from watchlist to reserve in the database.
   * 
   * @param symbol - The stock ticker symbol to move.
   * @returns Promise that resolves when the ticker is moved.
   * @throws Error if the API request fails.
   */
  static async moveToReserve(symbol: string): Promise<void> {
    await HttpClient.request(`/api/stocks/user/watchlist/${symbol}/move-to-reserve`, {
      method: 'POST'
    });
  }

  /**
   * Move a ticker from reserve to watchlist in the database.
   * 
   * @param symbol - The stock ticker symbol to move.
   * @returns Promise that resolves when the ticker is moved.
   * @throws Error if the API request fails.
   */
  static async moveToWatchlist(symbol: string): Promise<void> {
    await HttpClient.request(`/api/stocks/user/reserve/${symbol}/move-to-watchlist`, {
      method: 'POST'
    });
  }
}