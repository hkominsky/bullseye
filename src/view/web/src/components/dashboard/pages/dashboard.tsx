import React, { useState, useEffect } from 'react';
import '../styles/dashboard.css'
import { Stock } from '../utils/types.ts';
import { Header } from '../widgets/header.tsx';
import { Watchlist } from '../widgets/watch-list.tsx';
import { ReserveList } from '../widgets/reserve-list.tsx';
import { StockService } from '../../../services/stocks.ts';
import { EmailService } from '../../../services/emails.ts';
import { CachedData } from '../utils/types.ts';
import { ToastProvider, useToast } from '../widgets/toast-context.tsx';

const WATCHLIST_CACHE_KEY = 'dashboard_watchlist_cache';
const RESERVE_CACHE_KEY = 'dashboard_reserve_cache';
const CACHE_EXPIRY_MS = 5 * 60 * 1000;

/**
 * Dashboard content component with toast functionality.
 */
const DashboardContent: React.FC = () => {
  const { showToast } = useToast();
  const [showAddForm, setShowAddForm] = useState(false);
  const [showReserveAddForm, setShowReserveAddForm] = useState(false);
  const [ownedStocks, setOwnedStocks] = useState<Stock[]>([]);
  const [reserveStocks, setReserveStocks] = useState<Stock[]>([]);
  const [isEmailProcessing, setIsEmailProcessing] = useState(false);

  /**
   * Retrieves cached data from localStorage if it's still valid.
   */
  const getCachedData = (key: string): Stock[] | null => {
    try {
      const cached = localStorage.getItem(key);
      if (!cached) return null;

      const { stocks, timestamp }: CachedData = JSON.parse(cached);
      const now = Date.now();

      if (now - timestamp < CACHE_EXPIRY_MS) {
        return stocks;
      }

      localStorage.removeItem(key);
      return null;
    } catch (err) {
      console.error('Failed to read cache:', err);
      return null;
    }
  };

  /**
   * Saves data to localStorage with timestamp.
   */
  const setCachedData = (key: string, stocks: Stock[]): void => {
    try {
      const cacheData: CachedData = {
        stocks,
        timestamp: Date.now()
      };
      localStorage.setItem(key, JSON.stringify(cacheData));
    } catch (err) {
      console.error('Failed to save cache:', err);
    }
  };

  /**
   * Load initial stocks on component mount from cache or database.
   */
  useEffect(() => {
    const loadInitialStocks = async () => {
      try {
        const cachedWatchlist = getCachedData(WATCHLIST_CACHE_KEY);
        const cachedReserve = getCachedData(RESERVE_CACHE_KEY);

        if (cachedWatchlist) {
          setOwnedStocks(cachedWatchlist);
        }

        if (cachedReserve) {
          setReserveStocks(cachedReserve);
        }

        if (cachedWatchlist && cachedReserve) {
          return;
        }

        const watchlistTickers = await StockService.getUserWatchlist();
        const reserveTickers = await StockService.getUserReserve();
        
        if (!cachedWatchlist && watchlistTickers.length > 0) {
          const watchlistPromises = watchlistTickers.map(symbol => 
            StockService.getStockInfo(symbol)
          );
          const watchlistStocks = await Promise.all(watchlistPromises);
          setOwnedStocks(watchlistStocks);
          setCachedData(WATCHLIST_CACHE_KEY, watchlistStocks);
        }
        
        if (!cachedReserve && reserveTickers.length > 0) {
          const reservePromises = reserveTickers.map(symbol => 
            StockService.getStockInfo(symbol)
          );
          const reserveStocksData = await Promise.all(reservePromises);
          setReserveStocks(reserveStocksData);
          setCachedData(RESERVE_CACHE_KEY, reserveStocksData);
        }
      } catch (err) {
        console.error('Failed to load initial stocks:', err);
      }
    };

    loadInitialStocks();
  }, []);

  /**
   * Update cache whenever ownedStocks changes.
   */
  useEffect(() => {
    if (ownedStocks.length > 0) {
      setCachedData(WATCHLIST_CACHE_KEY, ownedStocks);
    }
  }, [ownedStocks]);

  /**
   * Update cache whenever reserveStocks changes.
   */
  useEffect(() => {
    if (reserveStocks.length > 0) {
      setCachedData(RESERVE_CACHE_KEY, reserveStocks);
    }
  }, [reserveStocks]);

  /**
   * Handles adding a new stock to the watchlist and database.
   * 
   * @param ticker - The stock ticker symbol to add.
   */
  const handleAddStock = async (ticker: string): Promise<void> => {
    if (ownedStocks.some(s => s.symbol === ticker)) {
      return;
    }

    try {
      const newStock = await StockService.getStockInfo(ticker);
      await StockService.addToWatchlist(ticker);
      setOwnedStocks(prevStocks => [...prevStocks, newStock]);
      setShowAddForm(false);
    } catch (err) {
      console.error(`Failed to add ${ticker}:`, err);
    }
  };

  /**
   * Handles adding a new stock to the reserve list and database.
   * 
   * @param ticker - The stock ticker symbol to add.
   */
  const handleAddReserveStock = async (ticker: string): Promise<void> => {
    if (reserveStocks.some(s => s.symbol === ticker)) {
      return;
    }

    try {
      const newStock = await StockService.getStockInfo(ticker);
      await StockService.addToReserve(ticker);
      setReserveStocks(prevStocks => [...prevStocks, newStock]);
      setShowReserveAddForm(false);
    } catch (err) {
      console.error(`Failed to add ${ticker}:`, err);
    }
  };

  /**
   * Removes a stock from the watchlist and database.
   * 
   * @param symbol - The stock symbol to remove from the watchlist.
   */
  const removeStock = async (symbol: string): Promise<void> => {
    try {
      await StockService.removeFromWatchlist(symbol);
      setOwnedStocks(prevStocks => prevStocks.filter(stock => stock.symbol !== symbol));
    } catch (err) {
      console.error(`Failed to remove ${symbol}:`, err);
    }
  };

  /**
   * Removes a stock from the reserve list and database.
   * 
   * @param symbol - The stock symbol to remove from the reserve list.
   */
  const removeReserveStock = async (symbol: string): Promise<void> => {
    try {
      await StockService.removeFromReserve(symbol);
      setReserveStocks(prevStocks => prevStocks.filter(stock => stock.symbol !== symbol));
    } catch (err) {
      console.error(`Failed to remove ${symbol}:`, err);
    }
  };

  /**
   * Moves a stock from the watchlist to the reserve list in both UI and database.
   * 
   * @param symbol - The stock symbol to move.
   */
  const moveToReserve = async (symbol: string): Promise<void> => {
    const stock = ownedStocks.find(s => s.symbol === symbol);
    if (stock) {
      try {
        await StockService.moveToReserve(symbol);
        setOwnedStocks(prevStocks => prevStocks.filter(s => s.symbol !== symbol));
        setReserveStocks(prevStocks => [...prevStocks, stock]);
      } catch (err) {
        console.error(`Failed to move ${symbol} to reserve:`, err);
      }
    }
  };

  /**
   * Moves a stock from the reserve list to the watchlist in both UI and database.
   * 
   * @param symbol - The stock symbol to move.
   */
  const moveToWatchlist = async (symbol: string): Promise<void> => {
    const stock = reserveStocks.find(s => s.symbol === symbol);
    if (stock) {
      try {
        await StockService.moveToWatchlist(symbol);
        setReserveStocks(prevStocks => prevStocks.filter(s => s.symbol !== symbol));
        setOwnedStocks(prevStocks => [...prevStocks, stock]);
      } catch (err) {
        console.error(`Failed to move ${symbol} to watchlist:`, err);
      }
    }
  };

  /**
   * Handles sending automated emails for all stocks in watchlist.
   */
  const handleEmailAll = async (): Promise<void> => {
    if (ownedStocks.length === 0) {
      showToast('Watchlist is empty. Add stocks before sending emails.', 'error');
      return;
    }

    setIsEmailProcessing(true);
    
    try {
      const response = await EmailService.sendWatchlistEmails();
      showToast(`Sending emails for ${response.ticker_count} stocks!`, 'success');
    } catch (err) {
      console.error('Failed to send emails:', err);
      showToast('Failed to start email processing. Please try again.', 'error');
    } finally {
      setIsEmailProcessing(false);
    }
  };

  /**
   * Handles sending email for a single stock.
   */
  const handleSingleEmail = async (symbol: string): Promise<void> => {
    setIsEmailProcessing(true);

    try {
      await EmailService.sendCustomEmails([symbol]);
      showToast(`Sending email for ${symbol}!`, 'success');
    } catch (err) {
      console.error(`Failed to send email for ${symbol}:`, err);
      showToast(`Failed to send email for ${symbol}. Please try again.`, 'error');
    } finally {
      setIsEmailProcessing(false);
    }
  };

  /**
   * Toggles the add stock form by flipping showAddForm state.
   */
  const openAddForm = (): void => {
    setShowAddForm(prev => !prev);
  };

  /**
   * Cancels and closes the add stock form by setting showAddForm to false.
   */
  const cancelAddForm = (): void => {
    setShowAddForm(false);
  };

  /**
   * Toggles the reserve add stock form by flipping showReserveAddForm state.
   */
  const openReserveAddForm = (): void => {
    setShowReserveAddForm(prev => !prev);
  };

  /**
   * Cancels and closes the reserve add stock form by setting showReserveAddForm to false.
   */
  const cancelReserveAddForm = (): void => {
    setShowReserveAddForm(false);
  };

  const existingStockSymbols = [
    ...ownedStocks.map(stock => stock.symbol),
    ...reserveStocks.map(stock => stock.symbol)
  ];

  return (
    <div className="dashboard-container">
      <Header />
      
      <Watchlist 
        stocks={ownedStocks}
        onRemoveStock={removeStock}
        onAddStock={handleAddStock}
        showAddForm={showAddForm}
        existingStocks={existingStockSymbols}
        onCancelAddForm={cancelAddForm}
        onToggleAddForm={openAddForm}
        onMoveToReserve={moveToReserve}
        onEmailAll={handleEmailAll}
        onSendEmail={handleSingleEmail}
        isEmailProcessing={isEmailProcessing}
      />

      <ReserveList
        stocks={reserveStocks}
        onRemoveStock={removeReserveStock}
        onAddStock={handleAddReserveStock}
        showAddForm={showReserveAddForm}
        existingStocks={existingStockSymbols}
        onCancelAddForm={cancelReserveAddForm}
        onToggleAddForm={openReserveAddForm}
        onMoveToWatchlist={moveToWatchlist}
      />
    </div>
  );
};

/**
 * Dashboard component wrapped with ToastProvider.
 */
const Dashboard: React.FC = () => {
  return (
    <ToastProvider>
      <DashboardContent />
    </ToastProvider>
  );
};

export default Dashboard;