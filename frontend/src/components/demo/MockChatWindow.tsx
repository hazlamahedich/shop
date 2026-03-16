/**
 * Mock Chat Window Component
 * Interactive chat interface for demoing general mode widgets
 */

import * as React from 'react';
import { styles } from './styles';
import {
  mockSources,
  mockFAQs,
  mockSuggestedReplies,
  mockContactOptions,
  mockConversations,
  mockFeedbackStats,
} from './mockData';

type FeatureId = 'sources' | 'faq' | 'replies' | 'feedback' | 'contact';

interface MockChatWindowProps {
  feature: FeatureId;
  theme: 'light' | 'dark' | 'auto';
}

export function MockChatWindow({ feature, theme }: MockChatWindowProps) {
  const [messages, setMessages] = React.useState(mockConversations[feature] || []);
  const [inputValue, setInputValue] = React.useState('');
  const [expandedSource, setExpandedSource] = React.useState<string | null>(null);
  const [feedbackGiven, setFeedbackGiven] = React.useState<'positive' | 'negative' | null>(null);
  const [feedbackCounts, setFeedbackCounts] = React.useState(mockFeedbackStats);
  const [toast, setToast] = React.useState<string | null>(null);
  const [isTyping, setIsTyping] = React.useState(false);

  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Reset state when feature changes
  React.useEffect(() => {
    setMessages(mockConversations[feature] || []);
    setExpandedSource(null);
    setFeedbackGiven(null);
    setFeedbackCounts(mockFeedbackStats);
    setInputValue('');
  }, [feature]);

  const showToast = (message: string) => {
    setToast(message);
    setTimeout(() => setToast(null), 2000);
  };

  const handleSend = () => {
    if (!inputValue.trim()) return;
    
    const userMessage = { sender: 'bot' as const, text: inputValue };
    setMessages(prev => [...prev, { sender: 'user' as const, text: inputValue }]);
    setInputValue('');
    
    // Simulate bot typing
    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      if (feature === 'sources') {
        setMessages(prev => [...prev, {
          sender: 'bot',
          text: 'Let me look that up for you...',
          sources: mockSources,
        }]);
      } else {
        setMessages(prev => [...prev, {
          sender: 'bot',
          text: 'Thanks for your question! I\'ll help you with that.',
          suggestedReplies: mockSuggestedReplies,
          showFeedback: true,
        }]);
      }
    }, 1000);
  };

  const handleFAQClick = (faq: typeof mockFAQs[0]) => {
    setMessages(prev => [...prev, { sender: 'user' as const, text: faq.question }]);
    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      setMessages(prev => [...prev, {
        sender: 'bot' as const,
        text: faq.answer,
        showFeedback: true,
        suggestedReplies: ['Tell me more', 'Contact support'],
      }]);
    }, 800);
  };

  const handleReplyClick = (reply: string) => {
    setMessages(prev => [...prev, { sender: 'user' as const, text: reply }]);
    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      setMessages(prev => [...prev, {
        sender: 'bot' as const,
        text: 'I\'m happy to help with that! Let me find the information for you.',
        showFeedback: true,
      }]);
    }, 600);
  };

  const handleFeedback = (type: 'positive' | 'negative') => {
    setFeedbackGiven(type);
    if (type === 'positive') {
      setFeedbackCounts(prev => ({ ...prev, positive: prev.positive + 1 }));
    } else {
      setFeedbackCounts(prev => ({ ...prev, negative: prev.negative + 1 }));
    }
    showToast('Thanks for your feedback!');
  };

  const handleContactClick = (type: string) => {
    showToast(`Opening ${type}...`);
  };

  // Get theme colors
  const getThemeStyles = () => {
    const isDark = theme === 'dark';
    return {
      bg: isDark ? '#0f172a' : '#ffffff',
      text: isDark ? '#f1f5f9' : '#1f2937',
      muted: isDark ? '#94a3b8' : '#6b7280',
      surface: isDark ? '#1e293b' : '#f3f4f6',
      border: isDark ? '#334155' : '#e5e7eb',
    };
  };

  const themeStyles = getThemeStyles();

  return (
    <div style={{ ...styles.chatWindow, backgroundColor: themeStyles.bg, color: themeStyles.text }}>
      {/* Header */}
      <div style={{ ...styles.chatHeader, borderBottomColor: themeStyles.border }}>
        <div style={styles.chatTitle}>
          <span>🤖</span>
          <span>Support Assistant</span>
          <span style={{ fontSize: '10px', padding: '2px 6px', backgroundColor: '#dcfce7', color: '#166534', borderRadius: '4px' }}>Demo</span>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: themeStyles.muted }}>
            {theme === 'dark' ? '🌙' : '☀️'}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div style={{ ...styles.chatMessages, backgroundColor: themeStyles.surface }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            ...styles.message,
            ...(msg.sender === 'user' ? styles.messageUser : styles.messageBot),
          }}>
            {msg.sender === 'bot' && (
              <div style={styles.botName}>Support Assistant</div>
            )}
            <div style={{
              ...styles.messageBubble,
              ...(msg.sender === 'user' ? { ...styles.messageBubbleUser, backgroundColor: '#6366f1' } : { ...styles.messageBubbleBot, backgroundColor: themeStyles.bg }),
            }}>
              {msg.text}
            </div>
            
            {/* Widgets */}
            {msg.sender === 'bot' && (
              <div style={styles.widgetContainer}>
                {/* Source Citations */}
                {msg.sources && <SourceCitations sources={msg.sources} expandedSource={expandedSource} setExpandedSource={setExpandedSource} />}
                
                {/* FAQ Chips */}
                {msg.faqs && <FAQChips faqs={msg.faqs} onFAQClick={handleFAQClick} />}
                
                {/* Quick Reply Chips */}
                {msg.suggestedReplies && <QuickReplyChips replies={msg.suggestedReplies} onReplyClick={handleReplyClick} />}
                
                {/* Feedback Buttons */}
                {msg.showFeedback && (
                  <FeedbackButtons
                    feedbackGiven={feedbackGiven}
                    feedbackCounts={feedbackCounts}
                    onFeedback={handleFeedback}
                  />
                )}
                
                {/* Contact Card */}
                {msg.contactOptions && (
                  <ContactCard options={msg.contactOptions} onContactClick={handleContactClick} />
                )}
              </div>
            )}
            
            <div style={{ ...styles.messageTime, color: themeStyles.muted }}>
              Just now
            </div>
          </div>
        ))}
        
        {/* Typing indicator */}
        {isTyping && (
          <div style={styles.messageBot}>
            <div style={{ ...styles.messageBubble, ...styles.messageBubbleBot, backgroundColor: themeStyles.bg }}>
              <span style={{ animation: 'pulse 1s infinite' }}>Typing...</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{ ...styles.chatInput, borderTopColor: themeStyles.border, backgroundColor: themeStyles.bg }}>
        <input
          type="text"
          placeholder="Type a message..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          style={{ ...styles.input, backgroundColor: themeStyles.surface, borderColor: themeStyles.border, color: themeStyles.text }}
        />
        <button onClick={handleSend} style={styles.sendButton}>
          Send
        </button>
      </div>

      {/* Toast */}
      {toast && (
        <div style={styles.toast}>
          {toast}
        </div>
      )}
    </div>
  );
}

