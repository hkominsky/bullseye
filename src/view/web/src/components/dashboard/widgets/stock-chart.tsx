import React from 'react';
import { PricePoint, StockChartProps } from '../utils/types';

const CHART_CONFIG = {
  WIDTH: 280,
  HEIGHT: 75,
  BORDER_RADIUS: 16,
  STROKE_WIDTH: 1.5,
  MIN_DATA_POINTS: 2,
  VISUAL_PADDING: 12,
} as const;

const BASE_COLORS = {
  POSITIVE: '#22c55e',
  NEGATIVE: '#ef4444',
} as const;

const OPACITY_VALUES = {
  HIGH: 0.25,
  LOW: 0.02,
  FULL: 1,
} as const;

const COLORS = {
  POSITIVE: BASE_COLORS.POSITIVE,
  NEGATIVE: BASE_COLORS.NEGATIVE,
  GRADIENT: {
    POSITIVE: {
      START: { color: BASE_COLORS.POSITIVE, opacity: OPACITY_VALUES.HIGH },
      END: { color: BASE_COLORS.POSITIVE, opacity: OPACITY_VALUES.LOW },
    },
    NEGATIVE: {
      START: { color: BASE_COLORS.NEGATIVE, opacity: OPACITY_VALUES.HIGH },
      END: { color: BASE_COLORS.NEGATIVE, opacity: OPACITY_VALUES.LOW },
    },
  },
} as const;

const CSS_CLASSES = {
  CONTAINER: 'stock-chart',
  PLACEHOLDER: 'stock-chart-placeholder',
  SVG: 'stock-chart-svg',
} as const;

const SVG_ATTRS = {
  WIDTH: '100%',
  PRESERVE_ASPECT_RATIO: 'none',
  STROKE_LINECAP: 'round',
  STROKE_LINEJOIN: 'round',
  FILL: 'none',
} as const;

const GRADIENT_CONFIG = {
  X1: '0%',
  Y1: '0%',
  X2: '0%',
  Y2: '100%',
  STOP_OFFSETS: {
    START: '0%',
    END: '100%',
  },
} as const;

/**
 * Calculates the minimum, maximum, and range of prices from price data.
 * 
 * @param data - Array of price points.
 * @returns Object containing minPrice, maxPrice, and priceRange.
 */
