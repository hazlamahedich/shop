import React from 'react';
import { Search, MoreVertical, Paperclip, Smile, Send } from 'lucide-react';

const Conversations = () => {
  return (
    <div className="flex h-[calc(100vh-8rem)] bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      {/* Left Pane: Chat List */}
      <div className="w-1/3 border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search chats..."
              className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${i === 1 ? 'bg-blue-50' : ''}`}
            >
              <div className="flex justify-between items-start mb-1">
                <h4
                  className={`font-medium text-sm ${i === 1 ? 'text-gray-900' : 'text-gray-700'}`}
                >
                  John Doe
                </h4>
                <span className="text-xs text-gray-400">2m</span>
              </div>
              <p className="text-xs text-gray-500 truncate">
                I'm looking for running shoes under $100.
              </p>
              {i === 1 && (
                <span className="inline-block px-2 py-0.5 bg-blue-100 text-blue-700 text-[10px] font-medium rounded-full mt-2">
                  Active
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Right Pane: Chat Thread */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="h-16 px-6 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium">
              JD
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-900">John Doe</h3>
              <p className="text-xs text-green-500 flex items-center">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1"></span> Active now
              </p>
            </div>
          </div>
          <button className="text-gray-400 hover:text-gray-600">
            <MoreVertical size={20} />
          </button>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50/50">
          {/* User Message */}
          <div className="flex items-end justify-end space-x-2">
            <div className="max-w-md">
              <div className="bg-primary text-white px-4 py-2 rounded-2xl rounded-tr-sm text-sm">
                I need running shoes under $100.
              </div>
              <span className="text-[10px] text-gray-400 mt-1 block text-right">10:42 AM</span>
            </div>
          </div>

          {/* Bot Message with Product Card */}
          <div className="flex items-end justify-start space-x-2">
            <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-primary text-xs font-bold">
              B
            </div>
            <div className="max-w-xs">
              <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm overflow-hidden p-3 space-y-3">
                <div className="h-32 bg-gray-100 rounded-lg flex items-center justify-center text-gray-400 text-xs">
                  Product Image
                </div>
                <div>
                  <h4 className="font-medium text-sm text-gray-900">Nike Air Zoom Pegasus</h4>
                  <p className="text-xs text-gray-500 mt-0.5">Men's Road Running Shoes</p>
                  <p className="font-bold text-gray-900 mt-2">$89.99</p>
                </div>
                <button className="w-full py-2 bg-primary text-white text-xs font-medium rounded-lg hover:bg-blue-700 transition-colors">
                  Add to Cart
                </button>
              </div>
              <span className="text-[10px] text-gray-400 mt-1 block">10:42 AM</span>
            </div>
          </div>
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-gray-200">
          <div className="flex items-center space-x-2 mb-3">
            {['Check Status', 'Talk to Human'].map((reply) => (
              <button
                key={reply}
                className="px-3 py-1 bg-blue-50 text-primary text-xs font-medium rounded-full hover:bg-blue-100 transition-colors"
              >
                {reply}
              </button>
            ))}
          </div>
          <div className="flex items-center space-x-2">
            <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full">
              <Paperclip size={20} />
            </button>
            <div className="flex-1 relative">
              <input
                type="text"
                placeholder="Type a message..."
                className="w-full pl-4 pr-10 py-2 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary text-sm"
              />
              <button className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                <Smile size={20} />
              </button>
            </div>
            <button className="p-2 bg-primary text-white rounded-full hover:bg-blue-700 transition-colors">
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Conversations;
