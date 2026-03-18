import * as React from 'react';
import { SourceCitation } from '../components/SourceCitation';
import type { SourceCitation as SourceCitationType } from '../types/widget';

// Demo page to showcase new widget UI/UX features
export function WidgetDemo() {
  const [activeFeature, setActiveFeature] = React.useState<string>('glassmorphism');
  const [demoTheme, setDemoTheme] = React.useState<'light' | 'dark' | 'auto'>('auto');
  const [showWidget, setShowWidget] = React.useState(true);
  
  const features = [
    { id: 'glassmorphism', name: 'Glassmorphism', icon: '🌙' },
    { id: 'carousel', name: 'Product Carousel', icon: '🛍️' },
    { id: 'quickreply', name: 'Quick Replies', icon: '⚡' },
    { id: 'voice', name: 'Voice Input', icon: '🎤' },
    { id: 'proactive', name: 'Proactive Engagement', icon: '🎪' },
    { id: 'grouping', name: 'Message Grouping', icon: '💬' },
    { id: 'animations', name: 'Microinteractions', icon: '✨' },
    { id: 'positioning', name: 'Smart Positioning', icon: '🎯' },
    { id: 'sources', name: 'Source Citations', icon: '📚' },
  ];
  
  return (
    <div style={styles.demoContainer}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>Widget UI/UX Demo</h1>
        <p style={styles.subtitle}>Interactive showcase of innovative features</p>
      </div>
      
      {/* Control Panel */}
      <div style={styles.controlPanel}>
        <div style={styles.controlsRow}>
          <h3 style={styles.controlTitle}>Features:</h3>
          <div style={styles.featureButtons}>
            {features.map(feature => (
              <button
                key={feature.id}
                onClick={() => setActiveFeature(feature.id)}
                style={{
                  ...styles.featureButton,
                  backgroundColor: activeFeature === feature.id ? '#6366f1' : '#f3f4f6',
                  color: activeFeature === feature.id ? 'white' : '#374151',
                }}
              >
                <span style={styles.featureIcon}>{feature.icon}</span>
                {feature.name}
              </button>
            ))}
          </div>
        </div>
        
        <div style={styles.controlsRow}>
          <h3 style={styles.controlTitle}>Theme:</h3>
          <div style={styles.themeButtons}>
            <button
              onClick={() => setDemoTheme('light')}
              style={{
                ...styles.themeButton,
                backgroundColor: demoTheme === 'light' ? '#6366f1' : '#f3f4f6',
                color: demoTheme === 'light' ? 'white' : '#374151',
              }}
            >
              ☀️ Light
            </button>
            <button
              onClick={() => setDemoTheme('dark')}
              style={{
                ...styles.themeButton,
                backgroundColor: demoTheme === 'dark' ? '#6366f1' : '#f3f4f6',
                color: demoTheme === 'dark' ? 'white' : '#374151',
              }}
            >
              🌙 Dark
            </button>
            <button
              onClick={() => setDemoTheme('auto')}
              style={{
                ...styles.themeButton,
                backgroundColor: demoTheme === 'auto' ? '#6366f1' : '#f3f4f6',
                color: demoTheme === 'auto' ? 'white' : '#374151',
              }}
            >
              🔄 Auto
            </button>
          </div>
          
          <button
            onClick={() => setShowWidget(!showWidget)}
            style={{
              ...styles.toggleButton,
              backgroundColor: showWidget ? '#10b981' : '#ef4444',
            }}
          >
            {showWidget ? '✓ Widget Visible' : '✕ Widget Hidden'}
          </button>
        </div>
      </div>
      
      {/* Feature Description */}
      <FeatureDescription feature={activeFeature} />
      
      {/* Demo Area */}
      <div style={styles.demoArea}>
        {showWidget && (
          <FeatureDemo feature={activeFeature} theme={demoTheme} />
        )}
        
        {/* Placeholder content to show smart positioning */}
        <div style={styles.pageContent}>
          <div style={styles.contentBox}>
            <h2>Sample Page Content</h2>
            <p>This represents your e-commerce website content.</p>
            <p>The widget will intelligently avoid overlapping with important elements.</p>
          </div>
          
          <div style={styles.ctaBox}>
            <button style={styles.ctaButton}>
              Important CTA Button
            </button>
          </div>
          
          <div style={styles.productGrid}>
            {[1, 2, 3, 4].map(i => (
              <div key={i} style={styles.productBox}>
                <div style={styles.productImage}>Product {i}</div>
                <p style={styles.productName}>Sample Product {i}</p>
                <p style={styles.productPrice}>$99.00</p>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* Instructions */}
      <div style={styles.instructions}>
        <h3>💡 Try These Interactions:</h3>
        <ul style={styles.instructionList}>
          <li>Click different features to see them in action</li>
          <li>Toggle between light and dark themes</li>
          <li>Hover over product cards for animations</li>
          <li>Click quick reply buttons to see responses</li>
          <li>Try voice input (requires microphone permission)</li>
          <li>Drag the chat window to reposition</li>
          <li>Watch for proactive engagement triggers</li>
        </ul>
      </div>
    </div>
  );
}

// Feature descriptions
function FeatureDescription({ feature }: { feature: string }) {
  const descriptions: Record<string, { title: string; description: string }> = {
    glassmorphism: {
      title: '🌙 Glassmorphism',
      description: 'Modern frosted glass effect with backdrop blur. Supports light and dark modes with glowing message bubbles.',
    },
    carousel: {
      title: '🛍️ Product Carousel',
      description: 'Horizontal scrolling product cards with touch/swipe support. Shows product images, prices, and quick add-to-cart.',
    },
    quickreply: {
      title: '⚡ Quick Reply Buttons',
      description: 'Pre-defined response buttons for faster interaction. Reduces typing and guides conversation flow.',
    },
    voice: {
      title: '🎤 Voice Input',
      description: 'Speech recognition for hands-free interaction. Shows real-time transcript and waveform visualization.',
    },
    proactive: {
      title: '🎪 Proactive Engagement',
      description: 'Triggers based on user behavior: exit intent, time on page, scroll depth. Increases engagement and conversions.',
    },
    grouping: {
      title: '💬 Message Grouping',
      description: 'Groups consecutive messages from same sender. Shows avatars and relative timestamps for cleaner UX.',
    },
    animations: {
      title: '✨ Microinteractions',
      description: 'Delightful animations: typing indicator, ripple effects, hover animations, pulse badges, and smooth transitions.',
    },
    positioning: {
      title: '🎯 Smart Positioning',
      description: 'Automatically detects and avoids important page elements. Responsive positioning for different screen sizes.',
    },
    sources: {
      title: '📚 Source Citations',
      description: 'Displays RAG document sources with relevance scores. Click to open documents. Supports PDF, URL, and text sources. Collapsible for 3+ sources.',
    },
  };
  
  const info = descriptions[feature] || { title: '', description: '' };
  
  return (
    <div style={styles.descriptionBox}>
      <h2 style={styles.descriptionTitle}>{info.title}</h2>
      <p style={styles.descriptionText}>{info.description}</p>
    </div>
  );
}

// Feature demo components
function FeatureDemo({ feature, theme }: { feature: string; theme: 'light' | 'dark' | 'auto' }) {
  switch (feature) {
    case 'glassmorphism':
      return <GlassmorphismDemo theme={theme} />;
    case 'carousel':
      return <CarouselDemo theme={theme} />;
    case 'quickreply':
      return <QuickReplyDemo theme={theme} />;
    case 'voice':
      return <VoiceInputDemo theme={theme} />;
    case 'proactive':
      return <ProactiveDemo theme={theme} />;
    case 'grouping':
      return <GroupingDemo theme={theme} />;
    case 'animations':
      return <AnimationsDemo theme={theme} />;
    case 'positioning':
      return <PositioningDemo theme={theme} />;
    case 'sources':
      return <SourcesDemo theme={theme} />;
    default:
      return <GlassmorphismDemo theme={theme} />;
  }
}

// 1. Glassmorphism Demo
function GlassmorphismDemo({ theme }: { theme: 'light' | 'dark' | 'auto' }) {
  const [systemTheme, setSystemTheme] = React.useState<'light' | 'dark'>('light');
  const [isOpen, setIsOpen] = React.useState(true);
  
  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    setSystemTheme(mediaQuery.matches ? 'dark' : 'light');
    
    const handler = (e: MediaQueryListEvent) => {
      setSystemTheme(e.matches ? 'dark' : 'light');
    };
    
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);
  
  const activeTheme = theme === 'auto' ? systemTheme : theme;
  
  return (
    <>
      {/* Chat Bubble */}
      <button
        data-testid="chat-bubble"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          backgroundColor: '#6366f1',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 24px rgba(99, 102, 241, 0.5)',
          zIndex: 2147483647,
          fontSize: '24px',
          color: 'white',
          transition: 'transform 0.2s ease',
        }}
      >
        {isOpen ? '✕' : '💬'}
      </button>
      
      {/* Chat Window */}
      {isOpen && (
        <div
          data-testid="chat-window"
          style={{
            position: 'fixed',
            bottom: '90px',
            right: '20px',
            width: '380px',
            height: '600px',
            borderRadius: '16px',
            overflow: 'hidden',
            zIndex: 2147483646,
            background: activeTheme === 'dark' 
              ? 'rgba(15, 23, 42, 0.8)' 
              : 'rgba(255, 255, 255, 0.7)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            border: activeTheme === 'dark' 
              ? '1px solid rgba(255, 255, 255, 0.1)' 
              : '1px solid rgba(255, 255, 255, 0.3)',
            boxShadow: activeTheme === 'dark'
              ? '0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
              : '0 8px 32px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.5)',
            display: 'flex',
            flexDirection: 'column',
            color: activeTheme === 'dark' ? 'white' : '#1f2937',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '16px',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.9) 0%, rgba(139, 92, 246, 0.9) 100%)',
              backdropFilter: 'blur(8px)',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              color: 'white',
              fontWeight: 600,
            }}
          >
            🤖 ShopBot Assistant
          </div>
          
          {/* Messages */}
          <div
            style={{
              flex: 1,
              padding: '16px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            {/* Bot message */}
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '70%',
                padding: '12px 16px',
                borderRadius: '12px',
                background: activeTheme === 'dark' 
                  ? 'rgba(255, 255, 255, 0.05)' 
                  : 'rgba(0, 0, 0, 0.03)',
                border: activeTheme === 'dark' 
                  ? '1px solid rgba(255, 255, 255, 0.1)' 
                  : '1px solid rgba(0, 0, 0, 0.05)',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
              }}
            >
              Hi! How can I help you today? ✨
            </div>
            
            {/* User message */}
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '70%',
                padding: '12px 16px',
                borderRadius: '12px',
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                boxShadow: '0 4px 16px rgba(99, 102, 241, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
                color: 'white',
              }}
            >
              Show me running shoes
            </div>
            
            {/* Bot message */}
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '70%',
                padding: '12px 16px',
                borderRadius: '12px',
                background: activeTheme === 'dark' 
                  ? 'rgba(255, 255, 255, 0.05)' 
                  : 'rgba(0, 0, 0, 0.03)',
                border: activeTheme === 'dark' 
                  ? '1px solid rgba(255, 255, 255, 0.1)' 
                  : '1px solid rgba(0, 0, 0, 0.05)',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
              }}
            >
              Great choice! I found some amazing running shoes for you! 🏃‍♂️
            </div>
          </div>
          
          {/* Input */}
          <div
            style={{
              padding: '16px',
              borderTop: activeTheme === 'dark' 
                ? '1px solid rgba(255, 255, 255, 0.1)' 
                : '1px solid rgba(0, 0, 0, 0.05)',
              display: 'flex',
              gap: '8px',
            }}
          >
            <input
              data-testid="message-input"
              type="text"
              placeholder="Type a message..."
              style={{
                flex: 1,
                padding: '10px 14px',
                borderRadius: '8px',
                border: activeTheme === 'dark' 
                  ? '1px solid rgba(255, 255, 255, 0.1)' 
                  : '1px solid rgba(0, 0, 0, 0.1)',
                background: activeTheme === 'dark' 
                  ? 'rgba(255, 255, 255, 0.05)' 
                  : 'rgba(0, 0, 0, 0.03)',
                color: activeTheme === 'dark' ? 'white' : '#1f2937',
                fontSize: '14px',
                outline: 'none',
              }}
            />
            <button
              data-testid="send-message-button"
              style={{
                padding: '10px 16px',
                borderRadius: '8px',
                backgroundColor: '#6366f1',
                color: 'white',
                border: 'none',
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
}

// 2. Product Carousel Demo
function CarouselDemo({ theme: _theme }: { theme: 'light' | 'dark' | 'auto' }) {
  const [currentIndex, setCurrentIndex] = React.useState(0);
  const [cart, setCart] = React.useState<string[]>([]);
  const [adding, setAdding] = React.useState<string | null>(null);
  
  const products = [
    { id: '1', name: 'Nike Air Max', price: 129.99, image: '👟' },
    { id: '2', name: 'Adidas UltraBoost', price: 99.99, image: '👟' },
    { id: '3', name: 'New Balance 990', price: 119.99, image: '👟' },
    { id: '4', name: 'Asics Gel-Kayano', price: 89.99, image: '👟' },
  ];
  
  const handleAddToCart = async (productId: string) => {
    setAdding(productId);
    await new Promise(resolve => setTimeout(resolve, 500));
    setCart(prev => [...prev, productId]);
    setAdding(null);
  };
  
  return (
    <>
      {/* Chat Bubble with badge */}
      <button
        data-testid="chat-bubble"
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          backgroundColor: '#6366f1',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          zIndex: 2147483647,
          fontSize: '24px',
          color: 'white',
        }}
      >
        💬
        {cart.length > 0 && (
          <span
            style={{
              position: 'absolute',
              top: '-5px',
              right: '-5px',
              backgroundColor: '#ef4444',
              color: 'white',
              borderRadius: '50%',
              width: '20px',
              height: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '11px',
              fontWeight: 600,
            }}
          >
            {cart.length}
          </span>
        )}
      </button>
      
      {/* Chat Window with Carousel */}
      <div
        data-testid="chat-window"
        style={{
          position: 'fixed',
          bottom: '90px',
          right: '20px',
          width: '380px',
          height: '600px',
          borderRadius: '12px',
          backgroundColor: 'white',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
          overflow: 'hidden',
          zIndex: 2147483646,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '16px',
            backgroundColor: '#6366f1',
            color: 'white',
            fontWeight: 600,
          }}
        >
          🤖 ShopBot Assistant
        </div>
        
        {/* Messages */}
        <div
          style={{
            flex: 1,
            padding: '16px',
            overflowY: 'auto',
          }}
        >
          {/* Bot message */}
          <div
            style={{
              marginBottom: '12px',
              padding: '12px',
              backgroundColor: '#f3f4f6',
              borderRadius: '12px',
              maxWidth: '70%',
            }}
          >
            Check out these running shoes! 👇
          </div>
          
          {/* Product Carousel */}
          <div
            style={{
              display: 'flex',
              gap: '12px',
              overflowX: 'auto',
              padding: '8px 0',
              scrollBehavior: 'smooth',
            }}
          >
            {products.map((product) => (
              <div
                key={product.id}
                style={{
                  flex: '0 0 160px',
                  backgroundColor: 'white',
                  borderRadius: '12px',
                  overflow: 'hidden',
                  transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                  border: '1px solid #e5e7eb',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.15)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
                }}
              >
                <div style={{ height: '120px', backgroundColor: '#f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '48px' }}>
                  {product.image}
                </div>
                <div style={{ padding: '12px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>{product.name}</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#10b981', marginBottom: '8px' }}>${product.price}</div>
                  <button
                    onClick={() => handleAddToCart(product.id)}
                    disabled={adding === product.id}
                    style={{
                      width: '100%',
                      padding: '8px',
                      backgroundColor: adding === product.id ? '#9ca3af' : '#6366f1',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: adding === product.id ? 'wait' : 'pointer',
                    }}
                  >
                    {adding === product.id ? 'Adding...' : 'Add to Cart'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Input */}
        <div
          style={{
            padding: '16px',
            borderTop: '1px solid #e5e7eb',
            display: 'flex',
            gap: '8px',
          }}
        >
          <input
            type="text"
            placeholder="Type a message..."
            style={{
              flex: 1,
              padding: '10px 14px',
              borderRadius: '8px',
              border: '1px solid #d1d5db',
              fontSize: '14px',
            }}
          />
          <button
            style={{
              padding: '10px 16px',
              borderRadius: '8px',
              backgroundColor: '#6366f1',
              color: 'white',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Send
          </button>
        </div>
      </div>
    </>
  );
}

// 3. Quick Reply Demo
function QuickReplyDemo({ theme: _theme }: { theme: 'light' | 'dark' | 'auto' }) {
  const [selectedOption, setSelectedOption] = React.useState<string | null>(null);
  const [messages, setMessages] = React.useState<Array<{ sender: 'user' | 'bot'; text: string }>>([
    { sender: 'bot', text: 'What would you like to do?' },
  ]);
  
  const quickReplies = [
    { id: 'track', text: '🏃 Track Order', response: 'I want to track my order' },
    { id: 'cart', text: '📦 My Cart', response: 'Show me my cart' },
    { id: 'question', text: '💬 Ask Question', response: 'I have a question' },
    { id: 'faq', text: '❓ FAQs', response: 'Show me frequently asked questions' },
  ];
  
  const handleQuickReply = async (reply: typeof quickReplies[0]) => {
    setSelectedOption(reply.id);
    
    // Add user message
    setMessages(prev => [...prev, { sender: 'user', text: reply.response }]);
    
    // Simulate bot response
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const botResponses: Record<string, string> = {
      track: "Great! Let me help you track your order. 📦\nPlease provide your order number.",
      cart: "Here's what's in your cart:\n\n👟 Nike Air Max - $129.99\n👕 T-Shirt - $29.99\n\nTotal: $159.98",
      question: "Of course! What would you like to know? I'm here to help! 😊",
      faq: "Here are our most common questions:\n\n1. Shipping & Delivery\n2. Returns & Refunds\n3. Payment Methods\n4. Size Guide\n\nWhich one interests you?",
    };
    
    setMessages(prev => [...prev, { sender: 'bot', text: botResponses[reply.id] }]);
    setSelectedOption(null);
  };
  
  return (
    <>
      {/* Chat Bubble */}
      <button
        data-testid="chat-bubble"
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          backgroundColor: '#6366f1',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          zIndex: 2147483647,
          fontSize: '24px',
          color: 'white',
        }}
      >
        💬
      </button>
      
      {/* Chat Window */}
      <div
        data-testid="chat-window"
        style={{
          position: 'fixed',
          bottom: '90px',
          right: '20px',
          width: '380px',
          height: '600px',
          borderRadius: '12px',
          backgroundColor: 'white',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
          overflow: 'hidden',
          zIndex: 2147483646,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '16px',
            backgroundColor: '#6366f1',
            color: 'white',
            fontWeight: 600,
          }}
        >
          🤖 ShopBot Assistant
        </div>
        
        {/* Messages */}
        <div
          style={{
            flex: 1,
            padding: '16px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          {messages.map((msg, index) => (
            <div
              key={index}
              style={{
                alignSelf: msg.sender === 'bot' ? 'flex-start' : 'flex-end',
                maxWidth: '70%',
                padding: '12px 16px',
                borderRadius: '12px',
                backgroundColor: msg.sender === 'bot' ? '#f3f4f6' : '#6366f1',
                color: msg.sender === 'bot' ? '#1f2937' : 'white',
                whiteSpace: 'pre-line',
              }}
            >
              {msg.text}
            </div>
          ))}
        </div>
        
        {/* Quick Reply Buttons */}
        <div style={{ padding: '12px', borderTop: '1px solid #e5e7eb' }}>
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '8px',
            }}
          >
            {quickReplies.map((reply) => (
              <button
                key={reply.id}
                onClick={() => handleQuickReply(reply)}
                disabled={selectedOption !== null}
                data-testid="quick-reply-button"
                style={{
                  flex: '1 1 calc(50% - 4px)',
                  minWidth: '120px',
                  padding: '10px 14px',
                  border: '2px solid #6366f1',
                  borderRadius: '8px',
                  backgroundColor: 'transparent',
                  color: '#6366f1',
                  fontSize: '14px',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'transform 0.15s ease',
                  opacity: selectedOption && selectedOption !== reply.id ? 0.5 : 1,
                }}
              >
                {reply.text}
                </button>
              ))}
          </div>
        </div>
      </div>
    </>
  );
}

