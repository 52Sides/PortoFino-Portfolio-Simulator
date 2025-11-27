import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import api from "@/api/client";
import { subscribeToReportWS } from "@/api/events";

interface HistoryItem {
  id: number;
  created_at: string;
  command: string;
  cagr: number | null;
  sharpe: number | null;
  max_drawdown: number | null;
}

interface SimulationDetail {
  id: number;
  created_at: string;
  command: string;
  portfolio_value: Record<string, number>;
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState<SimulationDetail | null>(null);
  const [reportLoading, setReportLoading] = useState<number | null>(null);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const resp = await api.get("/history/", { params: { page, page_size: pageSize } });
      setHistory(resp.data.root || []);
      setTotal(resp.data.total || 0);
    } catch (err) {
      console.error(err);
      alert("Failed to load simulation history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadHistory(); }, [page, pageSize]);

  const fetchSimulationDetail = async (id: number) => {
    try {
      const resp = await api.get(`/history/${id}`);
      setSelected(resp.data);
    } catch (err) {
      console.error(err);
      alert("Failed to load simulation details.");
    }
  };

  const generateReport = async (simulationId: number) => {
    setReportLoading(simulationId);
    try {
      const resp = await api.post("/report/", { simulation_id: Number(simulationId) });
      const ws = subscribeToReportWS(resp.data.task_id, (event) => {
        if (event.status === "done" && event.download_url) {
          const a = document.createElement("a");
          a.href = event.download_url;
          a.download = `report_${simulationId}.xlsx`;
          a.click();
          setReportLoading(null);
          ws.close();
        } else if (event.status === "failed") {
          console.error("Report generation failed");
          alert("Report generation failed.");
          setReportLoading(null);
          ws.close();
        }
      });
    } catch (err) {
      console.error(err);
      alert("Failed to initiate report generation.");
      setReportLoading(null);
    }
  };

  const PageButton = ({
    children,
    onClick,
    disabled
  }: { children: React.ReactNode; onClick: () => void; disabled?: boolean }) => (
    <button
      onClick={onClick}
      disabled={disabled}
      className="px-3 py-1 rounded border border-[var(--border)] bg-[var(--surface)] transition-colors disabled:opacity-50"
    >
      {children}
    </button>
  );

  const totalPages = Math.ceil(total / pageSize);

  const safeMetric = (value: number | null | undefined, digits = 3) =>
    value != null ? value.toFixed(digits) : "-";

  const safePercent = (value: number | null | undefined) =>
    value != null ? (value * 100).toFixed(2) + "%" : "-";

  return (
    <main className="max-w-5xl mx-auto px-4 py-10 w-full">
      <h1 className="text-2xl font-semibold mb-6 text-center text-[var(--text)]">
        Simulation History
      </h1>

      <div className="rounded-xl shadow-lg border border-[var(--border)] p-6 transition-colors bg-[var(--surface)]">
        <div className="flex justify-between mb-4">
          <div>
            <label className="text-[var(--text-muted)] mr-2">Page size:</label>
            <select
              value={pageSize}
              onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
              className="border border-[var(--border)] rounded px-2 py-1 bg-[var(--surface)] text-[var(--text)]"
            >
              {[10, 20, 50, 100].map(size =>
                <option key={size} value={size}>{size}</option>
              )}
            </select>
          </div>
          <div className="text-[var(--text-muted)]">Total: {total}</div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left border-b border-[var(--border)] text-[var(--text-muted)]">
              <tr>
                <th className="p-2">Date</th>
                <th className="p-2">Command</th>
                <th className="p-2">CAGR</th>
                <th className="p-2">Sharpe</th>
                <th className="p-2">Max DD</th>
                <th className="p-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-6 text-[var(--text-muted)]">
                    Loading...
                  </td>
                </tr>
              ) : history.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-6 text-[var(--text-muted)]">
                    No simulations yet
                  </td>
                </tr>
              ) : (
                history.map(item => (
                  <tr
                    key={item.id}
                    className="border-b border-[var(--border)] hover:bg-[var(--surface)] transition-colors"
                  >
                    <td className="p-2 text-[var(--text)]">
                      {new Date(item.created_at).toLocaleString()}
                    </td>

                    <td className="p-2 font-mono text-xs text-[var(--text)]">
                      {item.command}
                    </td>

                    <td className="p-2 text-[var(--text)]">
                      {safeMetric(item.cagr)}
                    </td>

                    <td className="p-2 text-[var(--text)]">
                      {safeMetric(item.sharpe)}
                    </td>

                    <td className="p-2 text-[var(--text)]">
                      {safePercent(item.max_drawdown)}
                    </td>

                    <td className="p-2 text-right">
                      <button
                        onClick={() => fetchSimulationDetail(item.id)}
                        className="mr-2 px-2 py-1 text-[var(--accent)] underline"
                      >
                        View
                      </button>

                      <button
                        onClick={() => generateReport(item.id)}
                        className="px-2 py-1 text-[var(--accent)] underline"
                        disabled={reportLoading === item.id}
                      >
                        {reportLoading === item.id ? "Generating..." : "Download"}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="flex justify-between items-center mt-4 text-[var(--text)]">
          <PageButton onClick={() => setPage(p => p - 1)} disabled={page <= 1}>
            Prev
          </PageButton>

          <div className="text-[var(--text-muted)]">
            Page {page} / {totalPages}
          </div>

          <PageButton onClick={() => setPage(p => p + 1)} disabled={page >= totalPages}>
            Next
          </PageButton>
        </div>
      </div>

      {selected && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
          <div className="bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] rounded-xl shadow-lg p-6 w-[480px] max-w-full transition-colors">
            <h2 className="text-xl font-semibold mb-4">Simulation Details</h2>

            <p className="text-sm text-[var(--text-muted)] mb-1">
              {new Date(selected.created_at).toLocaleString()}
            </p>

            <div className="font-mono text-sm p-3 rounded border border-[var(--border)] mb-4 bg-[var(--surface)]">
              {selected.command}
            </div>

            <Plot
              data={[{
                x: Object.keys(selected.portfolio_value),
                y: Object.values(selected.portfolio_value),
                type: "scatter",
                mode: "lines",
                line: { color: "var(--accent)", width: 2 },
                hovertemplate: "%{y:.2f} USD<br>%{x}<extra></extra>"
              }]}
              layout={{
                margin: { l: 40, r: 20, t: 10, b: 40 },
                autosize: true,
                plot_bgcolor: "var(--surface)",
                paper_bgcolor: "var(--surface)",
                font: { color: "var(--text)" }
              }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: "100%", height: "300px" }}
            />

            <button
              onClick={() => { setSelected(null); loadHistory(); }}
              className="mt-6 w-full py-2 rounded-lg bg-[var(--accent)] text-[var(--btn-accent-text)] transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
