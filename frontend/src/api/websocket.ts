import type { SeatState, VoteMap, CouncilConclusion } from "../types";

export type WebSocketEventType =
  | "connected"
  | "pong"
  | "ping"
  | "council_started"
  | "council_completed"
  | "step_started"
  | "step_completed"
  | "mode_changed"
  | "seat_prevote"
  | "knife_cut"
  | "round_started"
  | "round_completed"
  | "seat_speaking"
  | "bell_update"
  | "vote_update"
  | "conclusion"
  | "views_ready"
  | "safety_mode"
  | "error";

export interface WebSocketEvent {
  type: WebSocketEventType;
  payload: Record<string, any>;
}

export type WebSocketEventHandler = (event: WebSocketEvent) => void;

export class CouncilWebSocketClient {
  private ws: WebSocket | null = null;
  private sessionId: string | null = null;
  private eventHandlers: Map<WebSocketEventType, Set<WebSocketEventHandler>> =
    new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private pingInterval: number | null = null;

  constructor() {
    // Initialize event handler sets
    const eventTypes: WebSocketEventType[] = [
      "connected",
      "pong",
      "ping",
      "council_started",
      "council_completed",
      "step_started",
      "step_completed",
      "mode_changed",
      "seat_prevote",
      "knife_cut",
      "round_started",
      "round_completed",
      "seat_speaking",
      "bell_update",
      "vote_update",
      "conclusion",
      "views_ready",
      "safety_mode",
      "error",
    ];
    eventTypes.forEach((type) => this.eventHandlers.set(type, new Set()));
  }

  connect(sessionId: string): Promise<void> {
    this.sessionId = sessionId;
    this.reconnectAttempts = 0;

    return new Promise((resolve, reject) => {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/council/${sessionId}`;

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log(`[WebSocket] Connected to session ${sessionId}`);
        this.reconnectAttempts = 0;
        this.startPingInterval();
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const data: WebSocketEvent = JSON.parse(event.data);
          this.handleEvent(data);
        } catch (error) {
          console.error("[WebSocket] Failed to parse message:", error);
        }
      };

      this.ws.onclose = (event) => {
        console.log(
          `[WebSocket] Disconnected: code=${event.code}, reason=${event.reason}`,
        );
        this.stopPingInterval();
        this.handleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error("[WebSocket] Error:", error);
        reject(error);
      };
    });
  }

  disconnect(): void {
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnect
    this.stopPingInterval();
    if (this.ws) {
      this.ws.close(1000, "Client disconnected");
      this.ws = null;
    }
    this.sessionId = null;
  }

  on(eventType: WebSocketEventType, handler: WebSocketEventHandler): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.add(handler);
    }
  }

  off(eventType: WebSocketEventType, handler: WebSocketEventHandler): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  clearHandlers(eventType: WebSocketEventType): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.clear();
    }
  }

  clearAllHandlers(): void {
    this.eventHandlers.forEach((handlers) => handlers.clear());
  }

  private handleEvent(event: WebSocketEvent): void {
    const handlers = this.eventHandlers.get(event.type);
    if (handlers) {
      handlers.forEach((handler) => handler(event));
    }
  }

  private handleReconnect(): void {
    if (
      this.reconnectAttempts >= this.maxReconnectAttempts ||
      !this.sessionId
    ) {
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(
      `[WebSocket] Reconnecting attempt ${this.reconnectAttempts} in ${delay}ms`,
    );

    setTimeout(() => {
      if (this.sessionId) {
        this.connect(this.sessionId).catch((err) => {
          console.error("[WebSocket] Reconnection failed:", err);
        });
      }
    }, delay);
  }

  private startPingInterval(): void {
    this.pingInterval = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000); // Send ping every 30 seconds
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Global singleton instance
export const councilWebSocketClient = new CouncilWebSocketClient();
