/** HelpMenu component.

Dropdown menu with help links including "Start Tutorial".
Supports keyboard shortcut Cmd/Ctrl + Shift + T.
*/

import * as React from "react";
import { Book, HelpCircle, Keyboard, RotateCcw } from "lucide-react";
import { useTutorialStore } from "../../stores/tutorialStore";
import { useNavigate } from "react-router-dom";

export interface HelpMenuProps {
  className?: string;
}

export function HelpMenu({ className = "" }: HelpMenuProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const { startTutorial, resetTutorial } = useTutorialStore();
  const navigate = useNavigate();
  const menuRef = React.useRef<HTMLDivElement>(null);

  // Toggle menu
  const toggleMenu = () => setIsOpen((prev) => !prev);

  // Close menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [menuRef]);

  // Keyboard shortcut: Cmd/Ctrl + Shift + T
  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key === "t") {
        event.preventDefault();
        startTutorial();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [startTutorial]);

  const handleStartTutorial = () => {
    startTutorial();
    setIsOpen(false);
  };

  const handleResetTutorial = async () => {
    const confirmed = window.confirm(
      "This will reset your tutorial progress. You can restart the tutorial anytime. Continue?"
    );
    if (confirmed) {
      await resetTutorial();
      setIsOpen(false);
    }
  };

  const handleDocs = () => {
    navigate("/docs");
    setIsOpen(false);
  };

  return (
    <div className={`help-menu ${className}`} ref={menuRef}>
      <button
        onClick={toggleMenu}
        className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        aria-label="Open help menu"
        aria-expanded={isOpen}
      >
        <HelpCircle className="h-5 w-5" />
        <span className="hidden sm:inline text-sm font-medium">Help</span>
      </button>

      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50"
          role="menu"
        >
          {/* Start Tutorial */}
          <button
            onClick={handleStartTutorial}
            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
            role="menuitem"
          >
            <Book className="h-4 w-4 mr-3" />
            <div className="text-left">
              <div className="font-medium">Start Tutorial</div>
              <div className="text-xs text-gray-500">Interactive walkthrough</div>
            </div>
          </button>

          {/* Replay Tutorial */}
          <button
            onClick={handleResetTutorial}
            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
            role="menuitem"
          >
            <RotateCcw className="h-4 w-4 mr-3" />
            <div className="text-left">
              <div className="font-medium">Replay Tutorial</div>
              <div className="text-xs text-gray-500">Reset and start over</div>
            </div>
          </button>

          {/* Keyboard Shortcuts */}
          <button
            onClick={() => {}}
            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors cursor-default"
            role="menuitem"
            disabled
          >
            <Keyboard className="h-4 w-4 mr-3" />
            <div className="text-left">
              <div className="font-medium">Keyboard Shortcuts</div>
              <div className="text-xs text-gray-500">
                <kbd className="mx-1 px-1 py-0.5 bg-gray-100 rounded text-xs">⌘⇧T</kbd> to start tutorial
              </div>
            </div>
          </button>

          <hr className="my-2 border-gray-200" />

          {/* Documentation */}
          <button
            onClick={handleDocs}
            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
            role="menuitem"
          >
            <Book className="h-4 w-4 mr-3" />
            <span className="font-medium">Documentation</span>
          </button>
        </div>
      )}
    </div>
  );
}
