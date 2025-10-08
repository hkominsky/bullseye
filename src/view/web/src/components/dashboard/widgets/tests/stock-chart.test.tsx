import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { StockChart } from '../stock-chart.tsx';
import { PricePoint } from '../../utils/types.ts';

const mockPriceData: PricePoint[] = [
  { timestamp: '2025-10-01T00:00:00Z', price: 100 },
  { timestamp: '2025-10-02T00:00:00Z', price: 105 },
  { timestamp: '2025-10-03T00:00:00Z', price: 102 },
  { timestamp: '2025-10-04T00:00:00Z', price: 108 },
  { timestamp: '2025-10-05T00:00:00Z', price: 110 }
];

const mockDecreasingData: PricePoint[] = [
  { timestamp: '2025-10-01T00:00:00Z', price: 110 },
  { timestamp: '2025-10-02T00:00:00Z', price: 108 },
  { timestamp: '2025-10-03T00:00:00Z', price: 105 },
  { timestamp: '2025-10-04T00:00:00Z', price: 102 },
  { timestamp: '2025-10-05T00:00:00Z', price: 100 }
];

const renderStockChart = (props = {}) => {
  const defaultProps = {
    data: mockPriceData,
    changePercent: 10,
    ...props
  };

  return render(<StockChart {...defaultProps} />);
};

