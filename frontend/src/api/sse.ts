const API_BASE = "/api/v1";

export interface SSEEvent {
  type:
    | "start"
    | "token"
    | "conclusion"
    | "text_response"
    | "complete"
    | "error";
  content?: string;
  data?: any;
  message?: string;
  timestamp?: string;
}

export type SSEEventHandler = (event: SSEEvent) => void;

export class SSEClient {
  private eventSource: EventSource | null = null;
  private controller: AbortController | null = null;

  streamProposal(
    proposal: string,
    category?: string,
    onEvent?: SSEEventHandler,
  ): Promise<any> {
    return new Promise((resolve, reject) => {
      const url = `${API_BASE}/council/stream`;

      // Use fetch with ReadableStream for better control
      fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "default_user",
          session_id: `session_${Date.now()}`,
          user_input: proposal,
          category: category || "general",
          action_type: "submit_proposal",
        }),
      })
        .then(async (response) => {
          if (!response.ok) {
            throw new Error(`SSE request failed: ${response.status}`);
          }

          const reader = response.body?.getReader();
          if (!reader) {
            throw new Error("ReadableStream not supported");
          }

          const decoder = new TextDecoder();
          let buffer = "";
          let fullContent = "";

          while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Parse SSE events from buffer
            const lines = buffer.split("\n");
            buffer = lines.pop() || ""; // Keep incomplete line in buffer

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                try {
                  const eventData: SSEEvent = JSON.parse(line.slice(6));

                  if (onEvent) {
                    onEvent(eventData);
                  }

                  // Accumulate content
                  if (eventData.type === "token" && eventData.content) {
                    fullContent += eventData.content;
                  } else if (
                    eventData.type === "conclusion" &&
                    eventData.data
                  ) {
                    resolve(eventData.data);
                    return;
                  } else if (eventData.type === "complete") {
                    resolve({ content: fullContent });
                    return;
                  } else if (eventData.type === "error") {
                    reject(new Error(eventData.message));
                    return;
                  }
                } catch (e) {
                  console.warn("[SSE] Failed to parse event:", e);
                }
              }
            }
          }
        })
        .catch((error) => {
          console.error("[SSE] Streaming failed:", error);
          reject(error);
        });
    });
  }

  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    if (this.controller) {
      this.controller.abort();
      this.controller = null;
    }
  }
}

export const sseClient = new SSEClient();
