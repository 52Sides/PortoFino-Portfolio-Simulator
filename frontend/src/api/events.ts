export type SimulationEvent =
  | {
      task_id: string;
      user_id: number;
      status: "done";
      data: {
        cagr: number;
        sharpe: number;
        max_drawdown: number;
        portfolio_value: Record<string, number>;
      };
    }
  | {
      task_id: string;
      user_id: number;
      status: "error";
      message: string;
    };

export type ReportEvent =
  | {
      task_id: string;
      status: "done";
      download_url: string | null;
    }
  | {
      task_id: string;
      status: "failed";
      download_url?: string;
    };

type EventCallback<T> = (event: T) => void;

/**
 * Connect to WebSocket for simulation
 */
export function subscribeToSimulationWS(
  task_id: string,
  onEvent: EventCallback<SimulationEvent>
) {
  const token = localStorage.getItem("access_token");
  const WS_URL =
    import.meta.env.VITE_API_URL?.replace(/^http/, "ws") +
    `/ws/simulations/${task_id}?token=${token}`;

  const socket = new WebSocket(WS_URL);

  socket.onopen = () => console.log(`Simulation WS connected: ${task_id}`);
  socket.onmessage = (msg) => {
    try {
      const event = JSON.parse(msg.data) as SimulationEvent;
      onEvent(event);

      // Close WS in the end
      if (event.status === "done" || event.status === "error") {
        socket.close();
      }
    } catch (e) {
      console.error("Invalid WS message:", e);
    }
  };

  socket.onclose = () => console.log(`Simulation WS closed: ${task_id}`);

  return {
    close: () => socket.close(),
  };
}

/**
 * Connect to WebSocket for report
 */
export function subscribeToReportWS(
  task_id: string,
  onEvent: EventCallback<ReportEvent>
) {
  const token = localStorage.getItem("access_token");
  const WS_URL =
    import.meta.env.VITE_API_URL?.replace(/^http/, "ws") +
    `/ws/reports/${task_id}?token=${token}`;

  const socket = new WebSocket(WS_URL);

  socket.onopen = () => console.log(`Report WS connected: ${task_id}`);
  socket.onmessage = (msg) => {
    try {
      const event = JSON.parse(msg.data) as ReportEvent;
      onEvent(event);

      // Close WS in the end
      if (event.status === "done" || event.status === "failed") {
        socket.close();
      }
    } catch (e) {
      console.error("Invalid WS message:", e);
    }
  };

  socket.onclose = () => console.log(`Report WS closed: ${task_id}`);

  return {
    close: () => socket.close(),
  };
}
