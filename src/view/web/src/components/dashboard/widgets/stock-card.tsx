import React, { useState, useRef, useEffect } from 'react';
import { StockCardProps } from '../utils/types.ts';
import { StockChart } from './stock-chart.tsx';

/**
 * StockCard component that displays a single stock's information. Shows symbol, price, price change,
 * percent change, and a graph of the stock performance.
 * 
 * @param props - The component props.
 * @param props.stock - Stock object containing all stock data to display.
 * @param props.onRemove - Function to call when removing stock.
 * @param props.onMoveToReserve - Optional function to move stock to reserve list.
 * @param props.onMoveToWatchlist - Optional function to move stock to watchlist.
 * @param props.isReserveList - Boolean indicating if this card is in the reserve list.
 */
export const StockCard: React.FC<StockCardProps> = ({ 
  stock, 
  onRemove,
  onMoveToReserve,
  onMoveToWatchlist,
  onSendEmail,
  isReserveList = false
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  /**
   * Effect to handle clicks outside the dropdown menu to close it.
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  /**
   * Toggles the dropdown menu open/closed state.
   */
  const handleMenuToggle = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  /**
   * Handles removing the stock from the list.
   */
  const handleRemove = () => {
    onRemove(stock.symbol);
    setIsMenuOpen(false);
  };

  /**
   * Handles moving the stock between watchlist and reserve list.
   */
  const handleMove = () => {
    if (isReserveList && onMoveToWatchlist) {
      onMoveToWatchlist(stock.symbol);
    } else if (!isReserveList && onMoveToReserve) {
      onMoveToReserve(stock.symbol);
    }
    setIsMenuOpen(false);
  };

  /**
   * Handles sending email for this specific stock.
   */
  const handleSendEmail = () => {
    if (onSendEmail) {
      onSendEmail(stock.symbol);
    }
    setIsMenuOpen(false);
  };

  /**
   * Formats a numeric value into a human-readable string with appropriate suffix.
   * 
   * @param num - The numeric value to format.
   * @returns A formatted string with the appropriate suffix, or 'N/A' if the input is invalid.
   */
  const formatNumeric = (num: number): string => {
    if (num === null || num === undefined || isNaN(num)) return 'N/A';

    if (num >= 1e12) {
      return `${(num / 1e12).toFixed(2)}T`;
    } else if (num >= 1e9) {
      return `${(num / 1e9).toFixed(2)}B`;
    } else if (num >= 1e6) {
      return `${(num / 1e6).toFixed(2)}M`;
    } else if (num >= 1e3) {
      return `${(num / 1e3).toFixed(2)}K`;
    }

    return num.toString();
  };

  const isPositive = stock.percentChange ? stock.percentChange >= 0 : false;

  return (
    <div className="stock-card">
      <div className="stock-card-header">
        <div className="stock-info">
          <h3 className="stock-symbol">{stock.symbol}</h3>
          <span className="stock-name">{stock.name}</span>
        </div>
        <div className="stock-actions">
          <div className="menu-dropdown" ref={menuRef}>
            <button 
              className="stock-action-button menu-button"
              onClick={handleMenuToggle}
              title="Stock options"
            >
              ⋯
            </button>
            {isMenuOpen && (
              <div className="dropdown-menu">
                {!isReserveList && (
                  <button 
                    className="dropdown-item"
                    onClick={handleSendEmail}
                  >
                    ✉ Email
                  </button>
                )}
                <button 
                  className="dropdown-item"
                  onClick={handleMove}
                >
                  {isReserveList ? '🡩 Watchlist' : '🡫 Reserve'}
                </button>
                <button 
                  className="dropdown-item"
                  onClick={handleRemove}
                >
                  ✖ Delete
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
      
      <div className="stock-price-row">
        <span className="stock-price">
          {stock.price !== null ? stock.price.toFixed(2) : 'N/A'}
        </span>
        <span className={`stock-price-change ${isPositive ? 'positive' : 'negative'}`}>
          {stock.priceChange !== null ? `(${isPositive ? '+' : ''}${stock.priceChange.toFixed(2)})` : 'N/A'}
        </span>
        <span className={`stock-percent-change ${isPositive ? 'positive' : 'negative'}`}>
          {stock.percentChange !== null ? `${isPositive ? '+' : ''}${stock.percentChange.toFixed(2)}% ${isPositive ? '🡩' : '🡫'}` : 'N/A'}
        </span>
      </div>

      <div className="stock-details">
        <div className="detail-row">
          <span className="label">Mkt Cap:</span>
          <span className="value">
            {stock.marketCap ? `${formatNumeric(stock.marketCap)}` : 'N/A'}
          </span>
        </div>

        <div className="detail-row">
          <span className="label">Vol:</span>
          <span className="value">
            {stock.volume ? `${formatNumeric(stock.volume)}` : 'N/A'}
          </span>
        </div>

        <div className="detail-row">
          <span className="label">Avg Vol:</span>
          <span className="value">
            {stock.avgVolume ? `${formatNumeric(stock.avgVolume)}` : 'N/A'}
          </span>
        </div>

        <div className="detail-row">
          <span className="label">RVOL:</span>
            <span className="value">
              {stock.relativeVolume !== null ? `${stock.relativeVolume.toFixed(2)}%` : 'N/A'}
            </span>
        </div>
        
        <div className="detail-row">
          <span className="label">P/E Ratio:</span>
          <span className="value">
            {stock.peRatio !== null ? stock.peRatio.toFixed(2) : 'N/A'}
          </span>
        </div>

        <div className="detail-row">
          <span className="label">Trailing EPS:</span>
          <span className="value">
            {stock.trailingEPS !== null ? stock.trailingEPS.toFixed(2) : 'N/A'}
          </span>
        </div>
        
        <div className="detail-row">
          <span className="label">Forward EPS:</span>
          <span className="value">
            {stock.forwardEPS !== null ? stock.forwardEPS.toFixed(2) : 'N/A'}
          </span>
        </div>

        <div className="detail-row">
          <span className="label">Next Earnings:</span>
          <span className="value">
            {stock.nextEarningsDate 
              ? new Date(stock.nextEarningsDate).toLocaleDateString() 
              : 'N/A'}
          </span>
        </div>
        
        <div className="detail-row">
          <span className="label">Recommendation:</span>
          <span className="value">{stock.recommendation || 'N/A'}</span>
        </div>
      </div>

      <div className="stock-chart-section">
        <StockChart
          data={stock.priceHistory} 
          changePercent={stock.percentChange ?? 0}
        />
      </div>
    </div>
  );
};