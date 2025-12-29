import React from 'react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, beforeAll, afterAll, afterEach } from 'vitest';

import Login from '../pages/Login';
import Register from '../pages/Register';
import authService from '../services/authService';
import * as router from 'react-router-dom';

// Mock API base
const API_BASE = 'http://localhost:3000/api';

const server = setupServer(
  rest.post(`${API_BASE}/users/login`, (req, res, ctx) => {
    const { email, password } = req.body;
    if (email === 'valid@example.com' && password === 'password123') {
      return res(
        ctx.status(200),
        ctx.json({
          success: true,
          data: { token: 'mock-token', user: { id: '1', email } }
        })
      );
    }

    return res(ctx.status(401), ctx.json({ message: 'Invalid credentials' }));
  }),

  rest.post(`${API_BASE}/users/register`, (req, res, ctx) => {
    const { email } = req.body;
    if (email === 'existing@example.com') {
      return res(ctx.status(400), ctx.json({ message: 'User with this email already exists' }));
    }

    return res(ctx.status(201), ctx.json({ success: true, data: { token: 'reg-token', user: { id: '2', email } } }));
  })
);

beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  vi.clearAllMocks();
  // Clear mocked localStorage methods
  global.localStorage.getItem.mockReset();
  global.localStorage.setItem.mockReset();
  global.localStorage.removeItem.mockReset();
});
afterAll(() => server.close());

// Mock useNavigate
const mockNavigate = vi.fn();
vi.spyOn(router, 'useNavigate').mockReturnValue(mockNavigate);

