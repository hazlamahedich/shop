# Embeddable Chat Widget - Implementation Plan

> Status: Planned  
> Created: 2026-02-16  
> Target: Allow merchants and partners to embed the shopping assistant on external websites

## Overview

This document outlines the architecture and implementation plan for creating an embeddable chat widget that can be placed on any website. The widget will allow end users to interact with the AI shopping assistant without leaving the host page.

## Use Cases

1. **Merchant Websites** - Shop owners embed on their own sites to help customers
2. **Partner Integrations** - Third-party platforms (Wix, Shopify, WordPress) integrate the bot
3. **Marketing/Demo** - Showcase the bot on landing pages and demo sites

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    External Website                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  <script src="https://cdn.yourbot.com/widget.js"           │ │
│  │    data-merchant-id="xxx"                                  │ │
│  │    data-theme='{"primaryColor":"#6366f1"}' />              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Shadow DOM (isolated styles)                              │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  Chat Bubble (floating button)                       │  │ │
│  │  │  ┌────────────────────────────────────────────────┐  │  │ │
│  │  │  │  Chat Window (expandable)                      │  │  │ │
│  │  │  │  - Message list                                │  │  │ │
│  │  │  │  - Input field                                 │  │  │ │
│  │  │  │  - Themed via CSS custom properties            │  │  │ │
│  │  │  └────────────────────────────────────────────────┘  │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼ API calls (CORS-enabled)
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│  /api/v1/widget/session     → Create session                    │
│  /api/v1/widget/message     → Send message & get bot response   │
│  /api/v1/widget/config/:id  → Get merchant's theme/bot config   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   External Site  │     │   Widget Bundle  │     │   Backend API    │
│                  │     │   (React App)    │     │   (FastAPI)      │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         │  1. Load script        │                        │
         │ ──────────────────────>│                        │
         │                        │                        │
         │                        │  2. Fetch config       │
         │                        │ ──────────────────────>│
         │                        │                        │
         │                        │  3. Return theme/bot   │
         │                        │ <──────────────────────│
         │                        │                        │
         │                        │  4. Create session     │
         │                        │ ──────────────────────>│
         │                        │                        │
         │                        │  5. Session ID         │
         │                        │ <──────────────────────│
         │                        │                        │
         │  6. User types msg     │                        │
         │ ──────────────────────>│                        │
         │                        │                        │
         │                        │  7. POST /message      │
         │                        │ ──────────────────────>│
         │                        │                        │
         │                        │  8. Bot response       │
         │                        │ <──────────────────────│
         │                        │                        │
         │  9. Display response   │                        │
         │ <──────────────────────│                        │
```

---

## Phase 1: Backend Widget API

### New Files

| File | Purpose |
|------|---------|
| `backend/app/api/widget.py` | Public widget API endpoints |
| `backend/app/schemas/widget.py` | Widget request/response schemas |
| `backend/app/services/widget/widget_service.py` | Widget session management |

### API Endpoints

#### Create Session

```
POST /api/v1/widget/session
```

Creates an anonymous session for the widget user.

**Request:**
```json
{
  "merchant_id": "string"
}
```

**Response:**
```json
{
  "data": {
    "session_id": "string",
    "expires_at": "2024-01-01T12:00:00Z"
  },
  "meta": {}
}
```

#### Send Message

```
POST /api/v1/widget/message
```

Send a message and receive bot response.

**Request:**
```json
{
  "session_id": "string",
  "message": "string"
}
```

**Response:**
```json
{
  "data": {
    "message_id": "string",
    "content": "string",
    "sender": "bot",
    "created_at": "2024-01-01T12:00:00Z"
  },
  "meta": {}
}
```

#### Get Widget Config

```
GET /api/v1/widget/config/{merchant_id}
```

Retrieve merchant's widget configuration (theme, bot name, etc.).

**Response:**
```json
{
  "data": {
    "bot_name": "Shopping Assistant",
    "welcome_message": "Hi! How can I help?",
    "theme": {
      "primary_color": "#6366f1",
      "position": "bottom-right"
    }
  },
  "meta": {}
}
```

#### End Session

```
DELETE /api/v1/widget/session/{session_id}
```

Terminate a widget session.

### Database Changes

Add `widget_config` column to `merchants` table:

```sql
ALTER TABLE merchants ADD COLUMN widget_config JSONB DEFAULT '{}';
```

Schema:
```python
class WidgetConfig(BaseModel):
    enabled: bool = True
    bot_name: str = "Shopping Assistant"
    welcome_message: str = "Hi! How can I help you today?"
    theme: WidgetTheme = WidgetTheme()
    allowed_domains: list[str] = []  # Optional domain whitelist
