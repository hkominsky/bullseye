import React from 'react';
import { ReserveListProps } from '../utils/types.ts';
import { StockCard } from './stock-card.tsx';
import { AddStockForm } from './add-stock-form.tsx';

/**
 * EmptyState component that displays a message when the reserve list is empty.
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
 * ReserveList component that displays a user's reserve stocks with add/remove functionality.
 * Reserve stocks cannot have emails created with them, but can be moved to the watchlist.
 * 
 * @param props - The component props.
 * @param props.stocks - Array of stock objects to display.
 * @param props.onRemoveStock - Function to call when removing a stock.
 * @param props.onAddStock - Function to call when adding a stock.
 * @param props.showAddForm - Whether to show the add stock form.
 * @param props.existingStocks - Array of existing stock symbols to prevent duplicates.
 * @param props.onCancelAddForm - Function to call when cancelling the add form.
 * @param props.onToggleAddForm - Function to call when toggling add form visibility.
 * @param props.onMoveToWatchlist - Function to move stock to watchlist.
 */
export const ReserveList: React.FC<ReserveListProps> = ({ 
  stocks, 
  onRemoveStock,
  onAddStock,
  showAddForm,
  existingStocks,
  onCancelAddForm,
  onToggleAddForm,
  onMoveToWatchlist
}) => (
  <main className="reserve-section">
    <div className="section-header">
      <h1 className="section-title">Reserve</h1>
      <div className="watchlist-buttons">
        <button 
          className="list-button"
          onClick={onToggleAddForm}
          type="button"
        >
          +
        </button>
      </div>
    </div>
    
    {showAddForm && (
      <AddStockForm 
        onAddStock={onAddStock}
        onCancel={onCancelAddForm}
        existingStocks={existingStocks}
        targetList="reserve"
      />
    )}
    
    {stocks.length > 0 ? (
      <div className="stocks-grid" role="list" aria-label="Reserve stocks">
        {stocks.map((stock) => (
          <div key={stock.symbol} role="listitem">
            <StockCard 
              stock={stock} 
              onRemove={onRemoveStock}
              onMoveToWatchlist={onMoveToWatchlist}
              isReserveList={true}
            />
          </div>
        ))}
      </div>
    ) : (
      <EmptyState 
        title="Your reserve list is empty"
        description="Add stocks to your reserve list to keep track without email notifications"
      />
    )}
  </main>
);