/**
 * Tests for BudgetAlertConfig Component
 *
 * Story 3-8: Budget Alert Notifications
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';
import { BudgetAlertConfig } from './BudgetAlertConfig';

const mockToast = vi.fn();

vi.mock('../../context/ToastContext', () => ({
  useToast: () => ({ toast: mockToast }),
}));

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('BudgetAlertConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockReset();
  });

  afterEach(() => {
    cleanup();
  });

  it('renders alert configuration UI', () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: { warning_threshold: 80, critical_threshold: 95, enabled: true } }),
    });

    render(<BudgetAlertConfig />);
    expect(screen.getByText('Alert Configuration')).toBeInTheDocument();
  });

  it('loads existing config on mount', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        data: {
          warning_threshold: 75,
          critical_threshold: 90,
          enabled: true,
        },
      }),
    });

    render(<BudgetAlertConfig />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/merchant/alert-config', expect.any(Object));
    });
  });

  it('displays warning threshold value', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: { warning_threshold: 80, critical_threshold: 95, enabled: true } }),
    });

    render(<BudgetAlertConfig />);

    await waitFor(() => {
      expect(screen.getAllByText('80%').length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });

  it('displays critical threshold value', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: { warning_threshold: 80, critical_threshold: 95, enabled: true } }),
    });

    render(<BudgetAlertConfig />);

    await waitFor(() => {
      expect(screen.getAllByText('95%').length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });

  it('toggles alerts enabled state', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: { warning_threshold: 80, critical_threshold: 95, enabled: true } }),
    });

    render(<BudgetAlertConfig />);

    const toggle = screen.getByRole('checkbox', { name: /enable budget alerts/i });
    fireEvent.click(toggle);

    expect(screen.getByText('Disabled')).toBeInTheDocument();
  });

  it('shows warning when critical <= warning', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: { warning_threshold: 80, critical_threshold: 95, enabled: true } }),
    });

    render(<BudgetAlertConfig />);

    const warningSlider = screen.getByLabelText('Warning threshold percentage');
    fireEvent.change(warningSlider, { target: { value: 96 } });

    expect(screen.getByText(/Critical threshold should be higher/i)).toBeInTheDocument();
  });

  it('enables save button when changes made', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: { warning_threshold: 80, critical_threshold: 95, enabled: true } }),
    });

    render(<BudgetAlertConfig />);

    const warningSlider = screen.getByLabelText('Warning threshold percentage');
    fireEvent.change(warningSlider, { target: { value: 85 } });

    const saveButton = screen.getByRole('button', { name: /Save alert configuration/i });
    expect(saveButton).toBeEnabled();
  });

  it('calls save API on save click', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: { warning_threshold: 80, critical_threshold: 95, enabled: true } }),
      })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ data: {} }) });

    render(<BudgetAlertConfig />);

    const warningSlider = screen.getByLabelText('Warning threshold percentage');
    fireEvent.change(warningSlider, { target: { value: 85 } });

    const saveButton = screen.getByRole('button', { name: /Save alert configuration/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/merchant/alert-config',
        expect.objectContaining({ method: 'PUT' })
      );
    });
  });

  it('shows success toast on save', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: { warning_threshold: 80, critical_threshold: 95, enabled: true } }),
      })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ data: {} }) });

    render(<BudgetAlertConfig />);

    const warningSlider = screen.getByLabelText('Warning threshold percentage');
    fireEvent.change(warningSlider, { target: { value: 85 } });

    const saveButton = screen.getByRole('button', { name: /Save alert configuration/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith('Alert settings saved successfully', 'success');
    });
  });

  it('shows error toast on save failure', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: { warning_threshold: 80, critical_threshold: 95, enabled: true } }),
      })
      .mockResolvedValueOnce({ ok: false, json: () => Promise.resolve({ message: 'Error' }) });

    render(<BudgetAlertConfig />);

    const warningSlider = screen.getByLabelText('Warning threshold percentage');
    fireEvent.change(warningSlider, { target: { value: 85 } });

    const saveButton = screen.getByRole('button', { name: /Save alert configuration/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith('Error', 'error');
    });
  });

  it('resets to defaults on reset click', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: { warning_threshold: 75, critical_threshold: 90, enabled: true } }),
    });

    render(<BudgetAlertConfig />);

    await waitFor(() => {
      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    const resetButton = screen.getByRole('button', { name: /Reset to defaults/i });
    fireEvent.click(resetButton);

    expect(screen.getByText('80%')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
  });

  it('shows preview of alert levels', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: { warning_threshold: 80, critical_threshold: 95, enabled: true } }),
    });

    render(<BudgetAlertConfig />);

    await waitFor(() => {
      expect(screen.getByText(/Warning at 80%/)).toBeInTheDocument();
      expect(screen.getByText(/Critical at 95%/)).toBeInTheDocument();
    });
  });

  it('disables controls when alerts disabled', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: { warning_threshold: 80, critical_threshold: 95, enabled: false } }),
    });

    render(<BudgetAlertConfig />);

    await waitFor(() => {
      expect(screen.getByText('Disabled')).toBeInTheDocument();
    });

    const warningSlider = screen.getByLabelText('Warning threshold percentage');
    expect(warningSlider).toBeDisabled();
  });
});
