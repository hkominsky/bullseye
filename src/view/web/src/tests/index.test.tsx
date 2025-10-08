import ReactDOM from 'react-dom/client';

// Mocks
jest.mock('react-dom/client', () => ({
  createRoot: jest.fn()
}));

jest.mock('../app.tsx', () => ({
  __esModule: true,
  default: () => <div>App Component</div>
}));

jest.mock('../styles/index.css', () => ({}));

describe('index.tsx', () => {
  let mockRoot: { render: jest.Mock };
  let mockCreateRoot: jest.Mock;
  let mockGetElementById: jest.SpyInstance;

  beforeEach(() => {
    mockRoot = {
      render: jest.fn()
    };

    mockCreateRoot = ReactDOM.createRoot as jest.Mock;
    mockCreateRoot.mockReturnValue(mockRoot);

    mockGetElementById = jest.spyOn(document, 'getElementById');
  });

  afterEach(() => {
    jest.clearAllMocks();
    mockGetElementById.mockRestore();
  });

  describe('Root Element', () => {
    it('should get root element by id', async () => {
      const mockElement = document.createElement('div');
      mockElement.id = 'root';
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockGetElementById).toHaveBeenCalledWith('root');
    });

    it('should call getElementById with "root"', async () => {
      const mockElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockGetElementById).toHaveBeenCalledWith('root');
      expect(mockGetElementById).toHaveBeenCalledTimes(1);
    });

    it('should use the element returned by getElementById', async () => {
      const mockElement = document.createElement('div');
      mockElement.id = 'root';
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockCreateRoot).toHaveBeenCalledWith(mockElement);
    });
  });

  describe('React Root Creation', () => {
    it('should create React root with root element', async () => {
      const mockElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockCreateRoot).toHaveBeenCalledWith(mockElement);
    });

    it('should call createRoot once', async () => {
      const mockElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockCreateRoot).toHaveBeenCalledTimes(1);
    });

    it('should cast root element as HTMLElement', async () => {
      const mockElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockCreateRoot).toHaveBeenCalledWith(expect.any(HTMLDivElement));
    });
  });

  describe('App Rendering', () => {
    it('should render App component', async () => {
      const mockElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockRoot.render).toHaveBeenCalled();
    });

    it('should call render method on root', async () => {
      const mockElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockRoot.render).toHaveBeenCalledTimes(1);
    });

    it('should render App component with JSX', async () => {
      const mockElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockRoot.render).toHaveBeenCalledWith(expect.anything());
    });
  });

  describe('Initialization Sequence', () => {
    it('should execute in correct order', async () => {
      const mockElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      const callOrder: string[] = [];

      mockGetElementById.mockImplementation((id) => {
        callOrder.push('getElementById');
        return mockElement;
      });

      mockCreateRoot.mockImplementation((element) => {
        callOrder.push('createRoot');
        return mockRoot;
      });

      mockRoot.render.mockImplementation(() => {
        callOrder.push('render');
      });

      await import('../index.tsx');

      expect(callOrder).toEqual(['getElementById', 'createRoot', 'render']);
    });

    it('should create root before rendering', async () => {
      const mockElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockCreateRoot).toHaveBeenCalled();
      expect(mockRoot.render).toHaveBeenCalled();
      
      const createRootCallOrder = mockCreateRoot.mock.invocationCallOrder[0];
      const renderCallOrder = mockRoot.render.mock.invocationCallOrder[0];
      
      expect(createRootCallOrder).toBeLessThan(renderCallOrder);
    });
  });

  describe('CSS Import', () => {
    it('should import index.css', async () => {
      const mockElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      await expect(import('../index.tsx')).resolves.toBeDefined();
    });
  });

  describe('Error Handling', () => {
    it('should handle null root element', async () => {
      mockGetElementById.mockReturnValue(null);

      await expect(import('../index.tsx')).rejects.toThrow();
    });

    it('should throw error when root element not found', async () => {
      mockGetElementById.mockReturnValue(null);

      await expect(import('../index.tsx')).rejects.toThrow();
    });
  });

  describe('Module Execution', () => {
    it('should execute immediately on import', async () => {
      const mockElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockCreateRoot).toHaveBeenCalled();
      expect(mockRoot.render).toHaveBeenCalled();
    });

    it('should only execute once', async () => {
      const mockElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockCreateRoot).toHaveBeenCalledTimes(1);
      expect(mockRoot.render).toHaveBeenCalledTimes(1);
    });
  });

  describe('DOM Integration', () => {
    it('should work with valid HTML element', async () => {
      const mockElement = document.createElement('div');
      mockElement.id = 'root';
      document.body.appendChild(mockElement);
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockCreateRoot).toHaveBeenCalledWith(mockElement);

      document.body.removeChild(mockElement);
    });

    it('should handle different element types', async () => {
      const mockElement = document.createElement('section');
      mockElement.id = 'root';
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockCreateRoot).toHaveBeenCalledWith(mockElement);
    });
  });

  describe('Type Safety', () => {
    it('should cast element as HTMLElement', async () => {
      const mockElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockCreateRoot).toHaveBeenCalledWith(expect.any(HTMLElement));
    });

    it('should handle HTMLElement type correctly', async () => {
      const mockElement: HTMLElement = document.createElement('div');
      mockGetElementById.mockReturnValue(mockElement);

      await import('../index.tsx');

      expect(mockCreateRoot).toHaveBeenCalledWith(mockElement);
    });
  });
});