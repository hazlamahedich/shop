/**
 * Mock Data for General Mode Widgets Demo
 * Pure mock data - no backend calls required
 */

// ============================================
// CHAT WIDGET MOCK DATA
// ============================================

export const mockSources = [
  {
    id: '1',
    title: 'Return Policy PDF',
    type: 'document' as const,
    url: '#return-policy',
    snippet: 'Our return policy allows returns within 30 days of purchase. Items must be unused and in original packaging...',
  },
  {
    id: '2',
    title: 'FAQ #12: Returns',
    type: 'faq' as const,
    url: '#faq-12',
    snippet: 'Q: What is your return window? A: You have 30 days from the delivery date to return items...',
  },
  {
    id: '3',
    title: 'Shipping Guide',
    type: 'document' as const,
    url: '#shipping-guide',
    snippet: 'Return shipping is free for defective items. For other returns, a $5.99 shipping fee applies...',
  },
];

export const mockFAQs = [
  {
    id: 1,
    question: 'What is your return window?',
    answer: 'You have 30 days from the delivery date to return most items. Some products like electronics have a 14-day return window.',
  },
  {
    id: 2,
    question: 'How do refunds work?',
    answer: 'Refunds are processed within 5-7 business days after we receive your return. The refund will be credited to your original payment method.',
  },
  {
    id: 3,
    question: 'Can I exchange my item?',
    answer: 'Yes! Exchanges are free and can be initiated through your order history. The new item will be shipped once we receive your return.',
  },
  {
    id: 4,
    question: 'What if my item is damaged?',
    answer: 'Contact us within 48 hours of delivery with photos of the damage. We will send a replacement at no extra cost.',
  },
];

export const mockSuggestedReplies = [
  'How do I track my return?',
  'Contact customer support',
  'View full return policy',
];

export const mockContactOptions = {
  email: 'support@example.com',
  phone: '+1 (555) 123-4567',
  supportUrl: 'https://support.example.com',
  hours: 'Mon-Fri 9am-5pm EST',
  liveChat: true,
};

export const mockConversations: Record<string, Array<{ sender: 'user' | 'bot'; text: string; sources?: typeof mockSources; faqs?: typeof mockFAQs; suggestedReplies?: string[]; showFeedback?: boolean; contactOptions?: typeof mockContactOptions }>> = {
  sources: [
    { sender: 'bot', text: 'Hi! I\'m your support assistant. How can I help you today?' },
    { sender: 'user', text: 'What\'s your return policy?' },
    { sender: 'bot', text: 'Great question! Our return policy allows returns within 30 days of purchase. Items must be unused and in original packaging. Here are the details:', sources: mockSources },
  ],
  faq: [
    { sender: 'bot', text: 'Hi! I can help you with common questions. Click any topic below or type your own question.', faqs: mockFAQs.slice(0, 3) },
  ],
  replies: [
    { sender: 'bot', text: 'You can return items within 30 days of delivery. Refunds are processed in 5-7 business days.' },
    { sender: 'bot', text: 'Is there anything else I can help you with?', suggestedReplies: mockSuggestedReplies },
  ],
  feedback: [
    { sender: 'bot', text: 'Based on our policy, you have 30 days to return items from the delivery date. The item must be in its original condition.', showFeedback: true },
  ],
  contact: [
    { sender: 'user', text: 'I need to talk to a real person' },
    { sender: 'bot', text: 'I understand you\'d like to speak with our team. Here are the ways you can reach us:', contactOptions: mockContactOptions },
  ],
};

// ============================================
// DASHBOARD WIDGET MOCK DATA
// ============================================

