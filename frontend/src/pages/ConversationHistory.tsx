/**
 * ConversationHistory Page - Story 4-8: Conversation History View
 *
 * Displays full conversation history including bot context for handoff conversations.
 * Story 4-9: Added StickyActionBar for Open in Messenger / Return to Bot functionality.
 * Merchant Reply Feature: Added reply input for Messenger/Widget conversations.
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Bot, User, AlertCircle, CheckCircle, Store } from 'lucide-react';
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
    const fetchData = async () => {
      if (!conversationId) return;

      setIsLoading(true);
      setError(null);

      try {
        const [historyResponse, pageResponse] = await Promise.all([
          conversationsService.getConversationHistory(parseInt(conversationId, 10)),
          conversationsService.getFacebookPageInfo().catch(() => ({ data: { pageId: null, pageName: null, isConnected: false } })),
        ]);
        setHistory(historyResponse);
        setFacebookPage(pageResponse.data);
        setMessages(historyResponse.data.messages);
        
        const conversationData = historyResponse.data as ConversationHistoryResponse['data'] & {
          hybridMode?: HybridModeState;
        };
        if (conversationData.hybridMode) {
          setHybridMode(conversationData.hybridMode);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load conversation history');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
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
        setSuccessMessage("You're now in control! The bot will wait until you return control.");
      } else {
        setSuccessMessage("Bot has resumed normal operation.");
      }
      
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update hybrid mode');
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

      // Add the message to the local list
      const newMessage: MessageHistoryItem = {
        id: response.data.message.id,
        sender: 'merchant',
        content: response.data.message.content,
        createdAt: response.data.message.createdAt,
      };
      setMessages((prev) => [...prev, newMessage]);

      setSuccessMessage('Message sent successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      throw err;
    } finally {
      setIsReplyLoading(false);
    }
  };

  const handleBack = () => {
    navigate(backDestination);
  };

  if (isLoading) {
    return (
      <div data-testid="conversation-history-page" className="flex h-screen bg-gray-100">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-gray-500">Loading conversation...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div data-testid="conversation-history-page" className="flex h-screen bg-gray-100">
        <div className="flex-1 flex flex-col items-center justify-center">
          <AlertCircle className="text-red-500 mb-4" size={48} />
          <div className="text-red-600 mb-4">{error}</div>
          <button
            onClick={handleBack}
            className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
          >
            Back to {backDestination === '/handoff-queue' ? 'Queue' : 'Conversations'}
          </button>
        </div>
      </div>
    );
  }

  if (!history) {
    return (
      <div data-testid="conversation-history-page" className="flex h-screen bg-gray-100">
        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="text-gray-500 mb-4">Conversation not found</div>
          <button
            onClick={handleBack}
            className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
          >
            Back to {backDestination === '/handoff-queue' ? 'Queue' : 'Conversations'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="conversation-history-page" className="flex h-screen bg-gray-100">
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden pb-20">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={handleBack}
              className="p-2 hover:bg-gray-100 rounded-lg"
              aria-label={`Back to ${backDestination === '/handoff-queue' ? 'queue' : 'conversations'}`}
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Conversation History</h1>
              <p className="text-sm text-gray-500">
                Customer: {history.data.customer.maskedId}
              </p>
            </div>
          </div>
        </header>

        {/* Success Message */}
        {successMessage && (
          <div className="mx-6 mt-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
            <CheckCircle className="text-green-600" size={20} />
            <span className="text-green-800 text-sm">{successMessage}</span>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          <div data-testid="message-list" className="max-w-2xl mx-auto space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                data-testid="message-bubble"
                data-sender={message.sender}
                className={`flex ${
                  message.sender === 'customer' 
                    ? 'justify-end' 
                    : message.sender === 'merchant'
                    ? 'justify-start'
                    : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-3 ${
                    message.sender === 'customer'
                      ? 'bg-blue-500 text-white'
                      : message.sender === 'merchant'
                      ? 'bg-green-100 text-gray-900 border border-green-200'
                      : 'bg-gray-200 text-gray-900'
                  }`}
                >
                  {/* Sender Icon */}
                  <div className="flex items-center gap-2 mb-1">
                    {message.sender === 'bot' ? (
                      <Bot size={14} className="text-gray-600" />
                    ) : message.sender === 'merchant' ? (
                      <Store size={14} className="text-green-600" />
                    ) : (
                      <User size={14} className="text-blue-100" />
                    )}
                    <span
                      className={`text-xs font-medium ${
                        message.sender === 'customer' 
                          ? 'text-blue-100' 
                          : message.sender === 'merchant'
                          ? 'text-green-700'
                          : 'text-gray-500'
                      }`}
                    >
                      {message.sender === 'customer' ? 'Shopper' : message.sender === 'merchant' ? 'You' : 'Bot'}
                    </span>
                  </div>

                  {/* Message Content */}
                  <p className="text-sm">{message.content}</p>

                  {/* Confidence Score for Bot Messages */}
                  {message.sender === 'bot' && message.confidenceScore !== null && message.confidenceScore !== undefined && (
                    <div
                      data-testid="confidence-badge"
                      className="mt-2 pt-2 border-t border-gray-300"
                    >
                      <span className="text-xs text-gray-500">
                        Confidence: {formatConfidence(message.confidenceScore)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Reply Input */}
        {history && (
          <ReplyInput
            conversationId={history.data.conversationId}
            platform={history.data.platform as 'messenger' | 'widget' | 'preview' | 'facebook'}
            onSend={handleSendReply}
            isLoading={isReplyLoading}
          />
        )}
      </div>

      {/* Context Sidebar */}
      <ContextSidebar
        customer={history.data.customer}
        handoff={history.data.handoff}
        context={history.data.context}
      />

      {/* Sticky Action Bar - Story 4-9 */}
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
