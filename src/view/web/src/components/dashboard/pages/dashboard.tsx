import React, { useState, useEffect } from 'react';
import '../styles/dashboard.css'
import { Stock } from '../utils/types.ts';
import { Header } from '../widgets/header.tsx';
import { Watchlist } from '../widgets/watch-list.tsx';
import { ReserveList } from '../widgets/reserve-list.tsx';
import { StockService } from '../../../services/stocks.ts';
import { EmailService } from '../../../services/emails.ts';
import { ToastProvider, useToast } from '../widgets/toast-context.tsx';

const DashboardContent: React.FC = () => {
  const { showToast } = useToast();
  const [showAddForm, setShowAddForm] = useState(false);
  const [showReserveAddForm, setShowReserveAddForm] = useState(false);
  const [ownedStocks, setOwnedStocks] = useState<Stock[]>([]);
  const [reserveStocks, setReserveStocks] = useState<Stock[]>([]);
  const [isEmailProcessing, setIsEmailProcessing] = useState(false);

  useEffect(() => {
    const loadInitialStocks = async () => {
      try {
        const watchlistTickers = await StockService.getUserWatchlist();
        const reserveTickers = await StockService.getUserReserve();
        
        if (watchlistTickers.length > 0) {
          const watchlistPromises = watchlistTickers.map(symbol => 
            StockService.getStockInfo(symbol)
          );
          const watchlistStocks = await Promise.all(watchlistPromises);
          setOwnedStocks(watchlistStocks);
        }
        
        if (reserveTickers.length > 0) {
          const reservePromises = reserveTickers.map(symbol => 
            StockService.getStockInfo(symbol)
          );
          const reserveStocksData = await Promise.all(reservePromises);
          setReserveStocks(reserveStocksData);
        }
      } catch (err) {
        console.error('Failed to load initial stocks:', err);
      }
    };

    loadInitialStocks();
  }, []);

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

  const removeStock = async (symbol: string): Promise<void> => {
    try {
      await StockService.removeFromWatchlist(symbol);
      setOwnedStocks(prevStocks => prevStocks.filter(stock => stock.symbol !== symbol));
    } catch (err) {
      console.error(`Failed to remove ${symbol}:`, err);
    }
  };

  const removeReserveStock = async (symbol: string): Promise<void> => {
    try {
      await StockService.removeFromReserve(symbol);
      setReserveStocks(prevStocks => prevStocks.filter(stock => stock.symbol !== symbol));
    } catch (err) {
      console.error(`Failed to remove ${symbol}:`, err);
    }
  };

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

  const openAddForm = (): void => {
    setShowAddForm(prev => !prev);
  };

  const cancelAddForm = (): void => {
    setShowAddForm(false);
  };

  const openReserveAddForm = (): void => {
    setShowReserveAddForm(prev => !prev);
  };

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

const Dashboard: React.FC = () => {
  return (
    <ToastProvider>
      <DashboardContent />
    </ToastProvider>
  );
};

export default Dashboard;