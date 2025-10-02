import React, { useState, useEffect } from 'react';
import { StockSuggestion, AddStockFormProps } from '../utils/types.ts';
import { StockService } from '../../../services/stocks.ts'
import { useToast } from './toast-context.tsx';

/**
 * Form component for adding stocks to watchlist with validation and suggestions.
 * Provides real-time ticker search, validation, and prevents duplicate additions.
 * 
 * @param props - The component props.
 * @param props.onAddStock - Function to call when a valid stock is added.
 * @param props.onCancel - Function to call when the form is cancelled.
 * @param props.existingStocks - Array of existing stock tickers to prevent duplicates.
 * @param props.targetList - Optional target list ('watchlist' or  'reserve') for error messages.
 */
export const AddStockForm: React.FC<AddStockFormProps> = ({ 
  onAddStock, 
  onCancel, 
  existingStocks,
  targetList = 'watchlist'
}) => {
  const { showToast } = useToast();
  const [ticker, setTicker] = useState('');
  const [suggestions, setSuggestions] = useState<StockSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastValidatedTicker, setLastValidatedTicker] = useState('');
  const [isLastValidationValid, setIsLastValidationValid] = useState(false);
  const formRef = React.useRef<HTMLDivElement>(null);

  /**
   * Fetches stock suggestions based on user input with debouncing.
   */
  useEffect(() => {
    if (ticker.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const timeoutId = setTimeout(async () => {
      try {
        setLoading(true);
        const response = await StockService.searchStocks(ticker, 5);
        setSuggestions(response.suggestions || []);
        setShowSuggestions(response.suggestions?.length > 0);
      } catch (err) {
        console.error('Failed to fetch suggestions:', err);
        setSuggestions([]);
        setShowSuggestions(false);
        if (err instanceof Error && err.message.includes('Search service')) {
          showToast('Search service temporarily unavailable', 'error');
        }
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [ticker, showToast]);

  /**
   * Closes dropdown when clicking outside the form region.
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (formRef.current && !formRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  /**
   * Validates a stock ticker using the API service.
   * 
   * @param tickerToValidate - The stock ticker symbol to validate.
   * @returns Promise resolving to validation result with optional error message.
   */
  const validateTicker = async (tickerToValidate: string): Promise<{valid: boolean, error?: string}> => {
    try {
      const response = await StockService.validateTicker(tickerToValidate);
      return { 
        valid: response.valid, 
        error: response.error ?? undefined
      };
    } catch (err) {
      console.error('Failed to validate ticker:', err);
      return { valid: false, error: 'Network error. Please try again.' };
    }
  };

  /**
   * Handles form submission and stock validation.
   */
  const handleSubmit = async (): Promise<void> => {
    const trimmedTicker = ticker.trim().toUpperCase();
    
    if (!trimmedTicker) {
      setError('Please enter a stock ticker');
      return;
    }

    if (existingStocks.includes(trimmedTicker)) {
      setError(`${trimmedTicker} is already in your ${targetList}`);
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const result = await validateTicker(trimmedTicker);
      setLastValidatedTicker(trimmedTicker);
      setIsLastValidationValid(result.valid);
      
      if (!result.valid) {
        setError(result.error || 'Invalid stock ticker.');
        return;
      }

      onAddStock(trimmedTicker);
      setTicker('');
      setError('');
      setLastValidatedTicker('');
      setIsLastValidationValid(false);
    } catch (err) {
      const errorMessage = 'Network error. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handles selection of a stock suggestion from the dropdown.
   * 
   * @param suggestion - The selected stock suggestion object.
   */
  const selectSuggestion = (suggestion: StockSuggestion): void => {
    setTicker(suggestion.symbol);
    setSuggestions([]);
    setShowSuggestions(false);
    setLastValidatedTicker(suggestion.symbol);
    setIsLastValidationValid(true);
    setError('');
  };

  /**
   * Handles keyboard events for form interaction.
   * 
   * @param e - The keyboard event from the input field.
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === 'Enter') {
      handleSubmit();
    } else if (e.key === 'Escape') {
      onCancel();
    }
  };

  /**
   * Handles input changes and clears validation state when ticker is modified.
   * 
   * @param e - The change event from the input field.
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    setTicker(e.target.value.toUpperCase());
    if (error) {
      setError('');
    }
    if (lastValidatedTicker !== e.target.value.toUpperCase().trim()) {
      setLastValidatedTicker('');
      setIsLastValidationValid(false);
    }
  };

  /**
   * Determines if the stock can be added based on validation state.
   * 
   * @returns True if the stock can be added, false otherwise.
   */
  const canAddStock = (): boolean => {
    const trimmedTicker = ticker.trim().toUpperCase();
    
    if (!trimmedTicker || loading) {
      return false;
    }
    
    if (existingStocks.includes(trimmedTicker)) {
      return false;
    }
    
    return lastValidatedTicker === trimmedTicker && isLastValidationValid;
  };

  return (
    <section className="add-stock-form" aria-labelledby="add-stock-title" ref={formRef}>
      <div className="form-row">
        <div className="input-container">
          <input
            type="text"
            placeholder="Enter ticker"
            value={ticker}
            onChange={handleInputChange}
            className={`stock-input ${error ? 'error' : ''}`}
            onKeyDown={handleKeyDown}
            autoFocus
            aria-describedby={error ? "input-error" : undefined}
          />
          
          {showSuggestions && suggestions.length > 0 && (
            <div className="suggestions-dropdown">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion.symbol}
                  className="suggestion-item"
                  onClick={() => selectSuggestion(suggestion)}
                >
                  <span className="symbol">{suggestion.symbol}</span>
                  <span className="name">{suggestion.name}</span>
                </button>
              ))}
            </div>
          )}
          
          {error && (
            <div id="input-error" className="input-error" role="alert">
              {error}
            </div>
          )}
        </div>
      </div>
      
      <div className="form-buttons">
        <button 
          className={`form-button ${canAddStock() ? 'primary' : 'secondary'}`}
          onClick={handleSubmit}
          type="button"
          disabled={!canAddStock()}
        >
          Add Stock
        </button>
        <button 
          className="form-button secondary" 
          onClick={onCancel}
          type="button"
        >
          Cancel
        </button>
      </div>
    </section>
  );
};