/**
 * Live Preview Panel - Interactive Demo of Selected Mode
 *
 * Shows users a live preview of what they're building:
 * - General mode: Interactive chat widget demo
 * - Ecommerce mode: Shopping preview with product cards
 * - Real-time updates as users select options
 * - Fully interactive (not just static)
 */

import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { MessageCircle, ShoppingCart, Bot, Store, Play } from "lucide-react";
import { OnboardingMode } from "../../types/onboarding";

export interface LivePreviewPanelProps {
  mode: OnboardingMode | null;
  className?: string;
}

export function LivePreviewPanel({
  mode,
  className = "",
}: LivePreviewPanelProps): React.ReactElement {
  const prefersReducedMotion = useReducedMotion();
  const [isPlaying, setIsPlaying] = React.useState(false);

  if (!mode) {
    return (
      <div
        className={`bg-white/5 rounded-2xl p-8 border border-white/10 flex items-center justify-center min-h-[400px] ${className}`}
      >
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-white/10 flex items-center justify-center mx-auto">
            <Play size={32} className="text-white/40" />
          </div>
          <p className="text-white/40 text-sm">Select an option to see a live preview</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={prefersReducedMotion ? {} : { opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: prefersReducedMotion ? 0 : 0.3 }}
      className={`bg-gradient-to-br from-white/10 to-white/5 rounded-2xl p-6 border border-white/10 ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white">Live Preview</h3>
        <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/20 rounded-full">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs text-emerald-400 font-bold">INTERACTIVE</span>
        </div>
      </div>

      {/* Preview Content */}
      <div className="bg-background rounded-xl overflow-hidden min-h-[320px]">
        {mode === "general" && <GeneralModePreview isPlaying={isPlaying} onPlay={setIsPlaying} />}
        {mode === "ecommerce" && <EcommerceModePreview isPlaying={isPlaying} onPlay={setIsPlaying} />}
      </div>

      {/* Caption */}
      <motion.p
        initial={prefersReducedMotion ? {} : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: prefersReducedMotion ? 0 : 0.2 }}
        className="text-center text-sm text-white/60 mt-4"
      >
        {mode === "general" && "Your assistant will answer customer questions 24/7"}
        {mode === "ecommerce" && "Customers can browse and buy products directly in chat!"}
      </motion.p>
    </motion.div>
  );
}

/**
 * General Mode Preview - Chat Widget Demo
 */
function GeneralModePreview({ isPlaying, onPlay }: { isPlaying: boolean; onPlay: (playing: boolean) => void }): React.ReactElement {
  const [messages, setMessages] = React.useState<
    Array<{ role: "user" | "assistant"; content: string }>
  >([
    { role: "assistant", content: "Hi! 👋 How can I help you today?" },
  ]);

  const handlePlay = () => {
    if (isPlaying) return;

    onPlay(true);

    // Simulate conversation
    setTimeout(() => {
      setMessages((prev) => [...prev, { role: "user", content: "What are your business hours?" }]);
    }, 800);

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "We're open Monday-Friday 9am-6pm! 🕐" },
      ]);
      onPlay(false);
    }, 2000);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-emerald-500 to-cyan-500 p-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
          <Bot size={20} className="text-white" />
        </div>
        <div>
          <p className="text-white font-bold text-sm">Your Assistant</p>
          <p className="text-white/80 text-xs">Online now</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 p-4 space-y-3 bg-background">
        {messages.map((msg, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] px-4 py-2 rounded-2xl ${
                msg.role === "user"
                  ? "bg-emerald-500 text-black"
                  : "bg-white/10 text-white"
              }`}
            >
              <p className="text-sm">{msg.content}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Input Area (demo only) */}
      <div className="p-4 bg-white/5 border-t border-white/10">
        <button
          onClick={handlePlay}
          disabled={isPlaying}
          className="w-full py-3 bg-emerald-500 hover:bg-emerald-400 disabled:bg-white/10 text-black font-bold rounded-xl transition-all flex items-center justify-center gap-2"
        >
          {isPlaying ? (
            <>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <MessageCircle size={16} />
              </motion.div>
              Typing...
            </>
          ) : (
            <>
              <Play size={16} />
              Try it out - Click to see demo
            </>
          )}
        </button>
      </div>
    </div>
  );
}

/**
 * Ecommerce Mode Preview - Shopping Demo
 */
function EcommerceModePreview({ isPlaying, onPlay }: { isPlaying: boolean; onPlay: (playing: boolean) => void }): React.ReactElement {
  const [showCart, setShowCart] = React.useState(false);
  const [addedToCart, setAddedToCart] = React.useState(false);

  const handlePlay = () => {
    if (isPlaying) return;
    onPlay(true);
    setShowCart(true);

    setTimeout(() => {
      setAddedToCart(true);
      onPlay(false);
    }, 1500);
  };

  return (
    <div className="flex flex-col h-full relative">
      {/* Shopping Header */}
      <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Store size={20} className="text-white" />
          <p className="text-white font-bold text-sm">Your Store</p>
        </div>
        <motion.div
          animate={showCart ? { scale: [1, 1.2, 1] } : {}}
          onClick={() => setShowCart(!showCart)}
          className="relative cursor-pointer"
        >
          <ShoppingCart size={20} className="text-white" />
          {addedToCart && (
            <span className="absolute -top-2 -right-2 w-5 h-5 bg-white rounded-full text-purple-500 text-xs font-bold flex items-center justify-center">
              1
            </span>
          )}
        </motion.div>
      </div>

      {/* Product Grid */}
      <div className="flex-1 p-4 bg-background">
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4].map((idx) => (
            <motion.div
              key={idx}
              whileHover={{ scale: 1.05 }}
              className="bg-white/10 rounded-xl p-3 border border-white/10"
            >
              <div className="aspect-square bg-white/5 rounded-lg mb-2 flex items-center justify-center">
                <Store size={24} className="text-white/30" />
              </div>
              <p className="text-white text-xs font-bold truncate">Product {idx}</p>
              <p className="text-emerald-400 text-xs font-bold">${(idx * 29).toFixed(2)}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Demo Button */}
      <div className="p-4 bg-white/5 border-t border-white/10">
        <button
          onClick={handlePlay}
          disabled={isPlaying}
          className="w-full py-3 bg-purple-500 hover:bg-purple-400 disabled:bg-white/10 text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2"
        >
          {isPlaying ? (
            "Adding to cart..."
          ) : addedToCart ? (
            <>
              <ShoppingCart size={16} />
              Cart updated! 🛒
            </>
          ) : (
            <>
              <Play size={16} />
              Try it out - Click to shop
            </>
          )}
        </button>
      </div>

      {/* Cart Slide-out */}
      {showCart && (
        <motion.div
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          className="absolute inset-0 bg-background/95 backdrop-blur-sm border-l border-white/10 p-4"
        >
          <h4 className="text-white font-bold mb-3">Your Cart</h4>
          {addedToCart ? (
            <div className="space-y-3">
              <div className="flex gap-3 p-3 bg-white/10 rounded-lg">
                <div className="w-12 h-12 bg-white/10 rounded-lg" />
                <div className="flex-1">
                  <p className="text-white text-sm font-bold">Product 1</p>
                  <p className="text-emerald-400 text-xs font-bold">$29.00</p>
                </div>
              </div>
              <div className="border-t border-white/10 pt-3">
                <div className="flex justify-between text-sm">
                  <span className="text-white/60">Total</span>
                  <span className="text-white font-bold">$29.00</span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-white/40 text-sm">Your cart is empty</p>
          )}
        </motion.div>
      )}
    </div>
  );
}