// 4. Voice Input Demo
function VoiceInputDemo({ theme: _theme }: { theme: 'light' | 'dark' | 'auto' }) {
  const [isListening, setIsListening] = React.useState(false);
  const [transcript, setTranscript] = React.useState('');
  const [isSupported, setIsSupported] = React.useState(true);
  const [messages, setMessages] = React.useState<Array<{ sender: 'user' | 'bot'; text: string }>>([
    { sender: 'bot', text: 'Click the microphone to start speaking! 🎤' },
  ]);
  
  const startListening = () => {
    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    
    if (!SpeechRecognition) {
      setIsSupported(false);
      alert('Speech recognition is not supported in your browser. Try Chrome or Edge.');
      return;
    }
    
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
      setIsListening(true);
      setTranscript('');
    };
    
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setTranscript(transcript);
    };
    
    recognition.onend = () => {
      setIsListening(false);
      if (transcript) {
        setMessages(prev => [
          ...prev,
          { sender: 'user', text: transcript },
          { sender: 'bot', text: `You said: "${transcript}"` },
        ]);
        setTranscript('');
      }
    };
    
    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };
    
    recognition.start();
  };
  
  return (
    <>
      {/* Chat Bubble */}
      <button
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          backgroundColor: '#6366f1',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          zIndex: 2147483647,
          fontSize: '24px',
          color: 'white',
        }}
      >
        💬
      </button>
      
      {/* Chat Window */}
      <div
        style={{
          position: 'fixed',
          bottom: '90px',
          right: '20px',
          width: '380px',
          height: '600px',
          borderRadius: '12px',
          backgroundColor: 'white',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
          overflow: 'hidden',
          zIndex: 2147483646,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '16px',
            backgroundColor: '#6366f1',
            color: 'white',
            fontWeight: 600,
          }}
        >
          🎤 Voice Input Demo
        </div>
        
        {/* Messages */}
        <div
          style={{
            flex: 1,
            padding: '16px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          {messages.map((msg, index) => (
            <div
              key={index}
              style={{
                alignSelf: msg.sender === 'bot' ? 'flex-start' : 'flex-end',
                maxWidth: '70%',
                padding: '12px 16px',
                borderRadius: '12px',
                backgroundColor: msg.sender === 'bot' ? '#f3f4f6' : '#6366f1',
                color: msg.sender === 'bot' ? '#1f2937' : 'white',
              }}
            >
              {msg.text}
            </div>
          ))}
          
          {/* Listening indicator */}
          {isListening && (
            <div
              style={{
                alignSelf: 'center',
                padding: '20px',
                backgroundColor: '#f3f4f6',
                borderRadius: '12px',
                textAlign: 'center',
              }}
            >
              <div style={{ marginBottom: '12px' }}>
                {/* Waveform animation */}
                <div style={{ display: 'flex', justifyContent: 'center', gap: '4px', marginBottom: '12px' }}>
                  {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map(i => (
                    <div
                      key={i}
                      style={{
                        width: '4px',
                        height: '20px',
                        backgroundColor: '#6366f1',
                        borderRadius: '2px',
                        animation: `wave ${0.5 + i * 0.05}s ease-in-out infinite`,
                        animationDelay: `${i * 0.05}s`,
                      }}
                    />
                  ))}
                </div>
                <p style={{ fontSize: '14px', color: '#6b7280' }}>Listening...</p>
              </div>
              {transcript && (
                <p style={{ fontSize: '16px', color: '#1f2937', fontWeight: 500 }}>
                  "{transcript}"
                </p>
              )}
            </div>
          )}
        </div>
        
        {/* Input with Voice Button */}
        <div
          style={{
            padding: '16px',
            borderTop: '1px solid #e5e7eb',
            display: 'flex',
            gap: '8px',
            alignItems: 'center',
          }}
        >
          <input
            type="text"
            placeholder="Type or use voice..."
            style={{
              flex: 1,
              padding: '10px 14px',
              borderRadius: '8px',
              border: '1px solid #d1d5db',
              fontSize: '14px',
            }}
          />
          <button
            onClick={startListening}
            disabled={isListening || !isSupported}
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '50%',
              backgroundColor: isListening ? '#ef4444' : '#6366f1',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '20px',
              transition: 'background-color 0.2s ease',
            }}
          >
            🎤
          </button>
          <button
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '8px',
              backgroundColor: '#6366f1',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '16px',
              color: 'white',
              fontWeight: 600,
            }}
          >
            Send
          </button>
        </div>
      </div>
      
      {/* Wave animation styles */}
      <style>
        {`
          @keyframes wave {
            0%, 100% { height: 20px; }
            50% { height: 40px; }
          }
        `}
      </style>
    </>
  );
}

