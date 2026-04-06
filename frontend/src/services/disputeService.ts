import { apiClient } from './api';

export interface Dispute {
  id: number;
  shopifyDisputeId: string;
  amount: number;
  currency: string;
  reason: string | null;
  status: string;
  evidenceDueBy: string | null;
  createdAt: string;
  updatedAt: string;
  orderId: number | null;
}

export interface DisputeSummary {
  open: { count: number; total_amount: number };
  won: { count: number; total_amount: number };
  lost: { count: number; total_amount: number };
  pending: { count: number; total_amount: number };
  total_count: number;
  total_at_risk: number;
}

export interface PendingOrderItem {
  id: number;
  shopifyOrderId: string;
  orderName: string | null;
  totalPrice: number | null;
  currency: string;
  paymentMethod: string | null;
  createdAt: string;
}

export interface PaymentIssuesData {
  disputes: {
    open_count: number;
    pending_count: number;
    lost_count: number;
    total_at_risk: number;
    recent: Dispute[];
  };
  pending_orders: {
    count: number;
    recent: PendingOrderItem[];
  };
}

export const disputeService = {
  async getDisputes(
    status?: string,
    limit = 20,
    offset = 0,
  ) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', String(limit));
    params.append('offset', String(offset));
    return apiClient.get<Dispute[]>(`/api/v1/disputes?${params.toString()}`);
  },

  async getDisputeSummary() {
    return apiClient.get<DisputeSummary>('/api/v1/disputes/summary');
  },

  async getPaymentIssues() {
    return apiClient.get<PaymentIssuesData>('/api/v1/disputes/payment-issues');
  },
};