```

### CORS Configuration

Update `backend/app/core/config.py`:

```python
CORS_ORIGINS = [
    "http://localhost:*",  # Development
    "https://*.shopify.com",  # Shopify stores
    "https://*.myshopify.com",
    # Dynamic validation in middleware
]
```

Add dynamic origin validation middleware to allow any domain for widget requests (with merchant domain validation optional).

---

## Phase 2: Widget Frontend

### Directory Structure

```
frontend/
├── src/
│   └── widget/                    # Widget-specific code
│       ├── index.ts               # Entry point
│       ├── Widget.tsx             # Main widget component
│       ├── components/
│       │   ├── ChatBubble.tsx     # Floating trigger button
│       │   ├── ChatWindow.tsx     # Expandable chat panel
│       │   ├── MessageList.tsx    # Message display
│       │   ├── MessageInput.tsx   # Input field
│       │   └── TypingIndicator.tsx
│       ├── hooks/
│       │   ├── useWidgetSession.ts
│       │   ├── useWidgetTheme.ts
│       │   └── useWidgetApi.ts
│       ├── context/
│       │   └── WidgetContext.tsx
│       ├── utils/
│       │   ├── shadowDom.ts       # Shadow DOM helpers
│       │   └── styles.ts          # Style injection
│       └── types/
│           └── widget.ts
├── vite.widget.config.ts          # Widget-specific build config
└── dist/
    └── widget/
        ├── widget.umd.js          # UMD bundle
        ├── widget.es.js           # ES module bundle
        └── widget.css             # Styles
```

### Key Components

#### Widget.tsx (Main Component)

```tsx
import React from 'react';
import { ChatBubble } from './components/ChatBubble';
import { ChatWindow } from './components/ChatWindow';
import { WidgetProvider } from './context/WidgetContext';

interface WidgetProps {
  merchantId: string;
  theme?: Partial<WidgetTheme>;
  apiBaseUrl?: string;
}

export function Widget({ merchantId, theme, apiBaseUrl }: WidgetProps) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <WidgetProvider merchantId={merchantId} theme={theme} apiBaseUrl={apiBaseUrl}>
      <ChatBubble onClick={() => setIsOpen(!isOpen)} isOpen={isOpen} />
      {isOpen && <ChatWindow onClose={() => setIsOpen(false)} />}
    </WidgetProvider>
  );
}
```

#### ChatBubble.tsx (Floating Button)

```tsx
interface ChatBubbleProps {
  onClick: () => void;
  isOpen: boolean;
}

export function ChatBubble({ onClick, isOpen }: ChatBubbleProps) {
  const { theme } = useWidgetTheme();

  return (
    <button
      className="chat-bubble"
      onClick={onClick}
      style={{ backgroundColor: theme.primaryColor }}
      aria-label={isOpen ? 'Close chat' : 'Open chat'}
    >
      {isOpen ? <CloseIcon /> : <ChatIcon />}
    </button>
  );
}
```

#### ChatWindow.tsx (Chat Panel)

```tsx
interface ChatWindowProps {
  onClose: () => void;
}