describe('Auth: Login Component', () => {
  it('test_render_login_form', () => {
    render(<Login />);

    expect(screen.getByPlaceholderText(/Email address/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeInTheDocument();
  });

  it('test_login_with_valid_credentials', async () => {
    render(<Login />);

    await userEvent.type(screen.getByPlaceholderText(/Email address/i), 'valid@example.com');
    await userEvent.type(screen.getByPlaceholderText(/Password/i), 'password123');

    await userEvent.click(screen.getByRole('button', { name: /Sign in/i }));

    await waitFor(() => {
      // authService should store token and user
      expect(global.localStorage.setItem).toHaveBeenCalledWith('token', 'mock-token');
      expect(global.localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify({ id: '1', email: 'valid@example.com' }));
      // navigate should be called
      expect(mockNavigate).toHaveBeenCalledWith('/');
      // window reload called
      expect(window.location.reload).toHaveBeenCalled();
    });
  });

  it('test_login_with_invalid_credentials', async () => {
    render(<Login />);

    await userEvent.type(screen.getByPlaceholderText(/Email address/i), 'bad@example.com');
    await userEvent.type(screen.getByPlaceholderText(/Password/i), 'wrongpass');

    await userEvent.click(screen.getByRole('button', { name: /Sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/Login failed|Invalid credentials/i)).toBeInTheDocument();
    });
  });

  it('test_validation_errors_display', async () => {
    render(<Login />);

    // Submit empty form
    await userEvent.click(screen.getByRole('button', { name: /Sign in/i }));

    expect(await screen.findByText(/Email is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/Password is required/i)).toBeInTheDocument();
  });

  it('test_loading_state_during_login', async () => {
    // Delay response to observe loading state
    server.use(
      rest.post(`${API_BASE}/users/login`, (req, res, ctx) => {
        return res(ctx.delay(200), ctx.status(200), ctx.json({ success: true, data: { token: 'delayed-token', user: { id: '9', email: 'delayed@example.com' } } }));
      })
    );

    render(<Login />);

    await userEvent.type(screen.getByPlaceholderText(/Email address/i), 'valid@example.com');
    await userEvent.type(screen.getByPlaceholderText(/Password/i), 'password123');

    await userEvent.click(screen.getByRole('button', { name: /Sign in/i }));

    // Button shows loading
    expect(screen.getByRole('button', { name: /Signing in.../i })).toBeDisabled();

    await waitFor(() => expect(global.localStorage.setItem).toHaveBeenCalled());
  });
});

describe('Auth: Register Component', () => {
  it('test_render_register_form', () => {
    render(<Register />);

    expect(screen.getByPlaceholderText(/Choose a username/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Email address/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/^Password$/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Create account/i })).toBeInTheDocument();
  });

  it('test_register_with_valid_data', async () => {
    render(<Register />);

    await userEvent.type(screen.getByPlaceholderText(/Choose a username/i), 'newuser');
    await userEvent.type(screen.getByPlaceholderText(/Email address/i), 'new@example.com');
    await userEvent.type(screen.getByPlaceholderText(/^Password$/i), 'password123');
    await userEvent.type(screen.getByPlaceholderText(/Confirm password/i), 'password123');

    await userEvent.click(screen.getByRole('button', { name: /Create account/i }));

    await waitFor(() => {
      expect(global.localStorage.setItem).toHaveBeenCalledWith('token', 'reg-token');
      expect(global.localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify({ id: '2', email: 'new@example.com' }));
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });
  });

  it('test_register_with_existing_email', async () => {
    render(<Register />);

    await userEvent.type(screen.getByPlaceholderText(/Choose a username/i), 'exists');
    await userEvent.type(screen.getByPlaceholderText(/Email address/i), 'existing@example.com');
    await userEvent.type(screen.getByPlaceholderText(/^Password$/i), 'password123');
    await userEvent.type(screen.getByPlaceholderText(/Confirm password/i), 'password123');

    await userEvent.click(screen.getByRole('button', { name: /Create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/already exists/i)).toBeInTheDocument();
    });
  });

  it('test_password_confirmation_validation', async () => {
    render(<Register />);

    await userEvent.type(screen.getByPlaceholderText(/Choose a username/i), 'newuser');
    await userEvent.type(screen.getByPlaceholderText(/Email address/i), 'new2@example.com');
    await userEvent.type(screen.getByPlaceholderText(/^Password$/i), 'password123');
    await userEvent.type(screen.getByPlaceholderText(/Confirm password/i), 'different');

    await userEvent.click(screen.getByRole('button', { name: /Create account/i }));

    expect(await screen.findByText(/Passwords do not match/i)).toBeInTheDocument();
  });

  it('test_field_validation_messages', async () => {
    render(<Register />);

    await userEvent.click(screen.getByRole('button', { name: /Create account/i }));

    expect(await screen.findByText(/Username is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/Email is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/Password is required/i)).toBeInTheDocument();
  });
});

describe('Auth Flow', () => {
  it('test_redirect_after_login', async () => {
    render(<Login />);

    await userEvent.type(screen.getByPlaceholderText(/Email address/i), 'valid@example.com');
    await userEvent.type(screen.getByPlaceholderText(/Password/i), 'password123');

    await userEvent.click(screen.getByRole('button', { name: /Sign in/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/');
      expect(window.location.reload).toHaveBeenCalled();
    });
  });

  it('test_persist_user_session', async () => {
    render(<Login />);

    await userEvent.type(screen.getByPlaceholderText(/Email address/i), 'valid@example.com');
    await userEvent.type(screen.getByPlaceholderText(/Password/i), 'password123');

    await userEvent.click(screen.getByRole('button', { name: /Sign in/i }));

    await waitFor(() => {
      expect(authService.getCurrentUser()).toEqual({ id: '1', email: 'valid@example.com' });
      expect(authService.isAuthenticated()).toBeTruthy();
    });
  });

  it('test_logout_clears_session', () => {
    // Simulate logged-in state
    global.localStorage.getItem.mockImplementation((key) => {
      if (key === 'token') return 't';
      if (key === 'user') return JSON.stringify({ id: '1' });
      return null;
    });

    authService.logout();

    expect(global.localStorage.removeItem).toHaveBeenCalledWith('token');
    expect(global.localStorage.removeItem).toHaveBeenCalledWith('user');
    expect(window.location.href).toContain('/login');
  });
});
