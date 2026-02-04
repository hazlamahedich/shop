/** BotPreview component.

Messenger chat simulation component for testing the bot.
Displays bot responses in a chat bubble format with predefined test queries.
*/

import * as React from "react";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Button } from "../ui/Button";
import { Alert } from "../ui/Alert";

export interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const PREDEFINED_QUERIES = [
  "What running shoes do you have under $100?",
  "I'm looking for size 8 running shoes",
  "Show me your most popular products",
];

export interface BotPreviewProps {
  className?: string;
}

export function BotPreview({ className = "" }: BotPreviewProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const sendMessage = async (message: string) => {
    if (!message.trim()) return;

    setError(null);

    // Add user message
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: message,
        timestamp: new Date(),
      },
    ]);

    setIsLoading(true);

    try {
      const response = await fetch("/api/llm/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error("Failed to get bot response");
      }

      const data = await response.json();

      // Add bot response
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.data.response,
          timestamp: new Date(),
        },
      ]);
    } catch (err) {
      setError(
        "Sorry, I'm having trouble connecting. Please check your LLM configuration."
      );
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, I'm having trouble connecting. Please check your LLM configuration.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && inputValue.trim()) {
      sendMessage(inputValue);
      setInputValue("");
    }
  };

  return (
    <Card className={`bot-preview ${className}`}>
      <CardHeader>
        <CardTitle>Test Your Bot</CardTitle>
        <p className="text-sm text-slate-600">
          Send a test message to see how your bot responds
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Error alert */}
        {error && (
          <Alert variant="destructive" className="text-sm">
            {error}
          </Alert>
        )}

        {/* Quick query buttons */}
        <div className="space-y-2">
          <p className="text-sm font-medium text-slate-700">Quick test queries:</p>
          <div className="grid grid-cols-1 gap-2">
            {PREDEFINED_QUERIES.map((query, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                className="justify-start text-left"
                onClick={() => sendMessage(query)}
                disabled={isLoading}
                aria-label={`Send test query: ${query}`}
              >
                {query}
              </Button>
            ))}
          </div>
        </div>

        {/* Chat messages */}
        <div
          className="chat-messages flex max-h-64 flex-col gap-3 overflow-y-auto rounded-md border border-slate-200 bg-slate-50 p-4"
          role="log"
          aria-live="polite"
          aria-atomic="false"
        >
          {messages.length === 0 && (
            <div className="flex h-full items-center justify-center text-center">
              <p className="text-sm text-slate-500">
                No messages yet. Send a test message to get started.
              </p>
            </div>
          )}

          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`message-bubble max-w-[80%] rounded-lg px-4 py-2 ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-white text-slate-900 shadow-sm"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                <span
                  className={`text-xs ${
                    msg.role === "user" ? "text-blue-100" : "text-slate-500"
                  }`}
                >
                  {msg.timestamp.toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="message-bubble rounded-lg bg-white px-4 py-2 shadow-sm">
                <div className="flex items-center gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]"></span>
                  <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]"></span>
                  <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400"></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Custom input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a custom test message..."
            disabled={isLoading}
            className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            aria-label="Custom test message input"
          />
          <Button
            onClick={() => {
              if (inputValue.trim()) {
                sendMessage(inputValue);
                setInputValue("");
              }
            }}
            disabled={isLoading || !inputValue.trim()}
            aria-label="Send custom test message"
          >
            Send
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