export const mockDashboardStats = {
  // Conversation stats
  conversations: {
    total: 247,
    active: 12,
    handoffs: 8,
    satisfaction: 94,
    avgMessages: 4.2,
    change: 12,
  },

  // AI Cost stats
  aiCost: {
    total: 45.23,
    requests: 1234,
    change: -12,
    breakdown: {
      openai: 32.50,
      anthropic: 12.73,
    },
  },

  // Knowledge Base stats
  knowledgeBase: {
    totalDocs: 12,
    ready: 10,
    processing: 2,
    error: 0,
    lastUpload: '2024-01-15T10:30:00Z',
    totalChunks: 456,
  },

  // Handoff stats
  handoffs: {
    pending: 3,
    vip: 1,
    avgWait: '4m 23s',
    items: [
      { id: 1, customer: 'John D.', email: 'john@example.com', waitTime: '12m', urgency: 'high', isVip: true, message: 'Need help with a refund' },
      { id: 2, customer: 'Sarah M.', email: 'sarah@example.com', waitTime: '8m', urgency: 'medium', isVip: false, message: 'Question about shipping' },
      { id: 3, customer: 'Mike R.', email: 'mike@example.com', waitTime: '3m', urgency: 'low', isVip: false, message: 'Product availability' },
    ],
  },

  // Bot Quality stats
  botQuality: {
    csat: 4.2,
    responseTime: 2.3,
    fallbackRate: 8,
    resolutionRate: 92,
    healthStatus: 'healthy' as const,
    csatChange: 5,
  },

  // Sentiment stats
  sentiment: {
    positive: 78,
    negative: 12,
    neutral: 10,
    trend: 'improving' as const,
    trendChange: 5,
    dailyBreakdown: [
      { date: '2024-01-09', positiveRate: 0.72 },
      { date: '2024-01-10', positiveRate: 0.75 },
      { date: '2024-01-11', positiveRate: 0.68 },
      { date: '2024-01-12', positiveRate: 0.80 },
      { date: '2024-01-13', positiveRate: 0.77 },
      { date: '2024-01-14', positiveRate: 0.82 },
      { date: '2024-01-15', positiveRate: 0.78 },
    ],
  },

  // Peak Hours (7 days x 24 hours)
  peakHours: generatePeakHoursData(),

  // Knowledge Gaps
  knowledgeGaps: [
    { topic: 'Pricing information', count: 23, trend: 'up' as const },
    { topic: 'API documentation', count: 15, trend: 'stable' as const },
    { topic: 'Bulk ordering', count: 12, trend: 'up' as const },
    { topic: 'International shipping', count: 8, trend: 'down' as const },
  ],

  // Top Topics (for new widget)
  topTopics: [
    { topic: 'Returns & Refunds', count: 45, trend: 'up' as const },
    { topic: 'Shipping & Delivery', count: 38, trend: 'stable' as const },
    { topic: 'Pricing & Discounts', count: 29, trend: 'up' as const },
    { topic: 'Product Information', count: 24, trend: 'down' as const },
    { topic: 'Order Status', count: 18, trend: 'stable' as const },
  ],

  // Knowledge Effectiveness (for new widget)
  knowledgeEffectiveness: {
    hitRate: 87,
    avgRelevance: 0.82,
    chunksUsed: 156,
    queriesWithoutMatch: 23,
    change: 5,
  },

  // Response Time Distribution (for new widget)
  responseTimes: {
    p50: 1.2,
    p95: 3.4,
    p99: 5.1,
    avg: 2.3,
  },

  // FAQ Usage (for new widget)
  faqUsage: [
    { question: 'What is your return window?', clicks: 89, helpful: 76, notHelpful: 4 },
    { question: 'How much is shipping?', clicks: 67, helpful: 58, notHelpful: 3 },
    { question: 'Do you ship internationally?', clicks: 54, helpful: 49, notHelpful: 2 },
    { question: 'How do I track my order?', clicks: 45, helpful: 42, notHelpful: 1 },
    { question: 'What payment methods?', clicks: 38, helpful: 35, notHelpful: 0 },
  ],

  // Benchmark Comparison
  benchmarks: {
    costPerConversation: { value: 0.18, benchmark: 0.25, status: 'better' as const },
    responseTime: { value: 2.3, benchmark: 3.0, status: 'better' as const },
    resolutionRate: { value: 92, benchmark: 85, status: 'better' as const },
    satisfaction: { value: 94, benchmark: 88, status: 'better' as const },
  },
};

// Helper to generate peak hours heatmap data
function generatePeakHoursData(): number[][] {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const hours = Array.from({ length: 24 }, (_, i) => i);
  
  return days.map(() => 
    hours.map(hour => {
      // Simulate realistic patterns: higher during business hours
      if (hour >= 9 && hour <= 17) return Math.floor(Math.random() * 30) + 20;
      if (hour >= 18 && hour <= 21) return Math.floor(Math.random() * 20) + 10;
      return Math.floor(Math.random() * 10);
    })
  );
}

// Feedback mock
export const mockFeedbackStats = {
  positive: 156,
  negative: 23,
  total: 179,
  positiveRate: 87,
};
