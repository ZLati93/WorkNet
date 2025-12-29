/**
 * Tests for Freelancer Dashboard
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from '../src/pages/Dashboard';
import authService from '../src/services/authService';
import ordersService from '../src/services/ordersService';
import gigsService from '../src/services/gigsService';
import paymentsService from '../src/services/paymentsService';

// Mock services
vi.mock('../src/services/authService', () => ({
  default: {
    isAuthenticated: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}));

vi.mock('../src/services/ordersService', () => ({
  default: {
    getOrders: vi.fn(),
  },
}));

vi.mock('../src/services/gigsService', () => ({
  default: {
    getMyGigs: vi.fn(),
  },
}));

vi.mock('../src/services/paymentsService', () => ({
  default: {
    getEarningsSummary: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock recharts
vi.mock('recharts', () => ({
  BarChart: ({ children }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }) => <div data-testid="responsive-container">{children}</div>,
  LineChart: ({ children }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
}));

// Helper function to render with providers
const renderWithProviders = (component) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const mockUser = {
  id: '507f1f77bcf86cd799439011',
  username: 'freelancer1',
  email: 'freelancer@example.com',
  role: 'freelancer',
  totalEarnings: 1500,
  rating: 4.5,
};

const mockOrders = [
  {
    _id: '507f1f77bcf86cd799439020',
    gigId: { title: 'Logo Design' },
    buyerId: { username: 'client1' },
    price: 50,
    status: 'completed',
    createdAt: new Date().toISOString(),
  },
  {
    _id: '507f1f77bcf86cd799439021',
    gigId: { title: 'Web Development' },
    buyerId: { username: 'client2' },
    price: 100,
    status: 'pending',
    createdAt: new Date().toISOString(),
  },
];

const mockGigs = [
  {
    _id: '507f1f77bcf86cd799439030',
    title: 'Logo Design Service',
    isActive: true,
  },
  {
    _id: '507f1f77bcf86cd799439031',
    title: 'Web Development Service',
    isActive: true,
  },
];

describe('Dashboard Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    authService.isAuthenticated.mockReturnValue(true);
    authService.getCurrentUser.mockReturnValue(mockUser);
    ordersService.getOrders.mockResolvedValue({
      success: true,
      data: mockOrders,
    });
    gigsService.getMyGigs.mockResolvedValue({
      success: true,
      data: mockGigs,
    });
    paymentsService.getEarningsSummary.mockResolvedValue({
      success: true,
      totalEarnings: 1500,
      paymentCount: 10,
      period: 'month',
    });
  });

  it('redirects to login if not authenticated', () => {
    authService.isAuthenticated.mockReturnValue(false);

    renderWithProviders(<Dashboard />);

    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('renders dashboard title', () => {
    renderWithProviders(<Dashboard />);

    expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
  });

  it('displays stats cards', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/total gigs/i)).toBeInTheDocument();
      expect(screen.getByText(/total orders/i)).toBeInTheDocument();
      expect(screen.getByText(/total earnings/i)).toBeInTheDocument();
      expect(screen.getByText(/rating/i)).toBeInTheDocument();
    });
  });

  it('displays correct total gigs count', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      const totalGigsCard = screen.getByText(/total gigs/i).closest('div');
      expect(totalGigsCard).toHaveTextContent('2');
    });
  });

  it('displays correct total orders count', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      const totalOrdersCard = screen.getByText(/total orders/i).closest('div');
      expect(totalOrdersCard).toHaveTextContent('2');
    });
  });

  it('displays correct total earnings', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/\$1,500/)).toBeInTheDocument();
    });
  });

  it('displays correct rating', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/4\.5/)).toBeInTheDocument();
    });
  });

  it('displays charts', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/orders by status/i)).toBeInTheDocument();
      expect(screen.getByText(/earnings trend/i)).toBeInTheDocument();
    });

    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('displays recent orders section', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/recent orders/i)).toBeInTheDocument();
    });
  });

  it('displays recent orders list', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/logo design/i)).toBeInTheDocument();
      expect(screen.getByText(/web development/i)).toBeInTheDocument();
    });
  });

  it('displays order status badges', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/completed/i)).toBeInTheDocument();
      expect(screen.getByText(/pending/i)).toBeInTheDocument();
    });
  });

  it('displays order prices', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/\$50/)).toBeInTheDocument();
      expect(screen.getByText(/\$100/)).toBeInTheDocument();
    });
  });

  it('shows empty state when no orders', async () => {
    ordersService.getOrders.mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/no recent orders/i)).toBeInTheDocument();
    });
  });

  it('shows loading state while fetching data', () => {
    ordersService.getOrders.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );
    gigsService.getMyGigs.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );
    paymentsService.getEarningsSummary.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    renderWithProviders(<Dashboard />);

    // Should show loading indicators or stats with default values
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
  });

  it('calculates active gigs correctly', async () => {
    const gigsWithInactive = [
      ...mockGigs,
      {
        _id: '507f1f77bcf86cd799439032',
        title: 'Inactive Gig',
        isActive: false,
      },
    ];

    gigsService.getMyGigs.mockResolvedValue({
      success: true,
      data: gigsWithInactive,
    });

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      const totalGigsCard = screen.getByText(/total gigs/i).closest('div');
      expect(totalGigsCard).toHaveTextContent('3');
      expect(totalGigsCard).toHaveTextContent('2 active');
    });
  });

  it('calculates completed orders correctly', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      const totalOrdersCard = screen.getByText(/total orders/i).closest('div');
      expect(totalOrdersCard).toHaveTextContent('1 completed');
    });
  });

  it('handles error state gracefully', async () => {
    ordersService.getOrders.mockRejectedValue({
      message: 'Failed to load orders',
    });

    renderWithProviders(<Dashboard />);

    // Dashboard should still render even if some data fails to load
    await waitFor(() => {
      expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
    });
  });
});

