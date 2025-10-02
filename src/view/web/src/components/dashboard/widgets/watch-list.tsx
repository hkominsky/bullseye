import React from 'react';
import { WatchlistProps } from '../utils/types.ts';
import { StockCard } from './stock-card.tsx';
import { AddStockForm } from './add-stock-form.tsx';

/**
 * EmptyState component that displays a message when the watchlist is empty.
 * 
 * @param props - The component props.
 * @param props.title - The main title to display.
 * @param props.description - The descriptive text to show below the title.
 * @returns A React functional component displaying an empty state message.
 */
const EmptyState: React.FC<{ title: string; description: string }> = ({ title, description }) => (
  <div className="empty-state">
    <div className="empty-state-icon">📈</div>
    <h3 className="empty-state-title">{title}</h3>
    <p className="empty-state-description">{description}</p>
  </div>
);

/**
 * Watchlist component that displays a user's stock watchlist with add/remove functionality.
 * 
 * @param props - The component props.
 * @param props.stocks - Array of stock objects to display.
 * @param props.onRemoveStock - Function to call when removing a stock.
 * @param props.onAddStock - Function to call when adding a stock.
 * @param props.showAddForm - Whether to show the add stock form.
 * @param props.existingStocks - Array of existing stock symbols to prevent duplicates.
 * @param props.onCancelAddForm - Function to call when cancelling the add form.
 * @param props.onToggleAddForm - Function to call when toggling add form visibility.
 * @param props.onMoveToReserve - Optional function to move stock to reserve list.
 * @param props.onEmailAll - Optional function to send emails for all watchlist stocks.
 * @param props.onSendEmail - Optional function to send email for a single stock.
 * @param props.isEmailProcessing - Optional boolean indicating if emails are being processed.
 */
export const Watchlist: React.FC<WatchlistProps> = ({ 
  stocks, 
  onRemoveStock,
  onAddStock,
  showAddForm,
  existingStocks,
  onCancelAddForm,
  onToggleAddForm,
  onMoveToReserve,
  onEmailAll,
  onSendEmail,
  isEmailProcessing
}) => (
  <main className="stocks-section">
    <div className="section-header">
      <h1 className="section-title">Watchlist</h1>
      <div className="watchlist-buttons">
        <button 
          className="list-button"
          onClick={onToggleAddForm}
          type="button"
          aria-label="Add stock to watchlist"
        >
          +
        </button>
        {onEmailAll && (
          <button 
            className="list-button"
            onClick={onEmailAll}
            type="button"
            disabled={isEmailProcessing || stocks.length === 0}
          >
            ✉ All
          </button>
        )}
      </div>
    </div>
    
    {showAddForm && (
      <AddStockForm 
        onAddStock={onAddStock}
        onCancel={onCancelAddForm}
        existingStocks={existingStocks}
        targetList="watchlist"
      />
    )}
    
    {stocks.length > 0 ? (
      <div className="stocks-grid" role="list" aria-label="Stock watchlist">
        {stocks.map((stock) => (
          <div key={stock.symbol} role="listitem">
            <StockCard 
              stock={stock} 
              onRemove={onRemoveStock}
              onMoveToReserve={onMoveToReserve}
              onSendEmail={onSendEmail}
              isReserveList={false}
            />
          </div>
        ))}
      </div>
    ) : (
      <EmptyState 
        title="Your watchlist is empty"
        description="Add stocks you're interested in to keep track of their performance"
      />
    )}
  </main>
);