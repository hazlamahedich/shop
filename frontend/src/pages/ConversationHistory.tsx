/**
 * ConversationHistory Page - Story 4-8: Conversation History View
 *
 * Displays full conversation history including bot context for handoff conversations.
 * Re-imagined with Mantis aesthetic.
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Bot, User, AlertCircle, CheckCircle, Store, ShieldCheck, Activity, Terminal } from 'lucide-react';
import { conversationsService } from '../services/conversations';
import ContextSidebar from '../components/conversations/ContextSidebar';
import StickyActionBar from '../components/conversations/StickyActionBar';
import ReplyInput from '../components/conversations/ReplyInput';
import { GlassCard } from '../components/ui/GlassCard';
import type { 
  ConversationHistoryResponse, 
  HybridModeState, 
  FacebookPageInfo,
  MessageHistoryItem 
} from '../types/conversation';

function formatConfidence(score: number | null | undefined): string {
  if (score === null || score === undefined) return '';
  return `${Math.round(score * 100)}%`;
}

export default function ConversationHistory() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [history, setHistory] = useState<ConversationHistoryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hybridMode, setHybridMode] = useState<HybridModeState | null>(null);
  const [facebookPage, setFacebookPage] = useState<FacebookPageInfo | null>(null);
  const [isHybridModeLoading, setIsHybridModeLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isReplyLoading, setIsReplyLoading] = useState(false);
  const [messages, setMessages] = useState<MessageHistoryItem[]>([]);

  const backDestination = (location.state as { from?: string })?.from || '/conversations';

  useEffect(() => {
    if (!conversationId) return;

    let isMounted = true;

    const fetchData = async (isPolling = false) => {
      if (!isPolling) {
        setIsLoading(true);
        setError(null);
      }

      try {
        const [historyResponse, pageResponse] = await Promise.all([
          conversationsService.getConversationHistory(parseInt(conversationId, 10)),
          conversationsService.getFacebookPageInfo().catch(() => ({ data: { pageId: null, pageName: null, isConnected: false } })),
        ]);

        if (!isMounted) return;

        setHistory(historyResponse);
        setFacebookPage(pageResponse.data);
        setMessages(historyResponse.data.messages);
        
        const conversationData = historyResponse.data as ConversationHistoryResponse['data'] & {
          hybridMode?: HybridModeState;
        };
        if (conversationData.hybridMode) {
          setHybridMode(conversationData.hybridMode);
        } else {
          setHybridMode(null);
        }
      } catch (err) {
        if (!isMounted) return;
        if (!isPolling) {
          setError(err instanceof Error ? err.message : 'Failed to load conversation history');
        } else {
          console.error('Background polling error:', err);
        }
      } finally {
        if (isMounted && !isPolling) {
          setIsLoading(false);
        }
      }
    };

    fetchData();

    const intervalId = setInterval(() => {
      fetchData(true);
    }, 10000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, [conversationId]);

  const handleHybridModeChange = async (enabled: boolean) => {
    if (!conversationId) return;
    
    setIsHybridModeLoading(true);
    setSuccessMessage(null);
    try {
      const response = await conversationsService.setHybridMode(
        parseInt(conversationId, 10),
        { enabled, reason: enabled ? 'merchant_responding' : 'merchant_returning' }
      );
      
      setHybridMode({
        enabled: response.hybridMode.enabled,
        activatedAt: response.hybridMode.activatedAt,
        activatedBy: response.hybridMode.activatedBy,
        expiresAt: response.hybridMode.expiresAt,
        remainingSeconds: response.hybridMode.remainingSeconds,
      });
      
      if (enabled) {
        setSuccessMessage("NEURAL OVERRIDE: Merchant control active.");
      } else {
        setSuccessMessage("NEURAL RESET: Bot assistant resumed.");
      }
      
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Override failed');
    } finally {
      setIsHybridModeLoading(false);
    }
  };

  const handleSendReply = async (content: string) => {
    if (!conversationId || !history) return;

    setIsReplyLoading(true);
    try {
      const response = await conversationsService.sendMerchantReply(
        parseInt(conversationId, 10),
        content
      );

      const newMessage: MessageHistoryItem = {
        id: response.data.message.id,
        sender: 'merchant',
        content: response.data.message.content,
        createdAt: response.data.message.createdAt,
      };
      setMessages((prev) => [...prev, newMessage]);

      setSuccessMessage('Transmission successful.');
      setTimeout(() => setSuccessMessage(null), 3000);
    } finally {
      setIsReplyLoading(false);
    }
  };

  const handleBack = () => {
    navigate(backDestination);
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-[#030303] gap-4">
        <div className="w-12 h-12 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
        <p className="text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.4em]">Deciphering Stream...</p>
      </div>
    );
  }

  if (error || !history) {
    return (
      <div className="flex h-screen bg-[#030303] items-center justify-center p-8">
        <GlassCard accent="error" className="p-12 text-center max-w-lg space-y-8 border-red-500/10">
          <div className="w-20 h-20 bg-red-500/10 border border-red-500/20 rounded-full flex items-center justify-center mx-auto text-red-500">
            <AlertCircle size={40} />
          </div>
          <div className="space-y-4">
            <h2 className="text-xl font-black text-white uppercase tracking-tight">Data Stream Interrupted</h2>
            <p className="text-xs text-red-500/60 font-black uppercase tracking-widest leading-relaxed">
              {error || 'Neural link target not found.'}
            </p>
          </div>
          <button
            onClick={handleBack}
            className="h-14 px-8 bg-white/5 border border-white/10 text-white font-black text-[10px] uppercase tracking-[0.3em] rounded-2xl hover:bg-white/10 hover:border-white/20 transition-all"
          >
            Back to Registry
          </button>
        </GlassCard>
      </div>
    );
  }

  return (
    <div data-testid="conversation-history-page" className="flex h-screen bg-[#030303] animate-in fade-in duration-1000">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden pb-20 relative">
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.15] pointer-events-none mix-blend-overlay"></div>
        <div className="absolute inset-x-0 top-0 h-64 bg-gradient-to-b from-emerald-500/[0.05] to-transparent pointer-events-none"></div>

        {/* Header */}
        <header className="relative z-10 bg-[#0a0a0a]/80 backdrop-blur-3xl border-b border-white/[0.03] px-10 py-6 flex items-center justify-between shadow-2xl">
          <div className="flex items-center gap-8">
            <button
              onClick={handleBack}
              className="w-12 h-12 flex items-center justify-center bg-white/5 hover:bg-emerald-500/10 text-white/40 hover:text-emerald-400 rounded-2xl border border-white/5 hover:border-emerald-500/20 transition-all duration-500 group"
            >
              <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
            </button>
            <div>
              <div className="flex items-center gap-4">
                <h1 className="text-2xl font-black text-white uppercase tracking-tight">Stream Analysis</h1>
                <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span className="text-[10px] font-black text-emerald-400 uppercase tracking-widest">Live Sync</span>
                </div>
              </div>
              <p className="text-[11px] font-black text-emerald-900/40 mt-1 uppercase tracking-widest">
                ID: <span className="text-white/60 font-mono tracking-normal">{history.data.customer.maskedId}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            {history.data.handoff.urgencyLevel && (
              <div className={`px-4 py-2 rounded-xl border text-[10px] font-black uppercase tracking-[0.2em] flex items-center gap-3 ${
                history.data.handoff.urgencyLevel === 'high' 
                  ? 'bg-red-500/5 border-red-500/20 text-red-500 shadow-[0_0_20px_rgba(239,68,68,0.1)]' 
                  : 'bg-amber-500/5 border-amber-500/20 text-amber-500'
              }`}>
                <Activity size={14} className={history.data.handoff.urgencyLevel === 'high' ? 'animate-bounce' : ''} />
                {history.data.handoff.urgencyLevel} Priority Status
              </div>
            )}
          </div>
        </header>

        {/* Success Announcement Overlay */}
        {successMessage && (
          <div className="absolute top-28 left-1/2 -translate-x-1/2 z-30 pointer-events-none">
            <div className="px-8 py-4 bg-emerald-500 text-black font-black text-[11px] uppercase tracking-[0.35em] rounded-2xl shadow-[0_20px_50px_rgba(16,185,129,0.3)] animate-in fade-in zoom-in duration-500 flex items-center gap-4">
              <CheckCircle size={18} />
              {successMessage}
            </div>
          </div>
        )}

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto px-10 py-12 custom-scrollbar relative z-10 scroll-smooth">
          <div data-testid="message-list" className="max-w-4xl mx-auto space-y-12">
            {messages.map((message, index) => {
              const isCustomer = message.sender === 'customer';
              const isMerchant = message.sender === 'merchant';
              const isBot = message.sender === 'bot';

              return (
                <div
                  key={message.id}
                  data-testid="message-bubble"
                  data-sender={message.sender}
                  className={`flex ${isCustomer ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-4`}
                  style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'both' }}
                >
                  <div className={`flex flex-col ${isCustomer ? 'items-end' : 'items-start'} max-w-[80%]`}>
                    {/* Identification Label */}
                    <div className="flex items-center gap-3 mb-4 px-2">
                      {!isCustomer && (
                        <div className={`w-8 h-8 rounded-xl flex items-center justify-center border transition-colors ${
                          isBot ? 'bg-white/5 border-white/10 text-emerald-900/40' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                        }`}>
                          {isBot ? <Bot size={16} /> : <Terminal size={16} />}
                        </div>
                      )}
                      <span className={`text-[10px] font-black uppercase tracking-[0.3em] ${
                        isCustomer ? 'text-emerald-900/40' : isBot ? 'text-emerald-900/40' : 'text-emerald-500'
                      }`}>
                        {isCustomer ? 'Neural External (Client)' : isBot ? 'AI Assistant' : 'Override Identity (You)'}
                      </span>
                      {isCustomer && (
                        <div className="w-8 h-8 rounded-xl bg-white/5 border border-white/10 text-emerald-900/40 flex items-center justify-center">
                          <User size={16} />
                        </div>
                      )}
                    </div>

                    {/* Message Container */}
                    <div
                      className={`relative px-8 py-6 rounded-[32px] border transition-all duration-500 group/message ${
                        isCustomer
                          ? 'bg-white/[0.03] border-white/[0.05] text-white/90 hover:border-emerald-500/20 hover:bg-emerald-500/[0.02]'
                          : isMerchant
                          ? 'bg-emerald-500 text-black border-emerald-500 shadow-[0_10px_40px_rgba(16,185,129,0.2)] font-black'
                          : 'bg-[#0a0a0a] border-white/[0.03] text-white/50'
                      }`}
                    >
                      <p className="text-base leading-relaxed tracking-tight">{message.content}</p>

                      {/* Bot Confidence Array */}
                      {isBot && message.confidenceScore !== null && message.confidenceScore !== undefined && (
                        <div className="mt-6 pt-6 border-t border-white/[0.03] flex items-center justify-between gap-6">
                          <span className="text-[9px] font-black text-emerald-900/20 uppercase tracking-[0.4em]">Neural Accuracy</span>
                          <div className="flex items-center gap-3">
                             <div className="w-24 h-1 bg-white/[0.05] rounded-full overflow-hidden">
                               <div 
                                 className="h-full bg-emerald-500/30 rounded-full" 
                                 style={{ width: `${Math.round(message.confidenceScore * 100)}%` }}
                                ></div>
                             </div>
                             <span className="text-[10px] font-mono font-black text-emerald-500/40">
                               {formatConfidence(message.confidenceScore)}
                             </span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Timestamp */}
                    <span className="mt-3 px-3 text-[9px] font-black text-emerald-900/20 uppercase tracking-[0.2em]">
                      Synced {new Date(message.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Input Interface */}
        <div className="relative z-20 px-10 pb-10">
          <div className="max-w-4xl mx-auto">
            <GlassCard className="p-2 border-emerald-500/10 bg-emerald-500/5 backdrop-blur-3xl rounded-[40px] shadow-2xl overflow-hidden">
              <ReplyInput
                conversationId={history.data.conversationId}
                platform={history.data.platform as 'messenger' | 'widget' | 'preview' | 'facebook'}
                onSend={handleSendReply}
                isLoading={isReplyLoading}
              />
            </GlassCard>
          </div>
        </div>
      </div>

      {/* Analytics Sidebar */}
      <ContextSidebar
        customer={history.data.customer}
        handoff={history.data.handoff}
        context={history.data.context}
      />

      {/* Global Command Bar */}
      <StickyActionBar
        conversationId={history.data.conversationId}
        platformSenderId={history.data.platformSenderId}
        hybridMode={hybridMode}
        facebookPage={facebookPage}
        isLoading={isHybridModeLoading}
        onHybridModeChange={handleHybridModeChange}
      />
    </div>
  );
}
