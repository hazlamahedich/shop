/** Tests for deployment Zustand store.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch as any;

// Mock localStorage for persistence tests
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
} as any;

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

describe("deploymentStore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    // Reset mock implementations
    mockFetch.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
    localStorageMock.clear.mockClear();
  });

  describe("initial state", () => {
    it("has initial state", async () => {
      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      expect(result.current.platform).toBeNull();
      expect(result.current.status).toBe("pending");
      expect(result.current.progress).toBe(0);
      expect(result.current.logs).toEqual([]);
      expect(result.current.estimatedSeconds).toBe(900);
    });

    it("persists selected platform to localStorage", async () => {
      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      act(() => {
        result.current.setPlatform("flyio");
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "shop-deployment-storage",
        JSON.stringify({
          platform: "flyio",
          deploymentId: null,
          merchantKey: null,
        })
      );
    });
  });

  describe("setPlatform action", () => {
    it("sets platform and persists to localStorage", async () => {
      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      act(() => {
        result.current.setPlatform("railway");
      });

      expect(result.current.platform).toBe("railway");
      expect(result.current.status).toBe("pending");
      expect(result.current.progress).toBe(0);
      expect(localStorageMock.setItem).toHaveBeenCalled();
    });

    it("handles all platform types", async () => {
      const { useDeploymentStore } = await import("./deploymentStore");
      const platforms = ["flyio", "railway", "render"] as const;

      platforms.forEach(platform => {
        const { result } = renderHook(() => useDeploymentStore());
        
        act(() => {
          result.current.setPlatform(platform);
        });

        expect(result.current.platform).toBe(platform);
      });
    });
  });

  describe("startDeployment action", () => {
    it("starts deployment and updates state", async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({
          data: {
            deploymentId: "test-deployment-123",
            merchantKey: "shop-test123",
            status: "pending",
            estimatedSeconds: 900,
          },
        }),
      };

      mockFetch.mockResolvedValueOnce(mockResponse);

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      await act(async () => {
        await result.current.startDeployment("flyio");
      });

      await waitFor(() => {
        expect(result.current.deploymentId).toBe("test-deployment-123");
        expect(result.current.merchantKey).toBe("shop-test123");
        expect(result.current.platform).toBe("flyio");
        expect(result.current.status).toBe("pending");
        expect(result.current.progress).toBe(0);
      });

      // Verify fetch was called with correct parameters
      expect(mockFetch).toHaveBeenCalledWith("/api/deployment/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform: "flyio" }),
      });
    });

    it("handles deployment start network error", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      await act(async () => {
        await result.current.startDeployment("railway");
      });

      await waitFor(() => {
        expect(result.current.status).toBe("failed");
        expect(result.current.errorMessage).toBe("Network error");
      });
    });

    it("handles deployment start HTTP error", async () => {
      const mockResponse = {
        ok: false,
        statusText: "Bad Request",
      };

      mockFetch.mockResolvedValueOnce(mockResponse);

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      await act(async () => {
        await result.current.startDeployment("railway");
      });

      await waitFor(() => {
        expect(result.current.status).toBe("failed");
        expect(result.current.errorMessage).toBe("Failed to start deployment: Bad Request");
      });
    });

    it("polls for deployment status after starting", async () => {
      const mockStartResponse = {
        ok: true,
        json: async () => ({
          data: {
            deploymentId: "test-deployment-123",
            merchantKey: "shop-test123",
            status: "pending",
            estimatedSeconds: 900,
          },
        }),
      };

      mockFetch.mockResolvedValueOnce(mockStartResponse);

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      // Start deployment
      await act(async () => {
        await result.current.startDeployment("flyio");
      });

      // Mock status response
      const mockStatusResponse = {
        ok: true,
        json: async () => ({
          data: {
            deploymentId: "test-deployment-123",
            merchantKey: "shop-test123",
            status: "in-progress",
            progress: 50,
            logs: [],
            currentStep: "deploy",
          },
        }),
      };

      mockFetch.mockResolvedValueOnce(mockStatusResponse);

      // Wait for polling to complete
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
      });

      expect(mockFetch).toHaveBeenCalledWith("/api/deployment/status/test-deployment-123");
    });
  });

  describe("pollDeploymentStatus action", () => {
    it("polls deployment status and returns cleanup function", async () => {
      const mockResponses = [
        // First poll - in progress
        {
          ok: true,
          json: async () => ({
            data: {
              deploymentId: "test-123",
              merchantKey: "shop-test",
              status: "in-progress",
              progress: 50,
              logs: [],
              currentStep: "deploy",
            },
          }),
        },
        // Second poll - complete
        {
          ok: true,
          json: async () => ({
            data: {
              deploymentId: "test-123",
              merchantKey: "shop-test",
              status: "success",
              progress: 100,
              logs: [],
            },
          }),
        },
      ];

      mockFetch.mockResolvedValue(mockResponses[0] as any);
      mockFetch.mockResolvedValue(mockResponses[1] as any);

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      // Store cleanup function
      let cleanup: (() => void) | undefined;

      await act(async () => {
        cleanup = await result.current.pollDeploymentStatus("test-123");
      });

      // Verify cleanup function is returned
      expect(cleanup).toBeDefined();
      expect(typeof cleanup).toBe("function");

      // Wait for first poll to complete
      await waitFor(
        () => {
          expect(mockFetch).toHaveBeenCalledWith(
            "/api/deployment/status/test-123"
          );
        },
        { timeout: 3000 }
      );

      // Test cleanup function clears the interval
      vi.useFakeTimers();
      const clearIntervalSpy = vi.spyOn(global, "clearInterval");
      cleanup?.();
      expect(clearIntervalSpy).toHaveBeenCalled();
      vi.useRealTimers();
    }, 10000);

    it("stops polling when deployment succeeds", async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({
          data: {
            deploymentId: "test-123",
            merchantKey: "shop-test",
            status: "success",
            progress: 100,
            logs: [],
          },
        }),
      };

      mockFetch.mockResolvedValue(mockResponse as any);

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      const cleanup = await act(async () => {
        return await result.current.pollDeploymentStatus("test-123");
      });

      await waitFor(() => {
        expect(result.current.status).toBe("success");
        expect(result.current.progress).toBe(100);
      });

      // Verify interval was cleared after success
      vi.useFakeTimers();
      const clearIntervalSpy = vi.spyOn(global, "clearInterval");
      cleanup?.();
      expect(clearIntervalSpy).toHaveBeenCalled();
      vi.useRealTimers();
    });

    it("stops polling when deployment fails", async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({
          data: {
            deploymentId: "test-123",
            merchantKey: "shop-test",
            status: "failed",
            progress: 50,
            logs: [],
            errorMessage: "Deployment failed",
          },
        }),
      };

      mockFetch.mockResolvedValue(mockResponse as any);

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      const cleanup = await act(async () => {
        return await result.current.pollDeploymentStatus("test-123");
      });

      await waitFor(() => {
        expect(result.current.status).toBe("failed");
        expect(result.current.errorMessage).toBe("Deployment failed");
      });

      // Verify interval was cleared after failure
      vi.useFakeTimers();
      const clearIntervalSpy = vi.spyOn(global, "clearInterval");
      cleanup?.();
      expect(clearIntervalSpy).toHaveBeenCalled();
      vi.useRealTimers();
    });

    it("handles polling errors", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Polling failed"));

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      const cleanup = await act(async () => {
        return await result.current.pollDeploymentStatus("test-123");
      });

      await waitFor(() => {
        expect(result.current.status).toBe("failed");
        expect(result.current.errorMessage).toBe("Failed to fetch deployment status");
      });

      // Verify interval was cleared on error
      vi.useFakeTimers();
      const clearIntervalSpy = vi.spyOn(global, "clearInterval");
      cleanup?.();
      expect(clearIntervalSpy).toHaveBeenCalled();
      vi.useRealTimers();
    });
  });

  describe("cancelDeployment action", () => {
    it("cancels deployment", async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({
          data: {
            message: "Deployment cancelled",
            deploymentId: "test-deployment-123",
          },
        }),
      };

      mockFetch.mockResolvedValueOnce(mockResponse);

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      // Set a deployment ID first
      act(() => {
        result.current.updateDeploymentStatus({
          deploymentId: "test-deployment-123",
          merchantKey: "shop-test",
          status: "in-progress" as const,
          progress: 50,
          logs: [],
        });
      });

      await act(async () => {
        await result.current.cancelDeployment();
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          "/api/deployment/cancel/test-deployment-123",
          expect.objectContaining({
            method: "POST",
          })
        );
        expect(result.current.status).toBe("cancelled");
      });
    });

    it("handles cancellation error", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Cancellation failed"));

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      // Set a deployment ID first
      act(() => {
        result.current.updateDeploymentStatus({
          deploymentId: "test-deployment-123",
          merchantKey: "shop-test",
          status: "in-progress" as const,
          progress: 50,
          logs: [],
        });
      });

      await act(async () => {
        await result.current.cancelDeployment();
      });

      await waitFor(() => {
        expect(result.current.status).toBe("in-progress"); // Should remain unchanged
        expect(result.current.errorMessage).toBe("Cancellation failed");
      });
    });

    it("does nothing if no deployment ID", async () => {
      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      await act(async () => {
        await result.current.cancelDeployment();
      });

      expect(mockFetch).not.toHaveBeenCalled();
      expect(result.current.status).toBe("pending");
    });
  });

  describe("updateDeploymentStatus action", () => {
    it("updates deployment status with all properties", async () => {
      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      const statusUpdate = {
        deploymentId: "test-123",
        merchantKey: "shop-test",
        status: "in-progress" as const,
        progress: 75,
        logs: [
          {
            timestamp: "2026-02-03T12:00:00Z",
            level: "info" as const,
            message: "Deployment in progress",
          },
        ],
        currentStep: "deploy",
        errorMessage: null,
        troubleshootingUrl: null,
      };

      act(() => {
        result.current.updateDeploymentStatus(statusUpdate);
      });

      expect(result.current.deploymentId).toBe("test-123");
      expect(result.current.merchantKey).toBe("shop-test");
      expect(result.current.status).toBe("in-progress");
      expect(result.current.progress).toBe(75);
      expect(result.current.logs).toEqual(statusUpdate.logs);
      expect(result.current.currentStep).toBe("deploy");
      expect(result.current.errorMessage).toBe(null);
      expect(result.current.troubleshootingUrl).toBe(null);
    });
  });

  describe("addLog action", () => {
    it("adds log entry", async () => {
      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      const log = {
        timestamp: "2026-02-03T12:00:00Z",
        level: "info" as const,
        message: "Test log message",
      };

      act(() => {
        result.current.addLog(log);
      });

      expect(result.current.logs).toHaveLength(1);
      expect(result.current.logs[0]).toEqual(log);
    });

    it("adds multiple log entries", async () => {
      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      const log1 = {
        timestamp: "2026-02-03T12:00:00Z",
        level: "info" as const,
        message: "Log 1",
      };

      const log2 = {
        timestamp: "2026-02-03T12:01:00Z",
        level: "warning" as const,
        message: "Log 2",
      };

      act(() => {
        result.current.addLog(log1);
        result.current.addLog(log2);
      });

      expect(result.current.logs).toHaveLength(2);
      expect(result.current.logs[0]).toEqual(log1);
      expect(result.current.logs[1]).toEqual(log2);
    });

    it("preserves existing logs when adding new ones", async () => {
      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      // Add initial log
      const initialLog = {
        timestamp: "2026-02-03T12:00:00Z",
        level: "info" as const,
        message: "Initial log",
      };

      act(() => {
        result.current.addLog(initialLog);
      });

      // Add new log
      const newLog = {
        timestamp: "2026-02-03T12:01:00Z",
        level: "error" as const,
        message: "Error occurred",
      };

      act(() => {
        result.current.addLog(newLog);
      });

      expect(result.current.logs).toHaveLength(2);
      expect(result.current.logs[0]).toBe(initialLog);
      expect(result.current.logs[1]).toBe(newLog);
    });
  });

  describe("reset action", () => {
    it("resets state to initial values", async () => {
      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      // Set some state
      act(() => {
        result.current.setPlatform("render");
        result.current.updateDeploymentStatus({
          deploymentId: "test-123",
          merchantKey: "shop-test",
          status: "success" as const,
          progress: 100,
          logs: [],
        });
      });

      // Reset
      act(() => {
        result.current.reset();
      });

      expect(result.current.platform).toBeNull();
      expect(result.current.deploymentId).toBeNull();
      expect(result.current.merchantKey).toBeNull();
      expect(result.current.status).toBe("pending");
      expect(result.current.progress).toBe(0);
      expect(result.current.logs).toEqual([]);
      expect(result.current.errorMessage).toBeNull();
      expect(result.current.troubleshootingUrl).toBeNull();
      expect(result.current.estimatedSeconds).toBe(900);
    });

    it("does not clear localStorage on reset", async () => {
      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      // Set platform (which persists to localStorage)
      act(() => {
        result.current.setPlatform("flyio");
      });

      // Reset
      act(() => {
        result.current.reset();
      });

      // localStorage should still contain the persisted platform
      expect(localStorageMock.setItem).toHaveBeenCalled();
    });
  });

  describe("persistence", () => {
    it("persists only specified state to localStorage", async () => {
      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      // Set some state
      act(() => {
        result.current.setPlatform("flyio");
        result.current.updateDeploymentStatus({
          deploymentId: "test-123",
          merchantKey: "shop-test",
          status: "success" as const,
          progress: 100,
          logs: [
            {
              timestamp: "2026-02-03T12:00:00Z",
              level: "info" as const,
              message: "Deployment complete",
            },
          ],
        });
      });

      // Check what was persisted
      const persistCall = localStorageMock.setItem.mock.calls[0];
      const persistedData = JSON.parse(persistCall[1]);
      
      expect(persistedData).toEqual({
        platform: "flyio",
        deploymentId: "test-123",
        merchantKey: "shop-test",
      });

      // Verify non-persisted fields are not in localStorage
      expect(persistedData.status).toBeUndefined();
      expect(persistedData.progress).toBeUndefined();
      expect(persistedData.logs).toBeUndefined();
    });

    it("loads persisted state on initialization", async () => {
      // Set up persisted data
      const persistedState = {
        platform: "railway",
        deploymentId: "test-deployment-456",
        merchantKey: "shop-persisted",
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify(persistedState));

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      expect(result.current.platform).toBe("railway");
      expect(result.current.deploymentId).toBe("test-deployment-456");
      expect(result.current.merchantKey).toBe("shop-persisted");
    });

    it("handles malformed persisted state", async () => {
      localStorageMock.getItem.mockReturnValue("invalid json");

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      // Should still work with default state
      expect(result.current.platform).toBeNull();
      expect(result.current.deploymentId).toBeNull();
      expect(result.current.merchantKey).toBeNull();
    });
  });

  describe("edge cases", () => {
    it("handles rapid polling calls", async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({
          data: {
            deploymentId: "test-123",
            merchantKey: "shop-test",
            status: "in-progress",
            progress: 50,
            logs: [],
          },
        }),
      };

      mockFetch.mockResolvedValue(mockResponse as any);

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      // Start multiple polling calls
      const cleanup1 = await act(async () => {
        return await result.current.pollDeploymentStatus("test-123");
      });

      const cleanup2 = await act(async () => {
        return await result.current.pollDeploymentStatus("test-123");
      });

      // Both should return cleanup functions
      expect(cleanup1).toBeDefined();
      expect(cleanup2).toBeDefined();

      // Clean up both
      vi.useFakeTimers();
      const clearIntervalSpy = vi.spyOn(global, "clearInterval");
      cleanup1?.();
      cleanup2?.();
      expect(clearIntervalSpy).toHaveBeenCalledTimes(2);
      vi.useRealTimers();
    });

    it("handles deployment status transitions correctly", async () => {
      const transitions = [
        { status: "pending", progress: 0 },
        { status: "in-progress", progress: 25 },
        { status: "in-progress", progress: 50 },
        { status: "in-progress", progress: 75 },
        { status: "success", progress: 100 },
      ];

      mockFetch.mockImplementation(async () => ({
        ok: true,
        json: async () => ({
          data: {
            deploymentId: "test-123",
            merchantKey: "shop-test",
            status: transitions[0].status,
            progress: transitions[0].progress,
            logs: [],
          },
        }),
      }));

      const { useDeploymentStore } = await import("./deploymentStore");
      const { result } = renderHook(() => useDeploymentStore());

      // Start polling
      await act(async () => {
        await result.current.pollDeploymentStatus("test-123");
      });

      // Simulate status updates
      for (let i = 1; i < transitions.length; i++) {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            data: {
              deploymentId: "test-123",
              merchantKey: "shop-test",
              status: transitions[i].status,
              progress: transitions[i].progress,
              logs: [],
            },
          }),
        });

        await act(async () => {
          await new Promise(resolve => setTimeout(resolve, 50));
        });

        expect(result.current.status).toBe(transitions[i].status);
        expect(result.current.progress).toBe(transitions[i].progress);
      }
    });
  });
});
