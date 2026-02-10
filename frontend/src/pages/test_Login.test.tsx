/**
 * Tests for Login Page
 *
 * Story 1.8: Tests for login form, validation, and error handling.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Login from './Login';
import { useAuthStore } from '../stores/authStore';

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
}));

// Mock auth store
vi.mock('../stores/authStore', () => ({
  useAuthStore: vi.fn(),
  initializeAuth: vi.fn(),
}));

describe('Login Page', () => {
  const mockNavigate = vi.fn();
  const mockLogin = vi.fn();
  const mockClearError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(require('react-router-dom').useNavigate).mockReturnValue(mockNavigate);

    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      error: null,
      merchant: null,
      sessionExpiresAt: null,
      login: mockLogin,
      logout: vi.fn(),
      fetchMe: vi.fn(),
      refreshSession: vi.fn(),
      clearError: mockClearError,
      reset: vi.fn(),
      _startRefreshTimer: vi.fn(),
      _stopRefreshTimer: vi.fn(),
      _broadcastChannel: null,
    });
  });

  describe('rendering', () => {
    it('should render login form', () => {
      render(<Login />);

      expect(screen.getByLabelText('Email address')).toBeInTheDocument();
      expect(screen.getByLabelText('Password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
    });

    it('should show security notice', () => {
      render(<Login />);

      expect(screen.getByText(/Security Notice/)).toBeInTheDocument();
      expect(screen.getByText(/5 attempts per 15 minutes/)).toBeInTheDocument();
    });

    it('should show loading state when logging in', async () => {
      mockLogin.mockImplementation(() => new Promise(() => {})); // Never resolves

      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        error: null,
        merchant: null,
        sessionExpiresAt: null,
        login: mockLogin,
        logout: vi.fn(),
        fetchMe: vi.fn(),
        refreshSession: vi.fn(),
        clearError: mockClearError,
        reset: vi.fn(),
        _startRefreshTimer: vi.fn(),
        _stopRefreshTimer: vi.fn(),
        _broadcastChannel: null,
      });

      render(<Login />);

      expect(screen.getByText(/Signing in/)).toBeInTheDocument();
    });
  });

  describe('form validation', () => {
    it('should show error when submitting empty form', async () => {
      const user = userEvent.setup();
      render(<Login />);

      const submitButton = screen.getByRole('button', { name: 'Sign in' });
      await user.click(submitButton);

      expect(screen.getByText('Please enter both email and password')).toBeInTheDocument();
    });

    it('should show error for invalid email format', async () => {
      const user = userEvent.setup();
      render(<Login />);

      const emailInput = screen.getByLabelText('Email address');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign in' });

      await user.type(emailInput, 'notanemail');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    });

    it('should show error for short password', async () => {
      const user = userEvent.setup();
      render(<Login />);

      const emailInput = screen.getByLabelText('Email address');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign in' });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'short');
      await user.click(submitButton);

      expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument();
    });
  });

  describe('login flow', () => {
    it('should call login with correct credentials', async () => {
      const user = userEvent.setup();
      mockLogin.mockResolvedValueOnce(undefined);

      render(<Login />);

      const emailInput = screen.getByLabelText('Email address');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign in' });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
        });
      });
    });

    it('should navigate to dashboard on successful login', async () => {
      const user = userEvent.setup();
      mockLogin.mockResolvedValueOnce(undefined);

      render(<Login />);

      const emailInput = screen.getByLabelText('Email address');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign in' });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
      });
    });

    it('should display error message from store', async () => {
      const user = userEvent.setup();
      const mockError = new Error('Invalid email or password');
      (mockError as any).code = 2001;
      mockLogin.mockRejectedValueOnce(mockError);

      render(<Login />);

      const emailInput = screen.getByLabelText('Email address');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign in' });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'wrongpassword');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Invalid email or password')).toBeInTheDocument();
      });
    });

    it('should show specific message for rate limiting', async () => {
      const user = userEvent.setup();
      const mockError = new Error('Too many login attempts');
      (mockError as any).code = 2011;
      mockLogin.mockRejectedValueOnce(mockError);

      render(<Login />);

      const emailInput = screen.getByLabelText('Email address');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign in' });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Too many login attempts. Please try again later.')).toBeInTheDocument();
      });
    });
  });

  describe('error clearing', () => {
    it('should clear error when user types in email field', async () => {
      const user = userEvent.setup();
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: 'Previous error',
        merchant: null,
        sessionExpiresAt: null,
        login: mockLogin,
        logout: vi.fn(),
        fetchMe: vi.fn(),
        refreshSession: vi.fn(),
        clearError: mockClearError,
        reset: vi.fn(),
        _startRefreshTimer: vi.fn(),
        _stopRefreshTimer: vi.fn(),
        _broadcastChannel: null,
      });

      render(<Login />);

      const emailInput = screen.getByLabelText('Email address');
      await user.type(emailInput, 't');

      expect(mockClearError).toHaveBeenCalled();
    });

    it('should clear error when user types in password field', async () => {
      const user = userEvent.setup();
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: 'Previous error',
        merchant: null,
        sessionExpiresAt: null,
        login: mockLogin,
        logout: vi.fn(),
        fetchMe: vi.fn(),
        refreshSession: vi.fn(),
        clearError: mockClearError,
        reset: vi.fn(),
        _startRefreshTimer: vi.fn(),
        _stopRefreshTimer: vi.fn(),
        _broadcastChannel: null,
      });

      render(<Login />);

      const passwordInput = screen.getByLabelText('Password');
      await user.type(passwordInput, 'p');

      expect(mockClearError).toHaveBeenCalled();
    });
  });

  describe('redirect when authenticated', () => {
    it('should redirect to dashboard if already authenticated', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        error: null,
        merchant: { id: 1, email: 'test@example.com', merchant_key: 'abc123' },
        sessionExpiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        login: mockLogin,
        logout: vi.fn(),
        fetchMe: vi.fn(),
        refreshSession: vi.fn(),
        clearError: mockClearError,
        reset: vi.fn(),
        _startRefreshTimer: vi.fn(),
        _stopRefreshTimer: vi.fn(),
        _broadcastChannel: null,
      });

      render(<Login />);

      // Should trigger navigate effect
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
    });
  });
});
