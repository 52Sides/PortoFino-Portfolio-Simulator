import { useState, useEffect, useRef } from "react";
import { subscribeToSimulationWS } from "@/api/events";
import type { SimulationEvent } from "@/api/events";
import axios, { AxiosError } from 'axios';
import Plot from "react-plotly.js";
import api from "./api/client";
import MetricCard from "./components/MetricCard";


function App() {
  const [command, setCommand] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState<{
    cagr: number;
    sharpe: number;
    max_drawdown: number;
  } | null>(null);
  const [portfolio, setPortfolio] = useState<Record<string, number> | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const wsRef = useRef<{ close: () => void } | null>(null);
  const taskStatusRef = useRef<"pending" | "done" | "error" | null>(null);

  useEffect(() => {
    if (!taskId) return;

    wsRef.current?.close();
    wsRef.current = null;

    setErrorMessage(null);
    setLoading(true);

    wsRef.current = subscribeToSimulationWS(taskId, (event: SimulationEvent) => {
      if (event.status === "done") {
        setMetrics({
          cagr: event.data.cagr,
          sharpe: event.data.sharpe,
          max_drawdown: event.data.max_drawdown,
        });
        setPortfolio(event.data.portfolio_value);
        setLoading(false);
        taskStatusRef.current = "done";
      } else if (event.status === "error") {
        setErrorMessage(event.message || "Simulation error");
        setLoading(false);
        taskStatusRef.current = "error";
      }
    });

    return () => wsRef.current?.close();
  }, [taskId]);

  const startSimulation = async () => {
    if (taskStatusRef.current === "pending") return;

    setLoading(true);
    setMetrics(null);
    setPortfolio(null);
    setErrorMessage(null);
    taskStatusRef.current = "pending";

    try {
      const resp = await api.post("/simulate/", { command });
      setTaskId(resp.data.task_id);
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        setErrorMessage(err.response?.data?.detail || err.message || "Simulation failed");
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Simulation failed");
      }
      setLoading(false);
      taskStatusRef.current = null;
    }
  };

  return (
    <div className="flex flex-col items-center justify-center px-4 py-10">
      <div className="w-full max-w-4xl bg-[var(--surface)] text-[var(--text)] rounded-2xl shadow-lg p-8 transition-colors">
        <h1 className="text-3xl font-bold text-center mb-2">
          PortoFino Portfolio Simulator
        </h1>
        <p className="text-center text-[var(--text-muted)] mb-6">
          Fast portfolio simulation web platform
        </p>

        <textarea
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          className="w-full border border-[var(--border)] rounded-lg p-3 text-sm text-[var(--text)] bg-[var(--surface)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition"
          rows={3}
          placeholder="Example: 'TSLA-L-20% AAPL-S-80% 2020-01-01 2021-01-01'. Up to 10 tickers, sum of weights must be 100%"
          disabled={loading}
        />

        {errorMessage && (
          <p className="text-red-500 text-sm mt-2 text-center">{errorMessage}</p>
        )}

        <button
          onClick={startSimulation}
          disabled={loading}
          className="mt-4 w-full py-3 font-medium rounded-lg shadow-md disabled:opacity-50 hover:bg-[var(--accent-hover)] transition-colors text-[var(--btn-accent-text)] bg-[var(--accent)]"
        >
          {loading ? "Running Simulation..." : "Simulate"}
        </button>

        {metrics && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center mt-6">
            <MetricCard label="CAGR" value={metrics.cagr.toFixed(3)} />
            <MetricCard label="Sharpe Ratio" value={metrics.sharpe.toFixed(3)} />
            <MetricCard
              label="Max Drawdown"
              value={`${(metrics.max_drawdown * 100).toFixed(2)}%`}
            />
          </div>
        )}

        {portfolio && (
          <div className="mt-8">
            <Plot
              data={[
                {
                  x: Object.keys(portfolio),
                  y: Object.values(portfolio),
                  type: "scatter",
                  mode: "lines",
                  line: { color: "var(--accent)", width: 2 },
                  hovertemplate: "%{y:.2f} USD<br>%{x}<extra></extra>",
                },
              ]}
              layout={{
                margin: { l: 40, r: 20, t: 10, b: 40 },
                autosize: true,
                plot_bgcolor: "var(--surface)",
                paper_bgcolor: "var(--surface)",
                font: { color: "var(--text)" },
              }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: "100%", height: "420px" }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
