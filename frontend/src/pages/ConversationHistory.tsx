/**
 * ConversationHistory Page - Story 4-8: Conversation History View
 *
 * Displays full conversation history including bot context for handoff conversations.
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Bot, User, AlertCircle } from 'lucide-react';
import { conversationsService } from '../services/conversations';
import ContextSidebar from '../components/conversations/ContextSidebar';
import type { ConversationHistoryResponse } from '../types/conversation';

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

  const backDestination = (location.state as { from?: string })?.from || '/conversations';

  useEffect(() => {
    const fetchHistory = async () => {
      if (!conversationId) return;

      setIsLoading(true);
      setError(null);

      try {
        const response = await conversationsService.getConversationHistory(parseInt(conversationId, 10));
        setHistory(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load conversation history');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, [conversationId]);

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
      <div className="flex-1 flex flex-col overflow-hidden">
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

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          <div data-testid="message-list" className="max-w-2xl mx-auto space-y-4">
            {history.data.messages.map((message) => (
              <div
                key={message.id}
                data-testid="message-bubble"
                data-sender={message.sender}
                className={`flex ${message.sender === 'customer' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-3 ${
                    message.sender === 'customer'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-900'
                  }`}
                >
                  {/* Sender Icon */}
                  <div className="flex items-center gap-2 mb-1">
                    {message.sender === 'bot' ? (
                      <Bot size={14} className="text-gray-600" />
                    ) : (
                      <User size={14} className="text-blue-100" />
                    )}
                    <span
                      className={`text-xs font-medium ${
                        message.sender === 'customer' ? 'text-blue-100' : 'text-gray-500'
                      }`}
                    >
                      {message.sender === 'customer' ? 'Shopper' : 'Bot'}
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
      </div>

      {/* Context Sidebar */}
      <ContextSidebar
        customer={history.data.customer}
        handoff={history.data.handoff}
        context={history.data.context}
      />
    </div>
  );
}
