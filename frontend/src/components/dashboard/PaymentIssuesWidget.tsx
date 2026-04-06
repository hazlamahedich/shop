import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  Clock,
  ShieldAlert,
  CreditCard,
  CheckCircle,
  ChevronRight,
} from 'lucide-react';
import { disputeService, type PaymentIssuesData } from '../../services/disputeService';

function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(value);
}

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

export function PaymentIssuesWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['payment-issues'],
    queryFn: async () => {
      const response = await disputeService.getPaymentIssues();
      return response.data;
    },
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const issues = data as PaymentIssuesData | undefined;
  const openDisputes = issues?.disputes?.open_count ?? 0;
  const pendingDisputes = issues?.disputes?.pending_count ?? 0;
  const totalAtRisk = issues?.disputes?.total_at_risk ?? 0;
  const pendingOrders = issues?.pending_orders?.count ?? 0;
  const totalIssues = openDisputes + pendingDisputes + pendingOrders;

  const hasIssues = totalIssues > 0;

  return (
    <div
      className="relative overflow-hidden glass-card transition-all duration-300 w-full"
      data-testid="payment-issues-widget"
    >
      <div
        className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${
          openDisputes > 0
            ? 'from-rose-500 to-red-600 opacity-80'
            : pendingOrders > 0
              ? 'from-amber-400 to-orange-500 opacity-60'
              : 'from-emerald-400 to-green-500 opacity-40'
        }`}
      />

      <div className="p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-xl border shadow-[0_0_15px_rgba(0,0,0,0.1)] ring-1 ring-white/5 transition-transform hover:rotate-12 ${
                openDisputes > 0
                  ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                  : pendingOrders > 0
                    ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                    : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              }`}
            >
              <ShieldAlert size={18} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white/90 uppercase tracking-widest leading-none">
                Payment Issues
              </h3>
              <p className="text-[10px] font-medium text-white/40 uppercase tracking-tighter mt-1">
                Disputes & unpaid orders
              </p>
            </div>
          </div>
          {hasIssues && (
            <span
              className={`px-2 py-1 rounded-md text-[10px] font-black uppercase tracking-widest ${
                openDisputes > 0
                  ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              }`}
            >
              {totalIssues} {totalIssues === 1 ? 'issue' : 'issues'}
            </span>
          )}
        </div>

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-xl bg-white/5 animate-pulse flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-3/4 rounded bg-white/5 animate-pulse" />
                  <div className="h-3 w-1/4 rounded bg-white/5 animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        ) : isError ? (
          <p className="text-sm text-white/20 text-center py-6 font-medium italic">
            Connection lost. Could not sync payment data.
          </p>
        ) : !hasIssues ? (
          <div className="flex flex-col items-center justify-center py-8 text-center bg-white/[0.02] rounded-2xl border border-white/5">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/20 mb-3 shadow-[0_0_20px_rgba(16,185,129,0.1)]">
              <CheckCircle size={20} className="text-emerald-400" />
            </div>
            <p className="text-[10px] font-bold text-white/30 uppercase tracking-widest">
              All payments clear
            </p>
            <p className="text-[9px] text-white/20 mt-1">
              No disputes or payment issues detected
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {openDisputes > 0 && (
              <div className="bg-rose-500/[0.06] rounded-xl border border-rose-500/10 p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={12} className="text-rose-400" />
                    <span className="text-[10px] font-black uppercase tracking-widest text-rose-300">
                      Open Disputes
                    </span>
                  </div>
                  <span className="text-lg font-black text-rose-400">{openDisputes}</span>
                </div>
                {totalAtRisk > 0 && (
                  <p className="text-[9px] text-rose-300/60 font-medium">
                    {formatCurrency(totalAtRisk)} at risk
                  </p>
                )}
                {issues?.disputes?.recent?.slice(0, 2).map((d) => (
                  <div
                    key={d.id}
                    className="flex items-center justify-between mt-2 pt-2 border-t border-rose-500/10"
                  >
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <span className="text-[9px] text-white/50 font-mono truncate">
                        {d.reason || 'Dispute'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-[9px] font-bold text-rose-300">
                        {formatCurrency(d.amount, d.currency)}
                      </span>
                      {d.evidenceDueBy && (
                        <span className="flex items-center gap-1 text-[8px] text-white/30">
                          <Clock size={7} />
                          {formatRelativeTime(d.evidenceDueBy)}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {pendingDisputes > 0 && (
              <div className="bg-yellow-400/[0.06] rounded-xl border border-yellow-400/10 p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ShieldAlert size={12} className="text-yellow-400" />
                    <span className="text-[10px] font-black uppercase tracking-widest text-yellow-300">
                      Pending Inquiry
                    </span>
                  </div>
                  <span className="text-lg font-black text-yellow-400">{pendingDisputes}</span>
                </div>
              </div>
            )}

            {pendingOrders > 0 && (
              <div className="bg-amber-500/[0.06] rounded-xl border border-amber-500/10 p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CreditCard size={12} className="text-amber-400" />
                    <span className="text-[10px] font-black uppercase tracking-widest text-amber-300">
                      Unpaid Orders
                    </span>
                  </div>
                  <span className="text-lg font-black text-amber-400">{pendingOrders}</span>
                </div>
                {issues?.pending_orders?.recent?.slice(0, 2).map((o) => (
                  <div
                    key={o.id}
                    className="flex items-center justify-between mt-2 pt-2 border-t border-amber-500/10"
                  >
                    <span className="text-[9px] text-white/50 font-mono truncate">
                      {o.orderName || o.shopifyOrderId}
                    </span>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {o.totalPrice != null && (
                        <span className="text-[9px] font-bold text-amber-300">
                          {formatCurrency(o.totalPrice, o.currency)}
                        </span>
                      )}
                      <span className="flex items-center gap-1 text-[8px] text-white/30">
                        <Clock size={7} />
                        {formatRelativeTime(o.createdAt)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {hasIssues && (
              <div className="flex items-center justify-center gap-1 pt-2">
                <ChevronRight size={10} className="text-white/20" />
                <span className="text-[8px] font-bold text-white/20 uppercase tracking-widest">
                  View in Shopify for details
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default PaymentIssuesWidget;