// ============================================
// WIDGET SUB-COMPONENTS
// ============================================

interface SourceCitationsProps {
  sources: typeof mockSources;
  expandedSource: string | null;
  setExpandedSource: (id: string | null) => void;
}

function SourceCitations({ sources, expandedSource, setExpandedSource }: SourceCitationsProps) {
  return (
    <div>
      <div style={{ fontSize: '11px', fontWeight: 600, color: '#6b7280', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
        📚 Sources
      </div>
      <div style={styles.sourcesContainer}>
        {sources.map((source) => (
          <div key={source.id}>
            <div
              style={styles.sourceCard}
              onClick={() => setExpandedSource(expandedSource === source.id ? null : source.id)}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#6366f1';
                e.currentTarget.style.boxShadow = '0 2px 4px rgba(99, 102, 241, 0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#e5e7eb';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <span style={styles.sourceIcon}>
                {source.type === 'document' ? '📄' : '❓'}
              </span>
              <span style={{ color: '#374151', flex: 1 }}>{source.title}</span>
              <span style={{ fontSize: '10px', color: '#6366f1' }}>View →</span>
            </div>
            {expandedSource === source.id && (
              <div style={styles.sourceExpanded}>
                {source.snippet}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

interface FAQChipsProps {
  faqs: typeof mockFAQs;
  onFAQClick: (faq: typeof mockFAQs[0]) => void;
}

function FAQChips({ faqs, onFAQClick }: FAQChipsProps) {
  return (
    <div>
      <div style={{ fontSize: '11px', fontWeight: 600, color: '#6b7280', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
        💬 Related FAQs
      </div>
      <div style={styles.faqChips}>
        {faqs.map((faq) => (
          <button
            key={faq.id}
            style={styles.faqChip}
            onClick={() => onFAQClick(faq)}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#6366f1';
              e.currentTarget.style.color = 'white';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'white';
              e.currentTarget.style.color = '#6366f1';
            }}
          >
            {faq.question}
          </button>
        ))}
      </div>
    </div>
  );
}

interface QuickReplyChipsProps {
  replies: string[];
  onReplyClick: (reply: string) => void;
}

function QuickReplyChips({ replies, onReplyClick }: QuickReplyChipsProps) {
  return (
    <div>
      <div style={{ fontSize: '11px', fontWeight: 600, color: '#6b7280', marginBottom: '8px' }}>
        Suggested Questions
      </div>
      <div style={styles.replyChips}>
        {replies.map((reply, idx) => (
          <button
            key={idx}
            style={styles.replyChip}
            onClick={() => onReplyClick(reply)}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#e5e7eb';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#f3f4f6';
            }}
          >
            {reply}
          </button>
        ))}
      </div>
    </div>
  );
}

interface FeedbackButtonsProps {
  feedbackGiven: 'positive' | 'negative' | null;
  feedbackCounts: typeof mockFeedbackStats;
  onFeedback: (type: 'positive' | 'negative') => void;
}

function FeedbackButtons({ feedbackGiven, feedbackCounts, onFeedback }: FeedbackButtonsProps) {
  return (
    <div>
      <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '6px' }}>
        Was this helpful?
      </div>
      <div style={styles.feedbackContainer}>
        <button
          style={{
            ...styles.feedbackButton,
            backgroundColor: feedbackGiven === 'positive' ? '#dcfce7' : 'white',
            borderColor: feedbackGiven === 'positive' ? '#10b981' : '#e5e7eb',
          }}
          onClick={() => onFeedback('positive')}
          disabled={feedbackGiven !== null}
        >
          👍
          <span style={styles.feedbackCount}>{feedbackCounts.positive}</span>
        </button>
        <button
          style={{
            ...styles.feedbackButton,
            backgroundColor: feedbackGiven === 'negative' ? '#fee2e2' : 'white',
            borderColor: feedbackGiven === 'negative' ? '#ef4444' : '#e5e7eb',
          }}
          onClick={() => onFeedback('negative')}
          disabled={feedbackGiven !== null}
        >
          👎
          <span style={styles.feedbackCount}>{feedbackCounts.negative}</span>
        </button>
      </div>
    </div>
  );
}

interface ContactCardProps {
  options: typeof mockContactOptions;
  onContactClick: (type: string) => void;
}

function ContactCard({ options, onContactClick }: ContactCardProps) {
  return (
    <div>
      <div style={{ fontSize: '11px', fontWeight: 600, color: '#6b7280', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
        📞 Need more help?
      </div>
      <div style={styles.contactContainer}>
        <button
          style={styles.contactButton}
          onClick={() => onContactClick('email')}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = '#6366f1';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = '#e5e7eb';
          }}
        >
          <span style={{ fontSize: '18px' }}>📧</span>
          <div style={styles.contactInfo}>
            <div style={styles.contactLabel}>Email Support</div>
            <div style={styles.contactValue}>{options.email}</div>
          </div>
        </button>
        <button
          style={styles.contactButton}
          onClick={() => onContactClick('phone')}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = '#6366f1';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = '#e5e7eb';
          }}
        >
          <span style={{ fontSize: '18px' }}>📞</span>
          <div style={styles.contactInfo}>
            <div style={styles.contactLabel}>Call Us</div>
            <div style={styles.contactValue}>{options.phone}</div>
          </div>
        </button>
        <button
          style={styles.contactButton}
          onClick={() => onContactClick('live chat')}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = '#6366f1';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = '#e5e7eb';
          }}
        >
          <span style={{ fontSize: '18px' }}>💬</span>
          <div style={styles.contactInfo}>
            <div style={styles.contactLabel}>Live Chat</div>
            <div style={styles.contactValue}>{options.hours}</div>
          </div>
        </button>
      </div>
    </div>
  );
}
