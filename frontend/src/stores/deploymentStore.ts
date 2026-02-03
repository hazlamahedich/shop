/** Deployment Zustand Store.
 *
 * Manages deployment state with localStorage persistence.
 * Tracks deployment progress, logs, and status.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Platform = "flyio" | "railway" | "render";
export type DeploymentStatus = "pending" | "in-progress" | "success" | "failed" | "cancelled";

export interface DeploymentLog {
  timestamp: string;
  level: "info" | "warning" | "error";
  step?: string;
  message: string;
}

export interface DeploymentState {
  // State
  platform: Platform | null;
  deploymentId: string | null;
  merchantKey: string | null;
  status: DeploymentStatus;
  progress: number;
  logs: DeploymentLog[];
  currentStep: string | null;
  errorMessage: string | null;
  troubleshootingUrl: string | null;
  estimatedSeconds: number;

  // Actions
  setPlatform: (platform: Platform) => void;
  startDeployment: (platform: Platform) => Promise<void>;
  cancelDeployment: () => Promise<void>;
  pollDeploymentStatus: (deploymentId: string) => () => void; // Returns cleanup function
  updateDeploymentStatus: (data: {
    deploymentId: string;
    merchantKey: string;
    status: DeploymentStatus;
    progress: number;
    logs: DeploymentLog[];
    currentStep?: string;
    errorMessage?: string;
    troubleshootingUrl?: string;
  }) => void;
  addLog: (log: DeploymentLog) => void;
  reset: () => void;
}

const initialState = {
  platform: null,
  deploymentId: null,
  merchantKey: null,
  status: "pending" as DeploymentStatus,
  progress: 0,
  logs: [],
  currentStep: null,
  errorMessage: null,
  troubleshootingUrl: null,
  estimatedSeconds: 900,
};

export const useDeploymentStore = create<DeploymentState>()(
  persist(
    (set, get) => ({
      ...initialState,

      setPlatform: (platform) => set({ platform }),

      startDeployment: async (platform: Platform) => {
        set({ platform, status: "pending", progress: 0, logs: [] });

        try {
          const response = await fetch("/api/deployment/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ platform }),
          });

          if (!response.ok) {
            throw new Error(`Failed to start deployment: ${response.statusText}`);
          }

          const data = await response.json();
          set({
            deploymentId: data.data.deploymentId,
            merchantKey: data.data.merchantKey,
            status: data.data.status,
            estimatedSeconds: data.data.estimatedSeconds,
          });

          // Start polling for status updates
          get().pollDeploymentStatus(data.data.deploymentId);
        } catch (error) {
          set({
            status: "failed",
            errorMessage: error instanceof Error ? error.message : "Unknown error",
          });
        }
      },

      pollDeploymentStatus: async (deploymentId: string) => {
        const pollInterval = setInterval(async () => {
          try {
            const response = await fetch(`/api/deployment/status/${deploymentId}`);
            if (!response.ok) {
              clearInterval(pollInterval);
              return;
            }

            const data = await response.json();
            const deployment = data.data;

            set({
              status: deployment.status,
              progress: deployment.progress || 0,
              logs: deployment.logs || [],
              currentStep: deployment.currentStep || null,
              errorMessage: deployment.errorMessage || null,
              troubleshootingUrl: deployment.troubleshootingUrl || null,
            });

            // Stop polling if deployment is complete
            if (
              deployment.status === "success" ||
              deployment.status === "failed" ||
              deployment.status === "cancelled"
            ) {
              clearInterval(pollInterval);
            }
          } catch (error) {
            clearInterval(pollInterval);
            set({
              status: "failed",
              errorMessage: error instanceof Error ? error.message : "Failed to fetch deployment status",
            });
          }
        }, 2000);

        // Return cleanup function to prevent memory leak
        return () => clearInterval(pollInterval);
      },

      cancelDeployment: async () => {
        const { deploymentId } = get();
        if (!deploymentId) return;

        try {
          const response = await fetch(`/api/deployment/cancel/${deploymentId}`, {
            method: "POST",
          });

          if (!response.ok) {
            throw new Error(`Failed to cancel deployment: ${response.statusText}`);
          }

          set({ status: "cancelled" });
        } catch (error) {
          set({
            errorMessage: error instanceof Error ? error.message : "Failed to cancel deployment",
          });
        }
      },

      updateDeploymentStatus: (data) => set(data),

      addLog: (log) => set((state) => ({ logs: [...state.logs, log] })),

      reset: () => set(initialState),
    }),
    {
      name: "shop-deployment-storage",
      partialize: (state) => ({
        platform: state.platform,
        deploymentId: state.deploymentId,
        merchantKey: state.merchantKey,
      }),
    }
  )
);