export function ChatWindow({ onClose }: ChatWindowProps) {
  const { messages, sendMessage, isLoading } = useWidgetApi();
  const { theme, botName, welcomeMessage } = useWidgetTheme();

  return (
    <div className="chat-window" style={{ borderRadius: theme.borderRadius }}>
      <header>
        <h3>{botName}</h3>
        <button onClick={onClose}>×</button>
      </header>
      <MessageList messages={messages} />
      <MessageInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}
```

### Build Configuration

Create `frontend/vite.widget.config.ts`:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: path.resolve(__dirname, 'src/widget/index.ts'),
      name: 'ShopBotWidget',
      formats: ['umd', 'es'],
      fileName: (format) => `widget.${format === 'umd' ? 'umd' : 'es'}.js`,
    },
    rollupOptions: {
      external: [],
      output: {
        globals: {},
        assetFileNames: 'widget.[ext]',
      },
    },
    outDir: 'dist/widget',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
      },
    },
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
});
```

Add npm scripts to `frontend/package.json`:

```json
{
  "scripts": {
    "build:widget": "vite build --config vite.widget.config.ts",
    "build:all": "npm run build && npm run build:widget"
  }
}
```

---

## Phase 3: Embeddable Loader Script

### Usage

Users embed the widget with this HTML snippet:

```html
<script>
  window.ShopBotConfig = {
    merchantId: 'YOUR_MERCHANT_ID',
    theme: {
      primaryColor: '#6366f1',
      position: 'bottom-right',
      botName: 'My Assistant',
      welcomeMessage: 'Hi! How can I help you today?'
    }
  };
</script>
<script src="https://cdn.yourbot.com/widget.umd.js" async></script>
```

Alternative using data attributes:

```html
<script 
  src="https://cdn.yourbot.com/widget.umd.js" 
  data-merchant-id="YOUR_MERCHANT_ID"
  data-primary-color="#6366f1"
  data-position="bottom-right"
  async>
</script>
```

### Loader Implementation

In `src/widget/index.ts`:

```typescript
import React from 'react';
import { createRoot } from 'react-dom/client';
import { Widget } from './Widget';
import { injectStyles } from './utils/styles';
import './styles/widget.css';

interface ShopBotConfig {
  merchantId: string;
  theme?: Partial<WidgetTheme>;
  apiBaseUrl?: string;
}

declare global {
  interface Window {
    ShopBotConfig?: ShopBotConfig;
  }
}

function init() {
  const script = document.currentScript as HTMLScriptElement;
  
  // Get config from window or data attributes
  const config: ShopBotConfig = window.ShopBotConfig || {
    merchantId: script.dataset.merchantId || '',
    theme: {
      primaryColor: script.dataset.primaryColor,
      position: script.dataset.position as WidgetPosition,
    },
  };

  if (!config.merchantId) {
    console.error('ShopBot: merchantId is required');
    return;
  }

  // Create container with Shadow DOM for style isolation
  const container = document.createElement('div');
  container.id = 'shopbot-widget-root';
  const shadow = container.attachShadow({ mode: 'open' });
  
  // Inject styles into shadow DOM
  injectStyles(shadow);
  
  // Create mount point
  const mountPoint = document.createElement('div');
  shadow.appendChild(mountPoint);
  
  // Append to body
  document.body.appendChild(container);
  
  // Mount React app
  const root = createRoot(mountPoint);
  root.render(
    <Widget
      merchantId={config.merchantId}
      theme={config.theme}
      apiBaseUrl={config.apiBaseUrl}
    />
  );
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
```

### Style Isolation (Shadow DOM)

```typescript
// src/widget/utils/styles.ts
import cssText from '../styles/widget.css?inline';

export function injectStyles(shadow: ShadowRoot) {
  const style = document.createElement('style');
  style.textContent = cssText;
  shadow.appendChild(style);
}
```

---

## Phase 4: Theme Customization System

### Theme Schema

```typescript
// src/widget/types/widget.ts

type WidgetPosition = 'bottom-right' | 'bottom-left';

interface WidgetTheme {
  // Colors
  primaryColor: string;        // Button, accents (default: #6366f1)
  backgroundColor: string;     // Chat window background (default: #ffffff)
  textColor: string;           // Default text color (default: #1f2937)
  botBubbleColor: string;      // Bot message background (default: #f3f4f6)
  userBubbleColor: string;     // User message background (default: #6366f1)
  
  // Layout
  position: WidgetPosition;    // Bubble position (default: bottom-right)
  borderRadius: number;        // Corner radius 0-24 (default: 16)
  width: number;               // Chat window width px (default: 380)
  height: number;              // Chat window height px (default: 600)
  
  // Typography
  fontFamily: string;          // (default: system-ui)
  fontSize: number;            // Base font size px (default: 14)
  
  // Behavior
  autoOpen: boolean;           // Open on page load (default: false)
  persistSession: boolean;     // Remember session (default: true)
}

interface WidgetConfig {
  enabled: boolean;
  botName: string;
  botAvatar?: string;          // URL to custom avatar image
  welcomeMessage: string;
  theme: WidgetTheme;
}
```

### Default Theme

```typescript
const DEFAULT_THEME: WidgetTheme = {
  primaryColor: '#6366f1',
  backgroundColor: '#ffffff',
  textColor: '#1f2937',
  botBubbleColor: '#f3f4f6',
  userBubbleColor: '#6366f1',
  position: 'bottom-right',
  borderRadius: 16,
  width: 380,
  height: 600,
  fontFamily: 'system-ui, -apple-system, sans-serif',
  fontSize: 14,
  autoOpen: false,
  persistSession: true,
};
```

### CSS Custom Properties

The widget uses CSS custom properties for theming:

```css
/* src/widget/styles/widget.css */

:host {
  --sb-primary: var(--shopbot-primary-color, #6366f1);
  --sb-bg: var(--shopbot-background-color, #ffffff);
  --sb-text: var(--shopbot-text-color, #1f2937);
  --sb-bot-bubble: var(--shopbot-bot-bubble-color, #f3f4f6);
  --sb-user-bubble: var(--shopbot-user-bubble-color, #6366f1);
  --sb-radius: var(--shopbot-border-radius, 16px);
  --sb-font: var(--shopbot-font-family, system-ui);
  --sb-font-size: var(--shopbot-font-size, 14px);
}

.chat-bubble {
  background-color: var(--sb-primary);
  /* ... */
}

.chat-window {
  background-color: var(--sb-bg);
  border-radius: var(--sb-radius);
  /* ... */
}
```

### Admin UI (Merchant Settings)

Add widget configuration to the Settings page:

```tsx
// frontend/src/pages/Settings.tsx (excerpt)

function WidgetSettings() {
  return (
    <Card>
      <h2>Embeddable Widget</h2>
      <p>Customize how your chat widget appears on external websites.</p>
      
      <FormField label="Widget Enabled">
        <Toggle name="widgetEnabled" />
      </FormField>
      
      <FormField label="Bot Display Name">
        <Input name="botName" placeholder="Shopping Assistant" />
      </FormField>
      
      <FormField label="Welcome Message">
        <Textarea name="welcomeMessage" placeholder="Hi! How can I help?" />
      </FormField>
      
      <FormField label="Primary Color">
        <ColorPicker name="primaryColor" />
      </FormField>
      
      <FormField label="Position">
        <Select name="position" options={['bottom-right', 'bottom-left']} />
      </FormField>
      
      <FormField label="Embed Code">
        <CodeBlock language="html" copyable>
          {generateEmbedCode(merchantId)}
        </CodeBlock>
      </FormField>
    </Card>
  );
}
```

---

## Phase 5: Security & Performance

### Security Measures

| Concern | Solution |
|---------|----------|
| Rate limiting | Per-merchant + per-IP limits (100 req/min) |
| Session hijacking | Session IDs are UUIDs, expire after 1 hour idle |
| XSS prevention | Shadow DOM isolates widget from host page |
| CORS abuse | Optional domain whitelist per merchant |
| Data exposure | Widget sessions have no auth, only see public data |

### Rate Limiting Implementation

```python
# backend/app/api/widget.py

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/widget/message")
@limiter.limit("100/minute")  # Per IP
async def send_message(request: Request, ...):
    # Also check merchant-level limits
    await check_merchant_rate_limit(merchant_id)
    ...
```

### Performance Targets

| Metric | Target |
|--------|--------|
| Bundle size (gzipped) | < 100KB |
| Initial load time | < 500ms |
| Time to interactive | < 1s |
| Message response | < 2s |

### Optimization Strategies

1. **Tree shaking** - Only include necessary components
2. **Code splitting** - Lazy load non-critical features
3. **Asset optimization** - Inline small SVGs, compress images
4. **Caching** - Aggressive caching for static assets (1 year)
5. **CDN** - Serve widget from edge locations

---

## Phase 6: Distribution & Hosting

### Hosting Options

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| Self-hosted | Full control, no cost | Manual CDN setup | **Start here** |
| Cloudflare Workers | Edge caching, serverless | Learning curve | Future |
| Vercel/Netlify | Easy deploy, auto CDN | Another service | Alternative |
| npm package | Familiar for devs | Requires bundler | For React apps |

### Recommended CDN Setup

```
cdn.yourbot.com/
├── widget.umd.js      # UMD bundle (script tag)
├── widget.es.js       # ES module (import)
├── widget.css         # Styles (if separate)
└── v/
    └── 1.0.0/         # Versioned releases
        ├── widget.umd.js
        └── widget.es.js
```

### Cache Headers

```
# Latest version (frequent updates)
Cache-Control: public, max-age=3600, stale-while-revalidate=86400

# Versioned (immutable)
Cache-Control: public, max-age=31536000, immutable
```

---

## Implementation Timeline

| Phase | Description | Effort | Priority |
|-------|-------------|--------|----------|
| 1 | Backend Widget API | 2-3 days | P0 |
| 2 | Widget Frontend Components | 2-3 days | P0 |
| 3 | Build & Loader Script | 1-2 days | P0 |
| 4 | Theme Customization | 2-3 days | P1 |
| 5 | Security & Performance | 1-2 days | P1 |
| 6 | Documentation | 1 day | P2 |
| 7 | CDN Setup | 1 day | P2 |

**Total Estimated: 10-14 days**

---

## Future Enhancements

- **Multi-language support** - Localize widget UI
- **Analytics dashboard** - Track widget usage per merchant
- **A/B testing** - Test different widget configurations
- **Proactive messaging** - Bot initiates conversation based on user behavior
- **Product cards** - Rich product previews in chat
- **Handoff to live chat** - Transfer to human support
- **WhatsApp/Telegram integration** - Same bot, different channels

---

## Related Documents

- [Architecture: E-Commerce Abstraction](./architecture/ecommerce-abstraction.md)
- [API: Preview Mode](../backend/docs/api/preview.md)
- [Frontend: Component Library](../frontend/docs/components.md)

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-02-16 | AI Agent | Initial plan created |
