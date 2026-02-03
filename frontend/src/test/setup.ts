/// <reference types="vitest/globals" />
import "@testing-library/jest-dom";
import { cleanup } from "@testing-library/react";
import { afterEach, vi, beforeEach } from "vitest";

// Mock localStorage before any tests run
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  clear: vi.fn(),
  removeItem: vi.fn(),
  length: 0,
  key: vi.fn(),
};

// Mock window and localStorage only in browser environment
if (typeof window !== 'undefined') {
  Object.defineProperty(window, "localStorage", {
    value: localStorageMock,
    writable: true,
  });
}

// Track all intervals for cleanup
const activeIntervals = new Set<ReturnType<typeof setInterval>>();

// Override setInterval to track active intervals
const originalSetInterval = global.setInterval;
global.setInterval = ((handler: Function, delay?: number, ...args: any[]) => {
  const id = originalSetInterval(handler, delay ?? 0, ...args);
  activeIntervals.add(id);
  return id;
}) as any;

// Override clearInterval to remove from tracking
const originalClearInterval = global.clearInterval;
global.clearInterval = ((id: ReturnType<typeof setInterval>) => {
  activeIntervals.delete(id);
  return originalClearInterval(id);
}) as any;

beforeEach(() => {
  // Reset all mocks before each test
  vi.clearAllMocks();
});

afterEach(() => {
  // Clean up all active intervals to prevent memory leaks and errors
  activeIntervals.forEach(id => {
    try {
      originalClearInterval(id);
    } catch (e) {
      // Ignore errors during cleanup
    }
  });
  activeIntervals.clear();
  cleanup();
});
