export interface PricePoint {
  timestamp: string;
  price: number;
}

export interface Stock {
  symbol: string;
  name: string;
  price: number;
  priceChange: number;
  percentChange: number;
  priceHistory: PricePoint[];
  marketCap: number;
  volume: number;
  avgVolume: number;
  relativeVolume: number;
  nextEarningsDate: string;
  peRatio: number;
  trailingEPS: number;
  forwardEPS: number;
  recommendation: string;
}

export interface StockChartProps {
  data: PricePoint[];
  changePercent: number;
}

export interface StockCardProps {
  stock: Stock;
  onRemove: (symbol: string) => void;
  onMoveToReserve?: (symbol: string) => void;
  onMoveToWatchlist?: (symbol: string) => void;
  onSendEmail?: (symbol: string) => void;
  isReserveList?: boolean;
}

export interface StockSuggestion {
  symbol: string;
  name: string;
}

export interface AddStockFormProps {
  onAddStock: (ticker: string) => void;
  onCancel: () => void;
  existingStocks: string[];
  targetList?: 'watchlist' | 'reserve';
}

export interface WatchlistProps {
  stocks: Stock[];
  onRemoveStock: (symbol: string) => void;
  onAddStock: (ticker: string) => void;
  showAddForm: boolean;
  existingStocks: string[];
  onCancelAddForm: () => void;
  onToggleAddForm: () => void;
  onMoveToReserve?: (symbol: string) => void;
  onEmailAll?: () => void;
  onSendEmail?: (symbol: string) => void;
  isEmailProcessing?: boolean;
}

export interface ReserveListProps {
  stocks: Stock[];
  onRemoveStock: (symbol: string) => void;
  onAddStock: (ticker: string) => void;
  showAddForm: boolean;
  existingStocks: string[];
  onCancelAddForm: () => void;
  onToggleAddForm: () => void;
  onMoveToWatchlist: (symbol: string) => void;
}

export interface CachedData {
  stocks: Stock[];
  timestamp: number;
}