/**
 * ConversationHistory Page
 *
 * Displays full conversation history including bot context for handoff conversations.
 * Industrial Technical Dashboard design with terminal aesthetics.
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Bot, User, AlertCircle, CheckCircle, Activity, Send, Clock } from 'lucide-react';
import { conversationsService } from '../services/conversations';
import ContextSidebar from '../components/conversations/ContextSidebar';
import StickyActionBar from '../components/conversations/StickyActionBar';
import ReplyInput from '../components/conversations/ReplyInput';
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

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit',
    hour12: false 
  });
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
      <div className="flex flex-col items-center justify-center h-screen gap-4" style={{ backgroundColor: '#0C0C0C' }}>
        <div className="w-10 h-10 border-2 animate-spin" style={{ borderColor: '#2f2f2f', borderTopColor: '#00FF88' }} />
        <p className="text-[10px] font-bold uppercase tracking-[0.4em]" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
          Deciphering Stream...
        </p>
      </div>
    );
  }

  if (error || !history) {
    return (
      <div className="flex h-screen items-center justify-center p-8" style={{ backgroundColor: '#0C0C0C' }}>
        <div className="p-12 text-center max-w-lg space-y-8" style={{ backgroundColor: '#0A0A0A', border: '1px solid #FF444440' }}>
          <div className="w-16 h-16 flex items-center justify-center mx-auto" style={{ backgroundColor: '#FF444420' }}>
            <AlertCircle size={32} style={{ color: '#FF4444' }} />
          </div>
          <div className="space-y-4">
            <h2 className="text-xl font-bold uppercase tracking-tight" style={{ fontFamily: 'Space Grotesk, sans-serif', color: '#FFFFFF' }}>
              Data Stream Interrupted
            </h2>
            <p className="text-xs uppercase tracking-widest font-bold leading-relaxed" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#FF4444' }}>
              {error || 'Neural link target not found.'}
            </p>
          </div>
          <button
            onClick={handleBack}
            className="px-6 py-3.5 border transition-all"
            style={{
              fontFamily: 'JetBrains Mono, monospace',
              backgroundColor: '#080808',
              borderColor: '#2f2f2f',
              color: '#FFFFFF',
              fontSize: '10px',
              fontWeight: 700,
              letterSpacing: '0.2em',
              borderRadius: 0,
            }}
          >
            Back to Registry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="conversation-history-page" className="flex h-screen" style={{ backgroundColor: '#0C0C0C' }}>
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        {/* Header */}
        <header 
          className="relative z-10 flex items-center justify-between px-8 py-5"
          style={{ backgroundColor: '#0A0A0A', borderBottom: '1px solid #2f2f2f' }}
        >
          <div className="flex items-center gap-6">
            <button
              onClick={handleBack}
              className="w-11 h-11 flex items-center justify-center transition-all duration-300 group"
              style={{ backgroundColor: '#080808', border: '1px solid #2f2f2f' }}
            >
              <ArrowLeft size={18} style={{ color: '#8a8a8a' }} className="group-hover:-translate-x-0.5 transition-transform" />
            </button>
            <div>
              <div className="flex items-center gap-4">
                <h1 
                  className="text-xl font-bold uppercase tracking-tight"
                  style={{ fontFamily: 'Space Grotesk, sans-serif', color: '#FFFFFF' }}
                >
                  Stream Analysis
                </h1>
                <div 
                  className="flex items-center gap-2 px-3 py-1.5"
                  style={{ backgroundColor: '#00FF8810', border: '1px solid #00FF8840' }}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" style={{ backgroundColor: '#00FF88' }} />
                  <span 
                    className="text-[9px] font-bold uppercase tracking-widest"
                    style={{ fontFamily: 'JetBrains Mono, monospace', color: '#00FF88' }}
                  >
                    Live Sync
                  </span>
                </div>
              </div>
              <p 
                className="text-[10px] font-semibold mt-1 uppercase tracking-widest"
                style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}
              >
                ID: <span style={{ color: '#8a8a8a' }}>{history.data.customer.maskedId}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            {history.data.handoff.urgencyLevel && (
              <div 
                className="px-4 py-2 flex items-center gap-3"
                style={{
                  backgroundColor: history.data.handoff.urgencyLevel === 'high' ? '#FF880020' : '#FF880010',
                  border: `1px solid ${history.data.handoff.urgencyLevel === 'high' ? '#FF880040' : '#FF880020'}`,
                }}
              >
                <Activity size={14} style={{ color: '#FF8800' }} className={history.data.handoff.urgencyLevel === 'high' ? 'animate-bounce' : ''} />
                <span 
                  className="text-[10px] font-bold uppercase tracking-widest"
                  style={{ fontFamily: 'JetBrains Mono, monospace', color: '#FF8800' }}
                >
                  {history.data.handoff.urgencyLevel.toUpperCase()} Priority Status
                </span>
              </div>
            )}
          </div>
        </header>

        {/* Success Announcement Overlay */}
        {successMessage && (
          <div className="absolute top-24 left-1/2 -translate-x-1/2 z-30 pointer-events-none">
            <div 
              className="px-6 py-3 flex items-center gap-3 animate-in fade-in zoom-in duration-500"
              style={{ 
                backgroundColor: '#00FF88', 
                boxShadow: '0 10px 40px rgba(0, 255, 136, 0.3)',
              }}
            >
              <CheckCircle size={16} style={{ color: '#0C0C0C' }} />
              <span 
                className="text-[10px] font-bold uppercase tracking-[0.3em]"
                style={{ fontFamily: 'JetBrains Mono, monospace', color: '#0C0C0C' }}
              >
                {successMessage}
              </span>
            </div>
          </div>
        )}

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto px-8 py-8 custom-scrollbar relative z-10" style={{ backgroundColor: '#0C0C0C' }}>
          <div data-testid="message-list" className="max-w-3xl mx-auto space-y-8">
            {messages.map((message, index) => {
              const isCustomer = message.sender === 'customer';
              const isMerchant = message.sender === 'merchant';
              const isBot = message.sender === 'bot';

              return (
                <div
                  key={message.id}
                  data-testid="message-bubble"
                  data-sender={message.sender}
                  className={`flex ${isCustomer ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex flex-col ${isCustomer ? 'items-end' : 'items-start'} max-w-[75%]`}>
                    {/* Sender Label */}
                    <div className="flex items-center gap-3 mb-3">
                      {!isCustomer && (
                        <div 
                          className="w-8 h-8 flex items-center justify-center"
                          style={{ 
                            backgroundColor: '#0A0A0A', 
                            border: '1px solid #2f2f2f',
                            color: isBot ? '#6a6a6a' : '#00FF88'
                          }}
                        >
                          {isBot ? <Bot size={14} /> : <User size={14} />}
                        </div>
                      )}
                      <span 
                        className="text-[9px] font-bold uppercase tracking-[0.3em]"
                        style={{ 
                          fontFamily: 'JetBrains Mono, monospace', 
                          color: isCustomer ? '#6a6a6a' : isBot ? '#6a6a6a' : '#00FF88' 
                        }}
                      >
                        {isCustomer ? 'NEURAL EXTERNAL [CLIENT]' : isBot ? 'AI ASSISTANT' : 'OVERRIDE IDENTITY [YOU]'}
                      </span>
                      {isCustomer && (
                        <div 
                          className="w-8 h-8 flex items-center justify-center"
                          style={{ backgroundColor: '#0A0A0A', border: '1px solid #2f2f2f', color: '#6a6a6a' }}
                        >
                          <User size={14} />
                        </div>
                      )}
                    </div>

                    {/* Message Bubble */}
                    <div
                      className="px-6 py-5 transition-all duration-300"
                      style={{
                        backgroundColor: isCustomer 
                          ? '#0A0A0A' 
                          : isMerchant 
                            ? '#00FF88' 
                            : '#080808',
                        border: isMerchant ? 'none' : '1px solid #2f2f2f',
                        color: isMerchant ? '#0C0C0C' : isCustomer ? '#FFFFFF' : '#8a8a8a',
                      }}
                    >
                      <p 
                        className="text-sm leading-relaxed"
                        style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: isMerchant ? 600 : 500 }}
                      >
                        {message.content}
                      </p>

                      {/* Bot Confidence */}
                      {isBot && message.confidenceScore !== null && message.confidenceScore !== undefined && (
                        <div 
                          className="mt-5 pt-5 flex items-center justify-between gap-6"
                          style={{ borderTop: '1px solid #2f2f2f' }}
                        >
                          <span 
                            className="text-[9px] font-bold uppercase tracking-[0.4em]"
                            style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}
                          >
                            Neural Accuracy
                          </span>
                          <div className="flex items-center gap-3">
                            <div 
                              className="w-24 h-1 overflow-hidden"
                              style={{ backgroundColor: '#1A1A1A' }}
                            >
                              <div 
                                className="h-full transition-all duration-500"
                                style={{ 
                                  backgroundColor: '#00FF8840', 
                                  width: `${Math.round(message.confidenceScore * 100)}%` 
                                }}
                              />
                            </div>
                            <span 
                              className="text-[10px] font-bold"
                              style={{ fontFamily: 'JetBrains Mono, monospace', color: '#00FF88' }}
                            >
                              {formatConfidence(message.confidenceScore)}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Timestamp */}
                    <div className="flex items-center gap-2 mt-2 px-2">
                      <Clock size={10} style={{ color: '#6a6a6a' }} />
                      <span 
                        className="text-[9px] font-semibold uppercase tracking-[0.2em]"
                        style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}
                      >
                        Synced {formatTime(message.createdAt)}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Input Interface */}
        <div 
          className="relative z-20 px-8 py-5"
          style={{ backgroundColor: '#0A0A0A', borderTop: '1px solid #2f2f2f' }}
        >
          <div className="max-w-3xl mx-auto">
            <ReplyInput
              conversationId={history.data.conversationId}
              platform={history.data.platform as 'messenger' | 'widget' | 'preview' | 'facebook'}
              onSend={handleSendReply}
              isLoading={isReplyLoading}
            />
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
