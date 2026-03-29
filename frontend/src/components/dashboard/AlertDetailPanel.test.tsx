import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AlertDetailPanel } from './AlertDetailPanel';

describe('AlertDetailPanel', () => {
  it('should render handoff alert panel', () => {
    const { getByText, getByRole } = render(
      <AlertDetailPanel
        isOpen={true}
        onClose={() => {}}
        alertId="test-handoff"
        alertType="handoff"
        severity="warning"
        data={{ unreadCount: 3 }}
      />
    );

    expect(getByText('INTERCEPT REQUIRED')).toBeTruthy();
    expect(getByText('WARNING PRIORITY')).toBeTruthy();
    expect(getByText('3 customer(s)')).toBeTruthy();
  });

  it('should render bot quality alert panel', () => {
    const { getByText } = render(
      <AlertDetailPanel
        isOpen={true}
        onClose={() => {}}
        alertId="test-bot"
        alertType="bot-quality"
        severity="critical"
        data={{
          healthStatus: 'critical',
          avgResponseTimeSeconds: 90,
          fallbackRate: 0.35,
          resolutionRate: 0.65,
        }}
      />
    );

    expect(getByText('NEURAL LINK DEGRADED')).toBeTruthy();
    expect(getByText('CRITICAL PRIORITY')).toBeTruthy();
    expect(getByText('1m 30s')).toBeTruthy();
  });

  it('should render conversion drop alert panel', () => {
    const { getByText } = render(
      <AlertDetailPanel
        isOpen={true}
        onClose={() => {}}
        alertId="test-conversion"
        alertType="conversion-drop"
        severity="warning"
        data={{ firstStageDropoff: 45 }}
      />
    );

    expect(getByText('FUNNEL LEAKAGE')).toBeTruthy();
    expect(getByText('45% drop-off')).toBeTruthy();
  });

  it('should call onClose when close button is clicked', async () => {
    const onClose = vi.fn();
    const { getByLabelText } = render(
      <AlertDetailPanel
        isOpen={true}
        onClose={onClose}
        alertId="test-handoff"
        alertType="handoff"
        severity="warning"
        data={{}}
      />
    );

    const closeButton = getByLabelText('Close panel');
    await userEvent.click(closeButton);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('should call onClose when backdrop is clicked', async () => {
    const onClose = vi.fn();
    const { container } = render(
      <AlertDetailPanel
        isOpen={true}
        onClose={onClose}
        alertId="test-handoff"
        alertType="handoff"
        severity="warning"
        data={{}}
      />
    );

    const backdrop = container.querySelector('[aria-hidden="true"]');
    expect(backdrop).toBeTruthy();

    if (backdrop) {
      await userEvent.click(backdrop);
      expect(onClose).toHaveBeenCalledTimes(1);
    }
  });

  it('should close on Escape key press', async () => {
    const onClose = vi.fn();
    render(
      <AlertDetailPanel
        isOpen={true}
        onClose={onClose}
        alertId="test-handoff"
        alertType="handoff"
        severity="warning"
        data={{}}
      />
    );

    await userEvent.keyboard('{Escape}');

    await waitFor(() => {
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  it('should not render when isOpen is false', () => {
    const { container } = render(
      <AlertDetailPanel
        isOpen={false}
        onClose={() => {}}
        alertId="test-handoff"
        alertType="handoff"
        severity="warning"
        data={{}}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should apply correct severity styles', () => {
    const { rerender } = render(
      <AlertDetailPanel
        isOpen={true}
        onClose={() => {}}
        alertId="test"
        alertType="handoff"
        severity="critical"
        data={{}}
      />
    );

    expect(screen.getByText('CRITICAL PRIORITY')).toBeTruthy();

    rerender(
      <AlertDetailPanel
        isOpen={true}
        onClose={() => {}}
        alertId="test"
        alertType="handoff"
        severity="warning"
        data={{}}
      />
    );

    expect(screen.getByText('WARNING PRIORITY')).toBeTruthy();
  });

  it('should prevent body scroll when open', () => {
    const { rerender } = render(
      <AlertDetailPanel
        isOpen={false}
        onClose={() => {}}
        alertId="test"
        alertType="handoff"
        severity="warning"
        data={{}}
      />
    );

    expect(document.body.style.overflow).toBe('unset');

    rerender(
      <AlertDetailPanel
        isOpen={true}
        onClose={() => {}}
        alertId="test"
        alertType="handoff"
        severity="warning"
        data={{}}
      />
    );

    expect(document.body.style.overflow).toBe('hidden');
  });
});