const calculatePriceRange = (data: PricePoint[]) => {
  const prices = data.map(d => d.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice || 1;
  return { minPrice, maxPrice, priceRange };
};

/**
 * Converts price data points to SVG coordinate points for chart rendering.
 * 
 * @param data - Array of price points.
 * @param minPrice - Minimum price value for scaling.
 * @param priceRange - Price range for scaling.
 * @returns Array of coordinate points with x and y values.
 */
const generateChartPoints = (data: PricePoint[], minPrice: number, priceRange: number) => {
  const { WIDTH, HEIGHT, VISUAL_PADDING } = CHART_CONFIG;
  const availableHeight = HEIGHT - (VISUAL_PADDING * 2);
  
  return data.map((point, index) => {
    const x = (index / (data.length - 1)) * WIDTH;
    const y = VISUAL_PADDING + (availableHeight - ((point.price - minPrice) / priceRange) * availableHeight);
    return { x, y };
  });
};

/**
 * Creates an SVG path string for the chart line from coordinate points.
 * 
 * @param points - Array of coordinate points.
 * @returns SVG path string for the line.
 */
const createLinePath = (points: { x: number; y: number }[]) => {
  return `M ${points.map(p => `${p.x},${p.y}`).join(' L ')}`;
};

/**
 * Creates an SVG path string for the chart area fill with rounded corners.
 * 
 * @param points - Array of coordinate points.
 * @returns SVG path string for the filled area.
 */
const createAreaPath = (points: { x: number; y: number }[]) => {
  const { WIDTH, HEIGHT, BORDER_RADIUS } = CHART_CONFIG;
  
  const smoothLinePath = createLinePath(points).substring(2);
  
  return `M ${BORDER_RADIUS},${HEIGHT} 
          Q 0,${HEIGHT} 0,${HEIGHT - BORDER_RADIUS}
          L 0,${points[0].y}
          ${smoothLinePath}
          L ${WIDTH},${points[points.length - 1].y}
          L ${WIDTH},${HEIGHT - BORDER_RADIUS}
          Q ${WIDTH},${HEIGHT} ${WIDTH - BORDER_RADIUS},${HEIGHT}
          Z`;
};

/**
 * Determines color scheme based on positive or negative change percentage.
 * 
 * @param changePercent - The percentage change value.
 * @returns Object containing stroke color and gradient colors.
 */
const getColorScheme = (changePercent: number) => {
  const isPositive = changePercent >= 0;
  return {
    strokeColor: isPositive ? COLORS.POSITIVE : COLORS.NEGATIVE,
    gradientColors: isPositive ? COLORS.GRADIENT.POSITIVE : COLORS.GRADIENT.NEGATIVE,
  };
};

/**
 * Generates a unique gradient ID for SVG gradient definition.
 * 
 * @returns Random unique gradient ID string.
 */
const generateGradientId = () => {
  return `stock-chart-gradient-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * StockChart component that renders an SVG line chart based on stock data.
 * 
 * @param props - The component props.
 * @param props.data - Array of price points to render as chart data.
 * @param props.changePercent - Percentage change to determine chart colors.
 */
export const StockChart: React.FC<StockChartProps> = ({ data, changePercent }) => {
  if (!data || data.length < CHART_CONFIG.MIN_DATA_POINTS) {
    return <div className={CSS_CLASSES.PLACEHOLDER}>{'No chart data'}</div>;
  }

  const { minPrice, priceRange } = calculatePriceRange(data);
  const points = generateChartPoints(data, minPrice, priceRange);
  const linePath = createLinePath(points);
  const areaPath = createAreaPath(points);
  const { strokeColor, gradientColors } = getColorScheme(changePercent);
  const gradientId = generateGradientId();
  
  const { WIDTH, HEIGHT, STROKE_WIDTH } = CHART_CONFIG;
  const viewBox = `0 0 ${WIDTH} ${HEIGHT}`;

  return (
    <div className={CSS_CLASSES.CONTAINER}>
      <svg 
        width={SVG_ATTRS.WIDTH} 
        height={HEIGHT} 
        className={CSS_CLASSES.SVG} 
        viewBox={viewBox} 
        preserveAspectRatio={SVG_ATTRS.PRESERVE_ASPECT_RATIO}
      >
        <defs>
          <linearGradient 
            id={gradientId} 
            x1={GRADIENT_CONFIG.X1} 
            y1={GRADIENT_CONFIG.Y1} 
            x2={GRADIENT_CONFIG.X2} 
            y2={GRADIENT_CONFIG.Y2}
          >
            <stop 
              offset={GRADIENT_CONFIG.STOP_OFFSETS.START} 
              stopColor={gradientColors.START.color} 
              stopOpacity={gradientColors.START.opacity} 
            />
            <stop 
              offset={GRADIENT_CONFIG.STOP_OFFSETS.END} 
              stopColor={gradientColors.END.color} 
              stopOpacity={gradientColors.END.opacity} 
            />
          </linearGradient>
        </defs>
        
        {/* Gradient fill */}
        <path d={areaPath} fill={`url(#${gradientId})`} />
        
        {/* Line */}
        <path
          d={linePath}
          stroke={strokeColor}
          strokeWidth={STROKE_WIDTH}
          fill={SVG_ATTRS.FILL}
          strokeLinecap={SVG_ATTRS.STROKE_LINECAP}
          strokeLinejoin={SVG_ATTRS.STROKE_LINEJOIN}
        />
      </svg>
    </div>
  );
};