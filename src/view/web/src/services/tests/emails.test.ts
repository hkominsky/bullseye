import { EmailService } from '../emails.ts';
import { HttpClient } from '../http-client.ts';
import { EmailJobResponse } from '../utils/types.ts';

// Mocks
jest.mock('../http-client.ts');

const mockEmailJobResponse: EmailJobResponse = {
  message: 'Emails queued successfully',
  ticker_count: 3,
  tickers: ['AAPL', 'GOOGL', 'MSFT'],
  status: 'processing'
};

describe('EmailService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('sendWatchlistEmails', () => {
    it('should send watchlist emails successfully', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockEmailJobResponse);

      const result = await EmailService.sendWatchlistEmails();

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/email/send-watchlist',
        {
          method: 'POST'
        }
      );
      expect(result).toEqual(mockEmailJobResponse);
    });

    it('should return correct message from response', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockEmailJobResponse);

      const result = await EmailService.sendWatchlistEmails();

      expect(result.message).toBe('Emails queued successfully');
    });

    it('should return correct ticker count', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockEmailJobResponse);

      const result = await EmailService.sendWatchlistEmails();

      expect(result.ticker_count).toBe(3);
    });

    it('should return correct tickers array', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockEmailJobResponse);

      const result = await EmailService.sendWatchlistEmails();

      expect(result.tickers).toEqual(['AAPL', 'GOOGL', 'MSFT']);
    });

    it('should return correct status', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockEmailJobResponse);

      const result = await EmailService.sendWatchlistEmails();

      expect(result.status).toBe('processing');
    });

    it('should handle completed status', async () => {
      const completedResponse: EmailJobResponse = {
        ...mockEmailJobResponse,
        status: 'completed'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(completedResponse);

      const result = await EmailService.sendWatchlistEmails();

      expect(result.status).toBe('completed');
    });

    it('should handle failed status', async () => {
      const failedResponse: EmailJobResponse = {
        ...mockEmailJobResponse,
        status: 'failed'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(failedResponse);

      const result = await EmailService.sendWatchlistEmails();

      expect(result.status).toBe('failed');
    });

    it('should throw error when request fails', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      await expect(EmailService.sendWatchlistEmails()).rejects.toThrow('Network error');
    });

    it('should throw error with API error message', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('No stocks in watchlist')
      );

      await expect(EmailService.sendWatchlistEmails()).rejects.toThrow(
        'No stocks in watchlist'
      );
    });

    it('should handle empty watchlist', async () => {
      const emptyResponse: EmailJobResponse = {
        message: 'No stocks to process',
        ticker_count: 0,
        tickers: [],
        status: 'completed'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(emptyResponse);

      const result = await EmailService.sendWatchlistEmails();

      expect(result.ticker_count).toBe(0);
      expect(result.tickers).toEqual([]);
    });

    it('should handle large watchlist', async () => {
      const largeTickers = Array.from({ length: 50 }, (_, i) => `STOCK${i}`);
      const largeResponse: EmailJobResponse = {
        message: 'Emails queued successfully',
        ticker_count: 50,
        tickers: largeTickers,
        status: 'processing'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(largeResponse);

      const result = await EmailService.sendWatchlistEmails();

      expect(result.ticker_count).toBe(50);
      expect(result.tickers.length).toBe(50);
    });

    it('should use POST method', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockEmailJobResponse);

      await EmailService.sendWatchlistEmails();

      expect(HttpClient.request).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });

    it('should call correct API endpoint', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockEmailJobResponse);

      await EmailService.sendWatchlistEmails();

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/email/send-watchlist',
        expect.any(Object)
      );
    });
  });

  describe('sendCustomEmails', () => {
    const customTickers = ['AAPL', 'GOOGL', 'MSFT'];

    it('should send custom emails successfully', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockEmailJobResponse);

      const result = await EmailService.sendCustomEmails(customTickers);

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/email/send-custom',
        {
          method: 'POST',
          body: JSON.stringify({ tickers: customTickers })
        }
      );
      expect(result).toEqual(mockEmailJobResponse);
    });

    it('should send tickers in request body', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockEmailJobResponse);

      await EmailService.sendCustomEmails(customTickers);

      expect(HttpClient.request).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify({ tickers: customTickers })
        })
      );
    });

    it('should return correct response for custom emails', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockEmailJobResponse);

      const result = await EmailService.sendCustomEmails(customTickers);

      expect(result.message).toBe('Emails queued successfully');
      expect(result.ticker_count).toBe(3);
      expect(result.tickers).toEqual(['AAPL', 'GOOGL', 'MSFT']);
      expect(result.status).toBe('processing');
    });

    it('should handle single ticker', async () => {
      const singleTickerResponse: EmailJobResponse = {
        message: 'Email queued successfully',
        ticker_count: 1,
        tickers: ['AAPL'],
        status: 'processing'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(singleTickerResponse);

      const result = await EmailService.sendCustomEmails(['AAPL']);

      expect(result.ticker_count).toBe(1);
      expect(result.tickers).toEqual(['AAPL']);
    });

    it('should handle empty tickers array', async () => {
      const emptyResponse: EmailJobResponse = {
        message: 'No tickers provided',
        ticker_count: 0,
        tickers: [],
        status: 'completed'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(emptyResponse);

      const result = await EmailService.sendCustomEmails([]);

      expect(result.ticker_count).toBe(0);
      expect(result.tickers).toEqual([]);
    });

    it('should handle many tickers', async () => {
      const manyTickers = Array.from({ length: 100 }, (_, i) => `STOCK${i}`);
      const manyTickersResponse: EmailJobResponse = {
        message: 'Emails queued successfully',
        ticker_count: 100,
        tickers: manyTickers,
        status: 'processing'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(manyTickersResponse);

      const result = await EmailService.sendCustomEmails(manyTickers);

      expect(result.ticker_count).toBe(100);
      expect(result.tickers.length).toBe(100);
    });

    it('should throw error when request fails', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Invalid tickers')
      );

      await expect(EmailService.sendCustomEmails(customTickers)).rejects.toThrow(
        'Invalid tickers'
      );
    });

    it('should throw error for network failure', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      await expect(EmailService.sendCustomEmails(customTickers)).rejects.toThrow(
        'Network error'
      );
    });

    it('should use POST method', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockEmailJobResponse);

      await EmailService.sendCustomEmails(customTickers);

      expect(HttpClient.request).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });

    it('should call correct API endpoint', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockEmailJobResponse);

      await EmailService.sendCustomEmails(customTickers);

      expect(HttpClient.request).toHaveBeenCalledWith(
        '/api/email/send-custom',
        expect.any(Object)
      );
    });

    it('should serialize tickers correctly in body', async () => {
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(mockEmailJobResponse);

      await EmailService.sendCustomEmails(['AAPL', 'TSLA']);

      const expectedBody = JSON.stringify({ tickers: ['AAPL', 'TSLA'] });
      expect(HttpClient.request).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: expectedBody
        })
      );
    });

    it('should handle completed status for custom emails', async () => {
      const completedResponse: EmailJobResponse = {
        message: 'Emails sent successfully',
        ticker_count: 3,
        tickers: customTickers,
        status: 'completed'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(completedResponse);

      const result = await EmailService.sendCustomEmails(customTickers);

      expect(result.status).toBe('completed');
    });

    it('should handle failed status for custom emails', async () => {
      const failedResponse: EmailJobResponse = {
        message: 'Some emails failed',
        ticker_count: 3,
        tickers: customTickers,
        status: 'failed'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(failedResponse);

      const result = await EmailService.sendCustomEmails(customTickers);

      expect(result.status).toBe('failed');
    });

    it('should handle special characters in tickers', async () => {
      const specialTickers = ['BRK.B', 'BF.B'];
      const specialResponse: EmailJobResponse = {
        message: 'Emails queued successfully',
        ticker_count: 2,
        tickers: specialTickers,
        status: 'processing'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(specialResponse);

      const result = await EmailService.sendCustomEmails(specialTickers);

      expect(result.tickers).toEqual(specialTickers);
    });
  });

  describe('Static Class Behavior', () => {
    it('should be a static class', () => {
      expect(EmailService.sendWatchlistEmails).toBeDefined();
      expect(EmailService.sendCustomEmails).toBeDefined();
    });

    it('should not require instantiation', () => {
      expect(() => EmailService.sendWatchlistEmails()).not.toThrow(TypeError);
    });
  });

  describe('Error Handling', () => {
    it('should propagate HttpClient errors', async () => {
      const customError = new Error('API rate limit exceeded');
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(customError);

      await expect(EmailService.sendWatchlistEmails()).rejects.toThrow(
        'API rate limit exceeded'
      );
    });

    it('should propagate authentication errors', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Unauthorized')
      );

      await expect(EmailService.sendCustomEmails(['AAPL'])).rejects.toThrow(
        'Unauthorized'
      );
    });

    it('should propagate server errors', async () => {
      (HttpClient.request as jest.Mock).mockRejectedValueOnce(
        new Error('Internal server error')
      );

      await expect(EmailService.sendWatchlistEmails()).rejects.toThrow(
        'Internal server error'
      );
    });
  });

  describe('Response Status Types', () => {
    it('should handle processing status correctly', async () => {
      const processingResponse: EmailJobResponse = {
        message: 'Processing emails',
        ticker_count: 5,
        tickers: ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'],
        status: 'processing'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(processingResponse);

      const result = await EmailService.sendWatchlistEmails();

      expect(result.status).toBe('processing');
    });

    it('should handle completed status correctly', async () => {
      const completedResponse: EmailJobResponse = {
        message: 'All emails sent',
        ticker_count: 3,
        tickers: ['AAPL', 'GOOGL', 'MSFT'],
        status: 'completed'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(completedResponse);

      const result = await EmailService.sendWatchlistEmails();

      expect(result.status).toBe('completed');
    });

    it('should handle failed status correctly', async () => {
      const failedResponse: EmailJobResponse = {
        message: 'Email sending failed',
        ticker_count: 3,
        tickers: ['AAPL', 'GOOGL', 'MSFT'],
        status: 'failed'
      };
      (HttpClient.request as jest.Mock).mockResolvedValueOnce(failedResponse);

      const result = await EmailService.sendWatchlistEmails();

      expect(result.status).toBe('failed');
    });
  });
});