// 5. Proactive Engagement Demo
function ProactiveDemo({ theme: _theme }: { theme: 'light' | 'dark' | 'auto' }) {
  const [showPopup, setShowPopup] = React.useState(false);
  const [triggerType, setTriggerType] = React.useState<'exit' | 'time' | 'scroll' | null>(null);
  
  // Simulate time trigger
  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (!showPopup && !triggerType) {
        setTriggerType('time');
        setShowPopup(true);
      }
    }, 5000);
    
    return () => clearTimeout(timer);
  }, []);
  
  // Exit intent detection
  React.useEffect(() => {
    const handleMouseLeave = (e: MouseEvent) => {
      if (e.clientY < 10 && !showPopup && !triggerType) {
        setTriggerType('exit');
        setShowPopup(true);
      }
    };
    
    document.addEventListener('mouseleave', handleMouseLeave);
    return () => document.removeEventListener('mouseleave', handleMouseLeave);
  }, [showPopup, triggerType]);
  
  const triggerMessages: Record<string, { title: string; message: string; cta: string }> = {
    exit: {
      title: "👋 Wait! Don't leave yet!",
      message: 'Get 10% off your first order!',
      cta: 'Claim Discount',
    },
    time: {
      title: '💬 Need help choosing?',
      message: 'I can help you find the perfect product!',
      cta: 'Ask me anything',
    },
    scroll: {
      title: '🔥 Hot deal alert!',
      message: 'Items in your cart are selling fast!',
      cta: 'Complete Purchase',
    },
  };
  
  const currentMessage = triggerType ? triggerMessages[triggerType] : triggerMessages.time;
  
  return (
    <>
      {/* Chat Bubble */}
      <button
        data-testid="chat-bubble"
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          backgroundColor: '#6366f1',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          zIndex: 2147483647,
          fontSize: '24px',
          color: 'white',
        }}
      >
        💬
      </button>
      
      {/* Manual trigger buttons for demo */}
      <div
        style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          zIndex: 2147483640,
        }}
      >
        <button
          onClick={() => {
            setTriggerType('exit');
            setShowPopup(true);
          }}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            backgroundColor: '#6366f1',
            color: 'white',
            border: 'none',
            cursor: 'pointer',
          }}
        >
          Trigger Exit Intent
        </button>
        <button
          onClick={() => {
            setTriggerType('time');
            setShowPopup(true);
          }}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            backgroundColor: '#8b5cf6',
            color: 'white',
            border: 'none',
            cursor: 'pointer',
          }}
        >
          Trigger Time Popup
        </button>
        <button
          onClick={() => {
            setTriggerType('scroll');
            setShowPopup(true);
          }}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            backgroundColor: '#a855f7',
            color: 'white',
            border: 'none',
            cursor: 'pointer',
          }}
        >
          Trigger Scroll Popup
        </button>
      </div>
      
      {/* Popup */}
      {showPopup && (
        <div
          style={{
            position: 'fixed',
            bottom: '90px',
            right: '20px',
            width: '320px',
            padding: '20px',
            borderRadius: '16px',
            backgroundColor: 'white',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
            zIndex: 2147483646,
            animation: 'slideUp 0.3s ease',
          }}
        >
          <h3 style={{ marginBottom: '8px', fontSize: '16px' }}>{currentMessage.title}</h3>
          <p style={{ marginBottom: '16px', fontSize: '14px', color: '#6b7280' }}>{currentMessage.message}</p>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setShowPopup(false)}
              style={{
                flex: 1,
                padding: '12px 20px',
                borderRadius: '8px',
                backgroundColor: 'transparent',
                color: '#6366f1',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
                border: '1px solid #e5e7eb',
              }}
            >
              No thanks
            </button>
            <button
              onClick={() => setShowPopup(false)}
              style={{
                flex: 1,
                padding: '12px 20px',
                borderRadius: '8px',
                backgroundColor: '#6366f1',
                color: 'white',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
                border: 'none',
              }}
            >
              {currentMessage.cta}
            </button>
          </div>
        </div>
      )}
      
      {/* Animation styles */}
      <style>
        {`
          @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
          }
          @keyframes slideUp {
            from { 
              opacity: 0;
              transform: translateY(20px);
            }
            to { 
              opacity: 1;
              transform: translateY(0);
            }
          }
        `}
      </style>
    </>
  );
}

