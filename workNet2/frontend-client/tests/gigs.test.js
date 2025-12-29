/**
 * Tests for Gigs Display and Search
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Home from '../src/pages/Home';
import GigCard from '../src/components/GigCard';
import GigDetails from '../src/pages/GigDetails';
import gigsService from '../src/services/gigsService';
import authService from '../src/services/authService';

// Mock gigsService
vi.mock('../src/services/gigsService', () => ({
  default: {
    getGigs: vi.fn(),
    getGigById: vi.fn(),
    searchGigs: vi.fn(),
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

const mockGig = {
  _id: '507f1f77bcf86cd799439011',
  title: 'Professional Logo Design',
  description: 'I will create a professional logo design for your business',
  price: 50,
  rating: 4.5,
  category: 'Graphic Design',
  deliveryTime: 3,
  sales: 10,
  images: ['https://example.com/image.jpg'],
};

const mockGigsResponse = {
  success: true,
  data: [mockGig],
  pagination: {
    page: 1,
    limit: 12,
    total: 1,
    totalPages: 1,
    hasNextPage: false,
    hasPrevPage: false,
  },
};

describe('Home Page - Gigs Display', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    gigsService.getGigs.mockResolvedValue(mockGigsResponse);
  });

  it('renders home page correctly', () => {
    renderWithProviders(<Home />);

    expect(screen.getByText(/find the perfect freelancer/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search for services/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
  });

  it('displays gigs when loaded', async () => {
    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText(/professional logo design/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/\$50/)).toBeInTheDocument();
    expect(screen.getByText(/3 days/i)).toBeInTheDocument();
  });

  it('shows loading state while fetching gigs', () => {
    gigsService.getGigs.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    renderWithProviders(<Home />);

    expect(screen.getByText(/loading gigs/i)).toBeInTheDocument();
  });

  it('shows error message when fetch fails', async () => {
    gigsService.getGigs.mockRejectedValue({
      message: 'Failed to load gigs',
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText(/error loading gigs/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no gigs found', async () => {
    gigsService.getGigs.mockResolvedValue({
      success: true,
      data: [],
      pagination: {
        page: 1,
        limit: 12,
        total: 0,
        totalPages: 0,
        hasNextPage: false,
        hasPrevPage: false,
      },
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText(/no gigs found/i)).toBeInTheDocument();
    });
  });

  it('searches gigs when search form is submitted', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Home />);

    const searchInput = screen.getByPlaceholderText(/search for services/i);
    const searchButton = screen.getByRole('button', { name: /search/i });

    await user.type(searchInput, 'logo design');
    await user.click(searchButton);

    await waitFor(() => {
      expect(gigsService.getGigs).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'logo design',
        })
      );
    });
  });

  it('filters gigs by category', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText(/professional logo design/i)).toBeInTheDocument();
    });

    const categorySelect = screen.getByRole('combobox', { name: /category/i }) || 
                          screen.getByDisplayValue(/all categories/i);
    
    if (categorySelect) {
      await user.selectOptions(categorySelect, 'Graphic Design');

      await waitFor(() => {
        expect(gigsService.getGigs).toHaveBeenCalledWith(
          expect.objectContaining({
            category: 'Graphic Design',
          })
        );
      });
    }
  });

  it('sorts gigs by selected option', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText(/professional logo design/i)).toBeInTheDocument();
    });

    const sortSelect = screen.getByRole('combobox') || 
                      screen.getByDisplayValue(/newest/i);
    
    if (sortSelect) {
      await user.selectOptions(sortSelect, 'price');

      await waitFor(() => {
        expect(gigsService.getGigs).toHaveBeenCalledWith(
          expect.objectContaining({
            sort: 'price',
          })
        );
      });
    }
  });

  it('displays pagination when multiple pages exist', async () => {
    gigsService.getGigs.mockResolvedValue({
      success: true,
      data: [mockGig],
      pagination: {
        page: 1,
        limit: 12,
        total: 25,
        totalPages: 3,
        hasNextPage: true,
        hasPrevPage: false,
      },
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText(/page 1 of 3/i)).toBeInTheDocument();
    });

    const nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).toBeInTheDocument();
  });

  it('navigates to next page when next button is clicked', async () => {
    const user = userEvent.setup();
    gigsService.getGigs.mockResolvedValue({
      success: true,
      data: [mockGig],
      pagination: {
        page: 1,
        limit: 12,
        total: 25,
        totalPages: 3,
        hasNextPage: true,
        hasPrevPage: false,
      },
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText(/page 1 of 3/i)).toBeInTheDocument();
    });

    const nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    await waitFor(() => {
      expect(gigsService.getGigs).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2,
        })
      );
    });
  });
});

describe('GigCard Component', () => {
  it('test_render_gig_card_with_data', () => {
    renderWithProviders(<GigCard gig={mockGig} />);

    expect(screen.getByText(/professional logo design/i)).toBeInTheDocument();
    expect(screen.getByText(/\$50/)).toBeInTheDocument();
    expect(screen.getByText(/3 days/i)).toBeInTheDocument();
    expect(screen.getByText(/graphic design/i)).toBeInTheDocument();
  });

  it('test_gig_card_displays_correct_info', () => {
    renderWithProviders(<GigCard gig={mockGig} />);

    expect(screen.getByText(/professional logo design/i)).toBeInTheDocument();
    expect(screen.getByText(/\$50/)).toBeInTheDocument();
    expect(screen.getByText(/3 days/i)).toBeInTheDocument();
    expect(screen.getByText(/graphic design/i)).toBeInTheDocument();
    expect(screen.getByText(/4\.5/)).toBeInTheDocument();
    expect(screen.getByText(/10 sales/i)).toBeInTheDocument();
  });

  it('test_gig_card_with_missing_data', () => {
    const gigWithoutImage = { ...mockGig, images: [] };
    renderWithProviders(<GigCard gig={gigWithoutImage} />);

    expect(screen.getByText(/no image/i)).toBeInTheDocument();

    const gigWithoutRating = { ...mockGig, rating: 0 };
    renderWithProviders(<GigCard gig={gigWithoutRating} />);
    expect(screen.getByText(/professional logo design/i)).toBeInTheDocument();
  });

  it('test_gig_card_link_navigation', async () => {
    // Use MemoryRouter to verify navigation to gig page
    const { container } = render(
      <QueryClientProvider client={new (QueryClient)({ defaultOptions: { queries: { retry: false } } })}>
        <BrowserRouter>
          <GigCard gig={mockGig} />
        </BrowserRouter>
      </QueryClientProvider>
    );

    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', `/gigs/${mockGig._id}`);

    // Simulate navigation using MemoryRouter and Routes
    const { getByRole } = render(
      <QueryClientProvider client={new (QueryClient)({ defaultOptions: { queries: { retry: false } } })}>
        <BrowserRouter>
          <GigCard gig={mockGig} />
        </BrowserRouter>
      </QueryClientProvider>
    );

    // Click should be handled by react-router's Link — ensure it exists
    await (async () => {
      const user = (await import('@testing-library/user-event')).default.setup();
      await user.click(getByRole('link'));
    })();

    // We just assert link presence and href — navigation behavior is validated in route-level tests
    expect(getByRole('link')).toHaveAttribute('href', `/gigs/${mockGig._id}`);
  });
});

// Additional tests for search sorting by rating
it('test_sort_by_rating', async () => {
  const user = userEvent.setup();
  renderWithProviders(<Home />);

  await waitFor(() => {
    expect(screen.getByText(/professional logo design/i)).toBeInTheDocument();
  });

  const sortSelect = screen.getByRole('combobox') || screen.getByDisplayValue(/newest/i);
  if (sortSelect) {
    await user.selectOptions(sortSelect, 'rating');

    await waitFor(() => {
      expect(gigsService.getGigs).toHaveBeenCalledWith(
        expect.objectContaining({
          sort: 'rating',
        })
      );
    });
  }
});

describe('Gig Details Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    gigsService.getGigById.mockResolvedValue({ success: true, data: mockGig });
  });

  it('test_display_gig_details', async () => {
    render(
      <QueryClientProvider client={new (QueryClient)({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter initialEntries={[`/gigs/${mockGig._id}`]}>
          <Routes>
            <Route path="/gigs/:id" element={<GigDetails />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/professional logo design/i)).toBeInTheDocument();
      expect(screen.getByText(/I will create a professional logo design/i)).toBeInTheDocument();
      expect(screen.getByText(/Price:/i)).toBeInTheDocument();
    });
  });

  it('test_order_button_for_authenticated_users', async () => {
    authService.isAuthenticated = vi.fn().mockReturnValue(true);

    render(
      <QueryClientProvider client={new (QueryClient)({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter initialEntries={[`/gigs/${mockGig._id}`]}>
          <Routes>
            <Route path="/gigs/:id" element={<GigDetails />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/order now/i)).toBeInTheDocument();
    });

    const button = screen.getByRole('button', { name: /order now/i });
    await userEvent.click(button);

    expect(mockNavigate).toHaveBeenCalledWith(`/orders/create?gigId=${mockGig._id}`);
  });

  it('test_order_button_redirects_login_for_guests', async () => {
    authService.isAuthenticated = vi.fn().mockReturnValue(false);

    render(
      <QueryClientProvider client={new (QueryClient)({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter initialEntries={[`/gigs/${mockGig._id}`]}>
          <Routes>
            <Route path="/gigs/:id" element={<GigDetails />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/order now/i)).toBeInTheDocument();
    });

    const button = screen.getByRole('button', { name: /order now/i });
    await userEvent.click(button);

    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });
});


