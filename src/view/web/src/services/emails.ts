import { HttpClient } from './http-client.ts';
import { EmailJobResponse } from './utils/types.ts';

/**
 * Service for handling email-related API operations.
 */
export class EmailService {
  /**
   * Triggers automated emails for all stocks in the user's watchlist.
   * 
   * @returns Promise resolving to the email job response.
   * @throws Error if the request fails.
   */
  static async sendWatchlistEmails(): Promise<EmailJobResponse> {
    return HttpClient.request<EmailJobResponse>(
      '/api/email/send-watchlist',
      {
        method: 'POST'
      }
    );
  }

  /**
   * Triggers automated emails for a custom list of tickers.
   * 
   * @param tickers - Array of stock ticker symbols to process.
   * @returns Promise resolving to the email job response.
   * @throws Error if the request fails.
   */
  static async sendCustomEmails(tickers: string[]): Promise<EmailJobResponse> {
    return HttpClient.request<EmailJobResponse>(
      '/api/email/send-custom',
      {
        method: 'POST',
        body: JSON.stringify({ tickers })
      }
    );
  }
}