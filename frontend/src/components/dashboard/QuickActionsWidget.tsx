import { useQuery } from '@tanstack/react-query';
import { Plus, Upload, FileText, RefreshCw, Zap, BookOpen, AlertCircle } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: 'add_faq' | 'upload_document' | 'update_document' | 're_embed' | 'test_rag';
  actionUrl: string;
  priority: 'high' | 'medium' | 'low';
  estimatedTime?: string;
}

export function QuickActionsWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'quick-actions'],
    queryFn: () => analyticsService.getQuickActions(),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  });

  const actions = data as QuickAction[] | undefined;

  const getIcon = (icon: QuickAction['icon']) => {
    switch (icon) {
      case 'add_faq':
        return <Plus size={18} />;
      case 'upload_document':
        return <Upload size={18} />;
      case 'update_document':
        return <FileText size={18} />;
      case 're_embed':
        return <RefreshCw size={18} />;
      case 'test_rag':
        return <Zap size={18} />;
      default:
        return <AlertCircle size={18} />;
    }
  };

  const getIconClass = (icon: QuickAction['icon']) => {
    switch (icon) {
      case 'add_faq':
        return 'text-purple-400';
      case 'upload_document':
        return 'text-[#00f5d4]';
      case 'update_document':
        return 'text-orange-400';
      case 're_embed':
        return 'text-blue-400';
      case 'test_rag':
        return 'text-pink-400';
      default:
        return 'text-white/60';
    }
  };

  const getButtonClass = (icon: QuickAction['icon']) => {
    switch (icon) {
      case 'add_faq':
        return 'bg-purple-400/10 border-purple-400/20 hover:bg-purple-400/20 text-purple-400';
      case 'upload_document':
        return 'bg-[#00f5d4]/10 border-[#00f5d4]/20 hover:bg-[#00f5d4]/20 text-[#00f5d4]';
      case 'update_document':
        return 'bg-orange-400/10 border-orange-400/20 hover:bg-orange-400/20 text-orange-400';
      case 're_embed':
        return 'bg-blue-400/10 border-blue-400/20 hover:bg-blue-400/20 text-blue-400';
      case 'test_rag':
        return 'bg-pink-400/10 border-pink-400/20 hover:bg-pink-400/20 text-pink-400';
      default:
        return 'bg-white/5 border-white/10 hover:bg-white/10 text-white/60';
    }
  };

  return (
    <StatCard
      title="Quick Actions"
      value={isLoading ? '...' : `${actions?.length || 0}`}
      subValue="AVAILABLE_ACTIONS"
      icon={<Zap size={18} />}
      accentColor="mantis"
      isLoading={isLoading}
      expandable
    >
      <div className="space-y-4 mt-4">
        {isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">Actions Unavailable</p>
          </div>
        ) : !actions || actions.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-white/30 uppercase tracking-widest">No actions needed</p>
          </div>
        ) : (
          <>
            {/* Priority Actions */}
            {actions.filter((a) => a.priority === 'high').length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle size={12} className="text-rose-400" />
                  <p className="text-[9px] font-black text-white/20 uppercase tracking-widest">Priority Actions</p>
                </div>
                <div className="space-y-2">
                  {actions
                    .filter((a) => a.priority === 'high')
                    .map((action) => (
                      <button
                        key={action.id}
                        className={`w-full flex items-center gap-3 p-3 rounded-xl border transition-all ${getButtonClass(
                          action.icon
                        )} group hover:scale-[1.02]`}
                        onClick={() => {
                          // Navigate to action URL
                          if (action.actionUrl) {
                            window.location.href = action.actionUrl;
                          }
                        }}
                      >
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-white/5 ${getIconClass(
                          action.icon
                        )} group-hover:scale-110 transition-transform`}>
                          {getIcon(action.icon)}
                        </div>
                        <div className="flex-1 text-left">
                          <p className="text-[10px] font-bold uppercase tracking-wider">{action.title}</p>
                          <p className="text-[8px] text-white/60 mt-0.5">{action.description}</p>
                        </div>
                        {action.estimatedTime && (
                          <div className="text-right">
                            <p className="text-[8px] text-white/30 uppercase tracking-wider">Est. Time</p>
                            <p className="text-[9px] font-black">{action.estimatedTime}</p>
                          </div>
                        )}
                      </button>
                    ))}
                </div>
              </div>
            )}

            {/* Regular Actions */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 mb-2">
                <BookOpen size={12} className="text-white/40" />
                <p className="text-[9px] font-black text-white/20 uppercase tracking-widest">
                  All Actions
                </p>
              </div>
              <div className="grid grid-cols-1 gap-2">
                {actions.map((action) => (
                  <button
                    key={action.id}
                    className={`flex items-center gap-3 p-2 rounded-lg border transition-all ${getButtonClass(
                      action.icon
                    )} hover:scale-[1.01]`}
                    onClick={() => {
                      if (action.actionUrl) {
                        window.location.href = action.actionUrl;
                      }
                    }}
                  >
                    <div className={`w-8 h-8 rounded flex items-center justify-center bg-white/5 ${getIconClass(
                      action.icon
                    )}`}>
                      {getIcon(action.icon)}
                    </div>
                    <div className="flex-1 text-left">
                      <p className="text-[9px] font-semibold">{action.title}</p>
                      <p className="text-[8px] text-white/50 truncate">{action.description}</p>
                    </div>
                    {action.priority === 'high' && (
                      <span className="px-2 py-0.5 bg-rose-400/20 text-rose-400 rounded text-[8px] font-black uppercase tracking-wider">
                        High
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Common Tasks */}
            <div className="pt-2 border-t border-white/5">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[9px] font-black text-white/20 uppercase tracking-widest">Common Tasks</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  className="flex flex-col items-center gap-2 p-3 bg-white/5 border border-white/5 rounded-lg hover:bg-white/10 transition-all group"
                  onClick={() => (window.location.href = '/business-info-faq')}
                >
                  <Plus size={16} className="text-purple-400 group-hover:scale-110 transition-transform" />
                  <span className="text-[8px] font-black text-white/60 uppercase tracking-wider">Add FAQ</span>
                </button>
                <button
                  className="flex flex-col items-center gap-2 p-3 bg-white/5 border border-white/5 rounded-lg hover:bg-white/10 transition-all group"
                  onClick={() => (window.location.href = '/business-info-faq#knowledge')}
                >
                  <Upload size={16} className="text-[#00f5d4] group-hover:scale-110 transition-transform" />
                  <span className="text-[8px] font-black text-white/60 uppercase tracking-wider">Upload Doc</span>
                </button>
                <button
                  className="flex flex-col items-center gap-2 p-3 bg-white/5 border border-white/5 rounded-lg hover:bg-white/10 transition-all group"
                  onClick={() => (window.location.href = '/bot-preview')}
                >
                  <Zap size={16} className="text-pink-400 group-hover:scale-110 transition-transform" />
                  <span className="text-[8px] font-black text-white/60 uppercase tracking-wider">Test RAG</span>
                </button>
                <button
                  className="flex flex-col items-center gap-2 p-3 bg-white/5 border border-white/5 rounded-lg hover:bg-white/10 transition-all group"
                  onClick={() => {
                    // Trigger re-embed API call
                    fetch('/api/knowledge-base/re-embed', { method: 'POST' })
                      .then(() => alert('Re-embedding started!'))
                      .catch(() => alert('Failed to start re-embedding'));
                  }}
                >
                  <RefreshCw size={16} className="text-blue-400 group-hover:scale-110 transition-transform" />
                  <span className="text-[8px] font-black text-white/60 uppercase tracking-wider">Re-embed</span>
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </StatCard>
  );
}

export default QuickActionsWidget;