// 6. Message Grouping Demo
function GroupingDemo({ theme: _theme }: { theme: 'light' | 'dark' | 'auto' }) {
  const messages = [
    { id: 1, sender: 'bot' as const, text: 'Hi! Welcome to our store!', time: '10:30 AM' },
    { id: 2, sender: 'bot' as const, text: 'How can I help you today?', time: '10:30 AM' },
    { id: 3, sender: 'user' as const, text: 'Show me running shoes', time: '10:31 AM' },
    { id: 4, sender: 'bot' as const, text: 'Great choice!', time: '10:31 AM' },
    { id: 5, sender: 'bot' as const, text: 'Here are some popular options:', time: '10:31 AM' },
    { id: 6, sender: 'bot' as const, text: '🏃 Nike Air Max\n👟 Adidas UltraBoost\n👟 New Balance 990', time: '10:31 AM' },
    { id: 7, sender: 'user' as const, text: 'I like the Nike ones', time: '10:32 AM' },
    { id: 8, sender: 'user' as const, text: 'Do you have them in size 10?', time: '10:32 AM' },
    { id: 9, sender: 'bot' as const, text: 'Yes! We have the Nike Air Max in size 10. Would you like to add them to your cart?', time: '10:32 AM' },
  ];
  
  // Group consecutive messages
  const groupedMessages: Array<Array<typeof messages[0]>> = [];
  messages.forEach((msg) => {
    const lastGroup = groupedMessages[groupedMessages.length - 1];
    if (lastGroup && lastGroup[0].sender === msg.sender) {
      lastGroup.push(msg);
    } else {
      groupedMessages.push([msg]);
    }
  });
  
  return (
    <>
      {/* Chat Bubble */}
      <button
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          backgroundColor: '#6366f1',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          zIndex: 2147483647,
          fontSize: '24px',
          color: 'white',
        }}
      >
        💬
      </button>
      
      {/* Chat Window */}
      <div
        style={{
          position: 'fixed',
          bottom: '90px',
          right: '20px',
          width: '380px',
          height: '600px',
          borderRadius: '12px',
          backgroundColor: 'white',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
          overflow: 'hidden',
          zIndex: 2147483646,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '16px',
            backgroundColor: '#6366f1',
            color: 'white',
            fontWeight: 600,
          }}
        >
          🤖 ShopBot Assistant
        </div>
        
        {/* Messages */}
        <div
          style={{
            flex: 1,
            padding: '16px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          {groupedMessages.map((group, groupIndex) => {
            const isBot = group[0].sender === 'bot';
            const avatar = isBot ? '🤖' : '👤';
            
            return (
              <div
                key={groupIndex}
                style={{
                  display: 'flex',
                  alignItems: 'flex-end',
                  gap: '8px',
                  flexDirection: isBot ? 'row' : 'row-reverse',
                }}
              >
                {/* Avatar */}
                {isBot && (
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      backgroundColor: '#e5e7eb',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '18px',
                      flexShrink: 0,
                    }}
                  >
                    {avatar}
                  </div>
                )}
                
                {/* Messages */}
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    maxWidth: '70%',
                  }}
                >
                  {group.map((msg, msgIndex) => (
                    <div
                      key={msg.id}
                      style={{
                        padding: '10px 14px',
                        borderRadius: '12px',
                        backgroundColor: isBot ? '#f3f4f6' : '#6366f1',
                        color: isBot ? '#1f2937' : 'white',
                        borderBottomLeftRadius: isBot && msgIndex === group.length - 1 ? 4 : 12,
                        borderBottomRightRadius: !isBot && msgIndex === group.length - 1 ? 4 : 12,
                        whiteSpace: 'pre-line',
                      }}
                    >
                      {msg.text}
                      {/* Timestamp only on last message */}
                      {msgIndex === group.length - 1 && (
                        <div
                          style={{
                            fontSize: '11px',
                            opacity: 0.7,
                            marginTop: '4px',
                            textAlign: isBot ? 'left' : 'right',
                          }}
                        >
                          {msg.time}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
        
        {/* Input */}
        <div
          style={{
            padding: '16px',
            borderTop: '1px solid #e5e7eb',
            display: 'flex',
            gap: '8px',
          }}
        >
          <input
            type="text"
            placeholder="Type a message..."
            style={{
              flex: 1,
              padding: '10px 14px',
              borderRadius: '8px',
              border: '1px solid #d1d5db',
              fontSize: '14px',
            }}
          />
          <button
            style={{
              padding: '10px 16px',
              borderRadius: '8px',
              backgroundColor: '#6366f1',
              color: 'white',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Send
          </button>
        </div>
      </div>
    </>
  );
}

// 7. Microinteractions Demo
function AnimationsDemo({ theme: _theme }: { theme: 'light' | 'dark' | 'auto' }) {
  const [showTyping, setShowTyping] = React.useState(true);
  const [unreadCount, setUnreadCount] = React.useState(3);
  const [showSuccess, setShowSuccess] = React.useState(false);
  const [reducedMotion, setReducedMotion] = React.useState(false);
  
  return (
    <>
      {/* Chat Bubble with animated badge */}
      <button
        onClick={() => setUnreadCount(0)}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          backgroundColor: '#6366f1',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          zIndex: 2147483647,
          fontSize: '24px',
          color: 'white',
        }}
      >
        💬
        {unreadCount > 0 && (
          <span
            style={{
              position: 'absolute',
              top: '-5px',
              right: '-5px',
              backgroundColor: '#ef4444',
              color: 'white',
              borderRadius: '50%',
              minWidth: '20px',
              height: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '11px',
              fontWeight: 600,
              animation: reducedMotion ? 'none' : 'pulse 2s ease-in-out infinite',
            }}
          >
            {unreadCount}
          </span>
        )}
      </button>
      
      {/* Chat Window */}
      <div
        style={{
          position: 'fixed',
          bottom: '90px',
          right: '20px',
          width: '380px',
          height: '600px',
          borderRadius: '12px',
          backgroundColor: 'white',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
          overflow: 'hidden',
          zIndex: 2147483646,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '16px',
            backgroundColor: '#6366f1',
            color: 'white',
            fontWeight: 600,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>✨ Microinteractions Demo</span>
          <button
            onClick={() => setReducedMotion(!reducedMotion)}
            style={{
              padding: '4px 8px',
              borderRadius: '4px',
              backgroundColor: reducedMotion ? 'rgba(255, 255, 255, 0.3)' : 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              color: 'white',
              cursor: 'pointer',
              fontSize: '11px',
            }}
          >
            {reducedMotion ? '♿ Reduced Motion ON' : '♿ Reduced Motion OFF'}
          </button>
        </div>
        
        {/* Animation Types Documentation */}
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: '#f9fafb',
            borderBottom: '1px solid #e5e7eb',
            fontSize: '11px',
            color: '#6b7280',
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: '8px', color: '#374151' }}>
            Animation Types:
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
            <div>• <strong>Bouncing Dots:</strong> Typing indicator</div>
            <div>• <strong>Message Fade:</strong> New messages</div>
            <div>• <strong>Ripple Effect:</strong> Button clicks</div>
            <div>• <strong>Checkmark Draw:</strong> Success feedback</div>
            <div>• <strong>Badge Pulse:</strong> Unread count</div>
            <div>• <strong>Hover Scale:</strong> Chat bubble</div>
          </div>
        </div>
        
        {/* Messages */}
        <div
          style={{
            flex: 1,
            padding: '16px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          {/* Bot message with fade-in */}
          <div
            style={{
              alignSelf: 'flex-start',
              maxWidth: '70%',
              padding: '12px 16px',
              borderRadius: '12px',
              backgroundColor: '#f3f4f6',
              animation: reducedMotion ? 'none' : 'fadeInUp 0.3s ease',
            }}
          >
            Check out these cool animations! 👇
          </div>
          
          {/* Ripple button demo */}
          <div style={{ alignSelf: 'center', marginTop: '12px' }}>
            <button
              onClick={() => setShowSuccess(true)}
              style={{
                padding: '12px 24px',
                borderRadius: '8px',
                backgroundColor: '#10b981',
                color: 'white',
                border: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              {showSuccess ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <path d="M8 12l3 3 5-6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  Success!
                </span>
              ) : (
                'Click for Animation'
              )}
            </button>
          </div>
          
          {/* Typing indicator */}
          {showTyping && (
            <div
              style={{
                alignSelf: 'flex-start',
                padding: '12px 16px',
                borderRadius: '12px',
                backgroundColor: '#f3f4f6',
              }}
            >
              <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                <span style={{ fontSize: '14px', color: '#6b7280', marginRight: '8px' }}>
                  Bot is typing
                </span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {[0, 1, 2].map(i => (
                    <div
                      key={i}
                      style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        backgroundColor: '#9ca3af',
                        animation: reducedMotion ? 'none' : `bounce 1.4s ease-in-out infinite`,
                        animationDelay: reducedMotion ? '0s' : `${i * 0.15}s`,
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
          
          {/* Toggle typing indicator */}
          <button
            onClick={() => setShowTyping(!showTyping)}
            style={{
              alignSelf: 'center',
              padding: '8px 16px',
              borderRadius: '8px',
              backgroundColor: '#f3f4f6',
              border: '1px solid #d1d5db',
              cursor: 'pointer',
              fontSize: '12px',
            }}
          >
            {showTyping ? 'Hide Typing Indicator' : 'Show Typing Indicator'}
          </button>
          
          {/* Add unread badge */}
          <button
            onClick={() => setUnreadCount(prev => prev + 1)}
            style={{
              alignSelf: 'center',
              padding: '8px 16px',
              borderRadius: '8px',
              backgroundColor: '#f3f4f6',
              border: '1px solid #d1d5db',
              cursor: 'pointer',
              fontSize: '12px',
            }}
          >
            Add Unread Badge
          </button>
        </div>
        
        {/* Input */}
        <div
          style={{
            padding: '16px',
            borderTop: '1px solid #e5e7eb',
            display: 'flex',
            gap: '8px',
          }}
        >
          <input
            type="text"
            placeholder="Type a message..."
            style={{
              flex: 1,
              padding: '10px 14px',
              borderRadius: '8px',
              border: '1px solid #d1d5db',
              fontSize: '14px',
            }}
          />
          <button
            style={{
              padding: '10px 16px',
              borderRadius: '8px',
              backgroundColor: '#6366f1',
              color: 'white',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Send
          </button>
        </div>
      </div>
      
      {/* Animation styles */}
      <style>
        {`
          @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
          }
          @keyframes bounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-8px); }
          }
          @keyframes fadeInUp {
            from {
              opacity: 0;
              transform: translateY(10px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
        `}
      </style>
    </>
  );
}

// 8. Smart Positioning Demo
function PositioningDemo({ theme: _theme }: { theme: 'light' | 'dark' | 'auto' }) {
  const [position, setPosition] = React.useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = React.useState(false);
  const dragStartRef = React.useRef({ x: 0, y: 0, windowX: 0, windowY: 0 });
  
  const handleDragStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    dragStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      windowX: position.x,
      windowY: position.y,
    };
  };
  
  React.useEffect(() => {
    if (!isDragging) return;
    
    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - dragStartRef.current.x;
      const deltaY = e.clientY - dragStartRef.current.y;
      const newX = dragStartRef.current.windowX + deltaX;
      const newY = dragStartRef.current.windowY + deltaY;
      
      // Boundary constraints
      const boundedX = Math.max(-window.innerWidth + 200, Math.min(newX, window.innerWidth - 200));
      const boundedY = Math.max(-window.innerHeight + 200, Math.min(newY, window.innerHeight - 200));
      
      setPosition({ x: boundedX, y: boundedY });
    };
    
    const handleMouseUp = () => {
      setIsDragging(false);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);
  
  return (
    <>
      {/* Chat Bubble */}
      <button
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          backgroundColor: '#6366f1',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          zIndex: 2147483647,
          fontSize: '24px',
          color: 'white',
        }}
      >
        💬
      </button>
      
      {/* Draggable Chat Window */}
      <div
        style={{
          position: 'fixed',
          bottom: '90px',
          right: '20px',
          width: '380px',
          height: '600px',
          borderRadius: '12px',
          backgroundColor: 'white',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
          overflow: 'hidden',
          zIndex: 2147483646,
          display: 'flex',
          flexDirection: 'column',
          transform: position.x !== 0 || position.y !== 0 
            ? `translate(${position.x}px, ${position.y}px)` 
            : undefined,
          transition: isDragging ? 'none' : 'transform 0.2s ease-out',
          userSelect: isDragging ? 'none' : 'auto',
        }}
      >
        {/* Header (draggable) */}
        <div
          onMouseDown={handleDragStart}
          style={{
            padding: '16px',
            backgroundColor: '#6366f1',
            color: 'white',
            fontWeight: 600,
            cursor: isDragging ? 'grabbing' : 'grab',
          }}
        >
          🎯 Drag me to reposition!
        </div>
        
        {/* Info */}
        <div
          style={{
            flex: 1,
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '16px',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '48px' }}>🎯</div>
          <h3 style={{ fontSize: '20px', marginBottom: '8px' }}>Smart Positioning</h3>
          <p style={{ fontSize: '14px', color: '#6b7280', maxWidth: '300px' }}>
            Drag the header to move the widget. It will avoid overlapping with important page elements.
          </p>
          <div
            style={{
              padding: '12px',
              backgroundColor: '#f3f4f6',
              borderRadius: '8px',
              fontSize: '12px',
              fontFamily: 'monospace',
            }}
          >
            Position: ({Math.round(position.x)}, {Math.round(position.y)})
          </div>
          <button
            onClick={() => setPosition({ x: 0, y: 0 })}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              backgroundColor: '#f3f4f6',
              border: '1px solid #d1d5db',
              cursor: 'pointer',
              fontSize: '12px',
            }}
          >
            Reset Position
          </button>
        </div>
      </div>
    </>
  );
}

// Sources Demo Component (Story 10-1)
function SourcesDemo({ theme: _theme }: { theme: 'light' | 'dark' | 'auto' }) {
  const mockSources: SourceCitationType[] = [
    {
      documentId: 1,
      title: 'Product Manual - Battery Life.pdf',
      documentType: 'pdf',
      relevanceScore: 0.95,
      chunkIndex: 12,
    },
    {
      documentId: 2,
      title: 'FAQ - Returns & Exchanges',
      documentType: 'url',
      relevanceScore: 0.88,
      url: 'https://example.com/faq/returns',
    },
    {
      documentId: 3,
      title: 'Warranty Information.txt',
      documentType: 'text',
      relevanceScore: 0.82,
      chunkIndex: 3,
    },
    {
      documentId: 4,
      title: 'Shipping Policy',
      documentType: 'text',
      relevanceScore: 0.75,
    },
    {
      documentId: 5,
      title: 'Contact Support',
      documentType: 'url',
      relevanceScore: 0.72,
      url: 'https://example.com/contact',
    },
  ];

  const [showExpanded, setShowExpanded] = React.useState(false);
  const activeTheme = _theme === 'auto' ? 'light' : _theme;

  return (
    <div style={{
      padding: '32px',
      backgroundColor: activeTheme === 'dark' ? '#1f2937' : '#f9fafb',
      borderRadius: '12px',
      maxWidth: '600px',
      margin: '0 auto',
    }}>
      <h3 style={{ marginBottom: '24px', color: activeTheme === 'dark' ? 'white' : '#1f2937' }}>
        📚 Source Citations Demo
      </h3>

      <div style={{
        backgroundColor: activeTheme === 'dark' ? '#374151' : 'white',
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '24px',
      }}>
        <p style={{ marginBottom: '16px', color: activeTheme === 'dark' ? '#d1d5db' : '#6b7280' }}>
          Bot response with RAG sources:
        </p>
        <div style={{
          padding: '12px',
          backgroundColor: activeTheme === 'dark' ? '#1f2937' : '#f3f4f6',
          borderRadius: '8px',
          marginBottom: '16px',
          color: activeTheme === 'dark' ? '#f3f4f6' : '#1f2937',
        }}>
          Based on our documentation, the battery life is approximately 10 hours under normal usage conditions.
        </div>
        
        <SourceCitation 
          sources={mockSources} 
          theme={{
            primaryColor: '#6366f1',
            backgroundColor: activeTheme === 'dark' ? '#1f2937' : '#ffffff',
            textColor: activeTheme === 'dark' ? '#f3f4f6' : '#1f2937',
            botBubbleColor: activeTheme === 'dark' ? '#374151' : '#f3f4f6',
            userBubbleColor: '#6366f1',
            position: 'bottom-right',
            borderRadius: 16,
            width: 380,
            height: 600,
            fontFamily: 'Inter, sans-serif',
            fontSize: 14,
          }} 
        />
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '16px',
        marginTop: '24px',
      }}>
        <div style={{
          backgroundColor: activeTheme === 'dark' ? '#374151' : '#f3f4f6',
          padding: '16px',
          borderRadius: '8px',
        }}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>📄</div>
          <div style={{ 
            fontWeight: 600, 
            marginBottom: '4px',
            color: activeTheme === 'dark' ? 'white' : '#1f2937',
          }}>
            PDF
          </div>
          <div style={{ 
            fontSize: '12px',
            color: activeTheme === 'dark' ? '#9ca3af' : '#6b7280',
          }}>
            Document icon for PDFs
          </div>
        </div>

        <div style={{
          backgroundColor: activeTheme === 'dark' ? '#374151' : '#f3f4f6',
          padding: '16px',
          borderRadius: '8px',
        }}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>🔗</div>
          <div style={{ 
            fontWeight: 600, 
            marginBottom: '4px',
            color: activeTheme === 'dark' ? 'white' : '#1f2937',
          }}>
            URL
          </div>
          <div style={{ 
            fontSize: '12px',
            color: activeTheme === 'dark' ? '#9ca3af' : '#6b7280',
          }}>
            Link icon for web pages
          </div>
        </div>

        <div style={{
          backgroundColor: activeTheme === 'dark' ? '#374151' : '#f3f4f6',
          padding: '16px',
          borderRadius: '8px',
        }}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>📝</div>
          <div style={{ 
            fontWeight: 600, 
            marginBottom: '4px',
            color: activeTheme === 'dark' ? 'white' : '#1f2937',
          }}>
            Text
          </div>
          <div style={{ 
            fontSize: '12px',
            color: activeTheme === 'dark' ? '#9ca3af' : '#6b7280',
          }}>
            Text icon for documents
          </div>
        </div>
      </div>

      <div style={{
        marginTop: '24px',
        padding: '16px',
        backgroundColor: activeTheme === 'dark' ? '#374151' : '#eff6ff',
        borderRadius: '8px',
      }}>
        <h4 style={{ marginBottom: '12px', color: activeTheme === 'dark' ? 'white' : '#1f2937' }}>
          ✨ Key Features:
        </h4>
        <ul style={{ 
          margin: 0, 
          paddingLeft: '20px',
          color: activeTheme === 'dark' ? '#d1d5db' : '#374151',
        }}>
          <li style={{ marginBottom: '8px' }}>Shows max 3 sources initially</li>
          <li style={{ marginBottom: '8px' }}>Click "View more" to expand</li>
          <li style={{ marginBottom: '8px' }}>Color-coded relevance scores</li>
          <li style={{ marginBottom: '8px' }}>Click to open URL sources</li>
          <li>Dark mode support</li>
        </ul>
      </div>
    </div>
  );
}

// Styles
const styles: Record<string, React.CSSProperties> = {
  demoContainer: {
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    backgroundColor: '#f9fafb',
    minHeight: '100vh',
    padding: '20px',
  },
  header: {
    textAlign: 'center',
    marginBottom: '32px',
  },
  title: {
    fontSize: '36px',
    fontWeight: 700,
    color: '#1f2937',
    marginBottom: '8px',
  },
  subtitle: {
    fontSize: '16px',
    color: '#6b7280',
  },
  controlPanel: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '24px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
  },
  controlsRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    marginBottom: '16px',
    flexWrap: 'wrap',
  },
  controlTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#374151',
    minWidth: '80px',
  },
  featureButtons: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
    flex: 1,
  },
  featureButton: {
    padding: '8px 16px',
    borderRadius: '8px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: 500,
    transition: 'background-color 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  featureIcon: {
    fontSize: '16px',
  },
  themeButtons: {
    display: 'flex',
    gap: '8px',
  },
  themeButton: {
    padding: '8px 16px',
    borderRadius: '8px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: 500,
    transition: 'background-color 0.2s ease',
  },
  toggleButton: {
    padding: '8px 16px',
    borderRadius: '8px',
    border: 'none',
    color: 'white',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: 500,
    marginLeft: 'auto',
  },
  descriptionBox: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '24px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
  },
  descriptionTitle: {
    fontSize: '24px',
    fontWeight: 600,
    color: '#1f2937',
    marginBottom: '12px',
  },
  descriptionText: {
    fontSize: '16px',
    color: '#6b7280',
    lineHeight: 1.6,
  },
  demoArea: {
    position: 'relative',
    minHeight: '800px',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
    overflow: 'hidden',
  },
  pageContent: {
    padding: '24px',
  },
  contentBox: {
    padding: '24px',
    backgroundColor: '#f9fafb',
    borderRadius: '12px',
    marginBottom: '24px',
  },
  ctaBox: {
    textAlign: 'center',
    marginBottom: '24px',
  },
  ctaButton: {
    padding: '16px 32px',
    backgroundColor: '#ef4444',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  productGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
    gap: '16px',
  },
  productBox: {
    padding: '16px',
    backgroundColor: '#f9fafb',
    borderRadius: '12px',
    textAlign: 'center',
  },
  productImage: {
    height: '120px',
    backgroundColor: '#e5e7eb',
    borderRadius: '8px',
    marginBottom: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#6b7280',
  },
  productName: {
    fontSize: '14px',
    fontWeight: 600,
    marginBottom: '4px',
  },
  productPrice: {
    fontSize: '16px',
    fontWeight: 700,
    color: '#10b981',
  },
  instructions: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '24px',
    marginTop: '24px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
  },
  instructionList: {
    listStyleType: 'disc',
    paddingLeft: '24px',
    fontSize: '14px',
    color: '#6b7280',
    lineHeight: 1.8,
  },
};

export default WidgetDemo;