describe('StockChart Component', () => {
  describe('Rendering', () => {
    it('should render chart container', () => {
      const { container } = renderStockChart();

      expect(container.querySelector('.stock-chart')).toBeInTheDocument();
    });

    it('should render SVG element', () => {
      const { container } = renderStockChart();

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should render SVG with correct class', () => {
      const { container } = renderStockChart();

      const svg = container.querySelector('.stock-chart-svg');
      expect(svg).toBeInTheDocument();
    });

    it('should set correct viewBox dimensions', () => {
      const { container } = renderStockChart();

      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('viewBox', '0 0 280 75');
    });

    it('should set correct SVG height', () => {
      const { container } = renderStockChart();

      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('height', '75');
    });

    it('should set width to 100%', () => {
      const { container } = renderStockChart();

      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('width', '100%');
    });

    it('should set preserveAspectRatio to none', () => {
      const { container } = renderStockChart();

      const svg = container.querySelector('svg');
      expect(svg).toHaveAttribute('preserveAspectRatio', 'none');
    });
  });

  describe('Placeholder Display', () => {
    it('should show placeholder when data is undefined', () => {
      renderStockChart({ data: undefined });

      expect(screen.getByText('No chart data')).toBeInTheDocument();
    });

    it('should show placeholder when data is null', () => {
      renderStockChart({ data: null });

      expect(screen.getByText('No chart data')).toBeInTheDocument();
    });

    it('should show placeholder when data is empty array', () => {
      renderStockChart({ data: [] });

      expect(screen.getByText('No chart data')).toBeInTheDocument();
    });

    it('should show placeholder when data has only one point', () => {
      renderStockChart({ 
        data: [{ timestamp: '2025-10-01T00:00:00Z', price: 100 }] 
      });

      expect(screen.getByText('No chart data')).toBeInTheDocument();
    });

    it('should show placeholder with correct class', () => {
      const { container } = renderStockChart({ data: [] });

      const placeholder = container.querySelector('.stock-chart-placeholder');
      expect(placeholder).toBeInTheDocument();
      expect(placeholder).toHaveTextContent('No chart data');
    });

    it('should not show placeholder when data has minimum required points', () => {
      renderStockChart({ 
        data: [
          { timestamp: '2025-10-01T00:00:00Z', price: 100 },
          { timestamp: '2025-10-02T00:00:00Z', price: 105 }
        ] 
      });

      expect(screen.queryByText('No chart data')).not.toBeInTheDocument();
    });
  });

  describe('SVG Paths', () => {
    it('should render line path', () => {
      const { container } = renderStockChart();

      const paths = container.querySelectorAll('path');
      expect(paths.length).toBeGreaterThan(0);
    });

    it('should render area path for gradient fill', () => {
      const { container } = renderStockChart();

      const paths = container.querySelectorAll('path');
      expect(paths.length).toBe(2);
    });

    it('should render line path with stroke', () => {
      const { container } = renderStockChart();

      const paths = container.querySelectorAll('path');
      const linePath = paths[1];
      
      expect(linePath).toHaveAttribute('stroke');
      expect(linePath.getAttribute('stroke')).toBeTruthy();
    });

    it('should render line path with correct stroke width', () => {
      const { container } = renderStockChart();

      const paths = container.querySelectorAll('path');
      const linePath = paths[1];
      
      expect(linePath).toHaveAttribute('strokeWidth', '1.5');
    });

    it('should render line path with no fill', () => {
      const { container } = renderStockChart();

      const paths = container.querySelectorAll('path');
      const linePath = paths[1];
      
      expect(linePath).toHaveAttribute('fill', 'none');
    });

    it('should render line path with round linecap', () => {
      const { container } = renderStockChart();

      const paths = container.querySelectorAll('path');
      const linePath = paths[1];
      
      expect(linePath).toHaveAttribute('strokeLinecap', 'round');
    });

    it('should render line path with round linejoin', () => {
      const { container } = renderStockChart();

      const paths = container.querySelectorAll('path');
      const linePath = paths[1];
      
      expect(linePath).toHaveAttribute('strokeLinejoin', 'round');
    });

    it('should generate valid d attribute for line path', () => {
      const { container } = renderStockChart();

      const paths = container.querySelectorAll('path');
      const linePath = paths[1];
      const dAttr = linePath.getAttribute('d');
      
      expect(dAttr).toBeTruthy();
      expect(dAttr).toContain('M ');
      expect(dAttr).toContain(' L ');
    });

    it('should generate valid d attribute for area path', () => {
      const { container } = renderStockChart();

      const paths = container.querySelectorAll('path');
      const areaPath = paths[0];
      const dAttr = areaPath.getAttribute('d');
      
      expect(dAttr).toBeTruthy();
      expect(dAttr).toContain('M ');
      expect(dAttr).toContain('Z');
    });
  });

  describe('Gradient Configuration', () => {
    it('should render linear gradient definition', () => {
      const { container } = renderStockChart();

      const gradient = container.querySelector('linearGradient');
      expect(gradient).toBeInTheDocument();
    });

    it('should have unique gradient ID', () => {
      const { container: container1 } = renderStockChart();
      const { container: container2 } = renderStockChart();

      const gradient1 = container1.querySelector('linearGradient');
      const gradient2 = container2.querySelector('linearGradient');
      
      const id1 = gradient1?.getAttribute('id');
      const id2 = gradient2?.getAttribute('id');
      
      expect(id1).toBeTruthy();
      expect(id2).toBeTruthy();
      expect(id1).not.toBe(id2);
    });

    it('should set gradient x1 to 0%', () => {
      const { container } = renderStockChart();

      const gradient = container.querySelector('linearGradient');
      expect(gradient).toHaveAttribute('x1', '0%');
    });

    it('should set gradient y1 to 0%', () => {
      const { container } = renderStockChart();

      const gradient = container.querySelector('linearGradient');
      expect(gradient).toHaveAttribute('y1', '0%');
    });

    it('should set gradient x2 to 0%', () => {
      const { container } = renderStockChart();

      const gradient = container.querySelector('linearGradient');
      expect(gradient).toHaveAttribute('x2', '0%');
    });

    it('should set gradient y2 to 100%', () => {
      const { container } = renderStockChart();

      const gradient = container.querySelector('linearGradient');
      expect(gradient).toHaveAttribute('y2', '100%');
    });

    it('should render two gradient stops', () => {
      const { container } = renderStockChart();

      const stops = container.querySelectorAll('stop');
      expect(stops.length).toBe(2);
    });

    it('should set first stop offset to 0%', () => {
      const { container } = renderStockChart();

      const stops = container.querySelectorAll('stop');
      expect(stops[0]).toHaveAttribute('offset', '0%');
    });

    it('should set second stop offset to 100%', () => {
      const { container } = renderStockChart();

      const stops = container.querySelectorAll('stop');
      expect(stops[1]).toHaveAttribute('offset', '100%');
    });

    it('should apply gradient fill to area path', () => {
      const { container } = renderStockChart();

      const gradient = container.querySelector('linearGradient');
      const gradientId = gradient?.getAttribute('id');
      
      const paths = container.querySelectorAll('path');
      const areaPath = paths[0];
      
      expect(areaPath).toHaveAttribute('fill', `url(#${gradientId})`);
    });
  });

  describe('Positive Change Colors', () => {
    it('should use green stroke for positive change', () => {
      const { container } = renderStockChart({ changePercent: 5 });

      const paths = container.querySelectorAll('path');
      const linePath = paths[1];
      
      expect(linePath).toHaveAttribute('stroke', '#22c55e');
    });

    it('should use green gradient for positive change', () => {
      const { container } = renderStockChart({ changePercent: 5 });

      const stops = container.querySelectorAll('stop');
      
      expect(stops[0]).toHaveAttribute('stopColor', '#22c55e');
      expect(stops[1]).toHaveAttribute('stopColor', '#22c55e');
    });

    it('should use correct opacity for positive gradient start', () => {
      const { container } = renderStockChart({ changePercent: 5 });

      const stops = container.querySelectorAll('stop');
      expect(stops[0]).toHaveAttribute('stopOpacity', '0.25');
    });

    it('should use correct opacity for positive gradient end', () => {
      const { container } = renderStockChart({ changePercent: 5 });

      const stops = container.querySelectorAll('stop');
      expect(stops[1]).toHaveAttribute('stopOpacity', '0.02');
    });

    it('should use green colors for zero change', () => {
      const { container } = renderStockChart({ changePercent: 0 });

      const paths = container.querySelectorAll('path');
      const linePath = paths[1];
      
      expect(linePath).toHaveAttribute('stroke', '#22c55e');
    });
  });

  describe('Negative Change Colors', () => {
    it('should use red stroke for negative change', () => {
      const { container } = renderStockChart({ changePercent: -5 });

      const paths = container.querySelectorAll('path');
      const linePath = paths[1];
      
      expect(linePath).toHaveAttribute('stroke', '#ef4444');
    });

    it('should use red gradient for negative change', () => {
      const { container } = renderStockChart({ changePercent: -5 });

      const stops = container.querySelectorAll('stop');
      
      expect(stops[0]).toHaveAttribute('stopColor', '#ef4444');
      expect(stops[1]).toHaveAttribute('stopColor', '#ef4444');
    });

    it('should use correct opacity for negative gradient start', () => {
      const { container } = renderStockChart({ changePercent: -5 });

      const stops = container.querySelectorAll('stop');
      expect(stops[0]).toHaveAttribute('stopOpacity', '0.25');
    });

    it('should use correct opacity for negative gradient end', () => {
      const { container } = renderStockChart({ changePercent: -5 });

      const stops = container.querySelectorAll('stop');
      expect(stops[1]).toHaveAttribute('stopOpacity', '0.02');
    });
  });

  describe('Data Point Handling', () => {
    it('should render chart with minimum two data points', () => {
      const { container } = renderStockChart({
        data: [
          { timestamp: '2025-10-01T00:00:00Z', price: 100 },
          { timestamp: '2025-10-02T00:00:00Z', price: 105 }
        ]
      });

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should render chart with many data points', () => {
      const manyPoints = Array.from({ length: 100 }, (_, i) => ({
        timestamp: `2025-10-${String(i + 1).padStart(2, '0')}T00:00:00Z`,
        price: 100 + Math.random() * 10
      }));

      const { container } = renderStockChart({ data: manyPoints });

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should handle data with same prices', () => {
      const flatData = [
        { timestamp: '2025-10-01T00:00:00Z', price: 100 },
        { timestamp: '2025-10-02T00:00:00Z', price: 100 },
        { timestamp: '2025-10-03T00:00:00Z', price: 100 }
      ];

      const { container } = renderStockChart({ data: flatData });

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should handle increasing price trend', () => {
      const { container } = renderStockChart({ data: mockPriceData });

      const paths = container.querySelectorAll('path');
      expect(paths.length).toBe(2);
    });

    it('should handle decreasing price trend', () => {
      const { container } = renderStockChart({ data: mockDecreasingData });

      const paths = container.querySelectorAll('path');
      expect(paths.length).toBe(2);
    });

    it('should handle very small price differences', () => {
      const smallDiffData = [
        { timestamp: '2025-10-01T00:00:00Z', price: 100.00 },
        { timestamp: '2025-10-02T00:00:00Z', price: 100.01 },
        { timestamp: '2025-10-03T00:00:00Z', price: 100.02 }
      ];

      const { container } = renderStockChart({ data: smallDiffData });

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should handle very large price differences', () => {
      const largeDiffData = [
        { timestamp: '2025-10-01T00:00:00Z', price: 100 },
        { timestamp: '2025-10-02T00:00:00Z', price: 1000 },
        { timestamp: '2025-10-03T00:00:00Z', price: 10000 }
      ];

      const { container } = renderStockChart({ data: largeDiffData });

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle negative prices', () => {
      const negativeData = [
        { timestamp: '2025-10-01T00:00:00Z', price: -10 },
        { timestamp: '2025-10-02T00:00:00Z', price: -5 },
        { timestamp: '2025-10-03T00:00:00Z', price: 0 }
      ];

      const { container } = renderStockChart({ data: negativeData });

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should handle very small positive changePercent', () => {
      const { container } = renderStockChart({ changePercent: 0.01 });

      const paths = container.querySelectorAll('path');
      const linePath = paths[1];
      
      expect(linePath).toHaveAttribute('stroke', '#22c55e');
    });

    it('should handle very small negative changePercent', () => {
      const { container } = renderStockChart({ changePercent: -0.01 });

      const paths = container.querySelectorAll('path');
      const linePath = paths[1];
      
      expect(linePath).toHaveAttribute('stroke', '#ef4444');
    });

    it('should handle very large positive changePercent', () => {
      const { container } = renderStockChart({ changePercent: 1000 });

      const paths = container.querySelectorAll('path');
      const linePath = paths[1];
      
      expect(linePath).toHaveAttribute('stroke', '#22c55e');
    });

    it('should handle very large negative changePercent', () => {
      const { container } = renderStockChart({ changePercent: -1000 });

      const paths = container.querySelectorAll('path');
      const linePath = paths[1];
      
      expect(linePath).toHaveAttribute('stroke', '#ef4444');
    });

    it('should handle decimal prices', () => {
      const decimalData = [
        { timestamp: '2025-10-01T00:00:00Z', price: 100.123 },
        { timestamp: '2025-10-02T00:00:00Z', price: 100.456 },
        { timestamp: '2025-10-03T00:00:00Z', price: 100.789 }
      ];

      const { container } = renderStockChart({ data: decimalData });

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('SVG Structure', () => {
    it('should render defs element', () => {
      const { container } = renderStockChart();

      const defs = container.querySelector('defs');
      expect(defs).toBeInTheDocument();
    });

    it('should contain gradient inside defs', () => {
      const { container } = renderStockChart();

      const defs = container.querySelector('defs');
      const gradient = defs?.querySelector('linearGradient');
      
      expect(gradient).toBeInTheDocument();
    });

    it('should render area path before line path', () => {
      const { container } = renderStockChart();

      const paths = container.querySelectorAll('path');
      const areaPath = paths[0];
      const linePath = paths[1];
      
      expect(areaPath).toHaveAttribute('fill');
      expect(linePath).toHaveAttribute('stroke');
    });
  });

  describe('Gradient ID Generation', () => {
    it('should generate gradient ID with correct prefix', () => {
      const { container } = renderStockChart();

      const gradient = container.querySelector('linearGradient');
      const id = gradient?.getAttribute('id');
      
      expect(id).toMatch(/^stock-chart-gradient-/);
    });

    it('should generate unique IDs for multiple charts', () => {
      const ids = new Set<string>();
      
      for (let i = 0; i < 10; i++) {
        const { container } = renderStockChart();
        const gradient = container.querySelector('linearGradient');
        const id = gradient?.getAttribute('id');
        if (id) ids.add(id);
      }
      
      expect(ids.size).toBe(10);
    });
  });
});