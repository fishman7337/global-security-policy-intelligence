import React, { useEffect, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import Plot from "react-plotly.js";
import {
  Activity,
  BarChart3,
  Bot,
  Brain,
  Database,
  GitBranch,
  Landmark,
  LineChart,
  Map as MapIcon,
  Network,
  ShieldCheck,
  Sparkles
} from "lucide-react";
import { getJson, postJson } from "./api";
import "./styles.css";

type Summary = {
  rows: number;
  year_min: number;
  year_max: number;
  countries: number;
  regions: number;
  total_fatalities: number;
  total_wounded: number;
  success_rate: number;
  aggregate_policy: string;
};

type Distribution = { label: string; count: number };
type Trend = { period: string; group: string; attacks: number; fatalities: number; wounded: number };
type ChatResponse = { answer: string; citations: Array<{ title: string; source: string }>; safe: boolean };

const sections = [
  { id: "overview", label: "Overview", icon: Activity },
  { id: "quality", label: "Spark Quality", icon: Database },
  { id: "geo", label: "Hotspots", icon: MapIcon },
  { id: "forecast", label: "Forecasts", icon: LineChart },
  { id: "models", label: "ML Lab", icon: Brain },
  { id: "policy", label: "Policy Research", icon: Landmark },
  { id: "clusters", label: "Clusters", icon: GitBranch },
  { id: "graph", label: "Graph", icon: Network },
  { id: "chat", label: "RAG Chat", icon: Bot },
  { id: "complexity", label: "DSA", icon: BarChart3 },
  { id: "ethics", label: "Ethics", icon: ShieldCheck }
];

function useApi<T>(path: string, fallback: T): T {
  const [data, setData] = useState<T>(fallback);
  useEffect(() => {
    getJson<T>(path).then(setData).catch(() => setData(fallback));
  }, [path]);
  return data;
}

function App() {
  const [active, setActive] = useState("overview");
  const summary = useApi<Summary>("/api/summary", {
    rows: 0,
    year_min: 0,
    year_max: 0,
    countries: 0,
    regions: 0,
    total_fatalities: 0,
    total_wounded: 0,
    success_rate: 0,
    aggregate_policy: "Aggregate-only historical analysis."
  });
  const distributions = useApi<Record<string, Distribution[]>>("/api/analytics/distributions", {});
  const trends = useApi<Trend[]>("/api/analytics/trends", []);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Sparkles size={24} />
          <div>
            <strong>GTD Capstone</strong>
            <span>AI systems lab</span>
          </div>
        </div>
        <nav>
          {sections.map((section) => {
            const Icon = section.icon;
            return (
              <button
                key={section.id}
                className={active === section.id ? "active" : ""}
                onClick={() => setActive(section.id)}
                title={section.label}
              >
                <Icon size={18} />
                <span>{section.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>
      <main>
        <header className="topbar">
          <div>
            <h1>Historical Aggregate Intelligence Dashboard</h1>
            <p>{summary.aggregate_policy}</p>
          </div>
          <div className="status-pill">W&B tracked · MCP ready · Spark pipeline</div>
        </header>
        {active === "overview" && <Overview summary={summary} distributions={distributions} trends={trends} />}
        {active === "quality" && <Quality />}
        {active === "geo" && <Hotspots />}
        {active === "forecast" && <Forecasts />}
        {active === "models" && <Models />}
        {active === "policy" && <PolicyResearch />}
        {active === "clusters" && <Clusters />}
        {active === "graph" && <Graph />}
        {active === "chat" && <Chat />}
        {active === "complexity" && <Complexity />}
        {active === "ethics" && <Ethics />}
      </main>
    </div>
  );
}

function Overview({
  summary,
  distributions,
  trends
}: {
  summary: Summary;
  distributions: Record<string, Distribution[]>;
  trends: Trend[];
}) {
  const yearly = useMemo(() => {
    const totals = new globalThis.Map<string, number>();
    trends.forEach((row) => totals.set(row.period, (totals.get(row.period) || 0) + row.attacks));
    return Array.from(totals.entries()).sort(([a], [b]) => a.localeCompare(b)) as Array<[string, number]>;
  }, [trends]);
  const attackTypes = distributions.attack_types || [];
  return (
    <section className="content-grid">
      <Metric label="Rows" value={summary.rows.toLocaleString()} />
      <Metric label="Coverage" value={`${summary.year_min}-${summary.year_max}`} />
      <Metric label="Countries" value={summary.countries.toLocaleString()} />
      <Metric label="Fatalities" value={Math.round(summary.total_fatalities).toLocaleString()} />
      <div className="panel wide">
        <h2>Global Attack Trend</h2>
        <Plot
          data={[{ x: yearly.map(([year]) => year), y: yearly.map(([, count]) => count), type: "scatter", mode: "lines", line: { color: "#2563eb", width: 3 } }] as any}
          layout={plotLayout("Attacks by Year") as any}
          config={{ responsive: true, displayModeBar: false }}
          className="plot"
        />
      </div>
      <div className="panel">
        <h2>Top Attack Types</h2>
        <Plot
          data={[{ x: attackTypes.map((item) => item.count), y: attackTypes.map((item) => item.label), type: "bar", orientation: "h", marker: { color: "#e11d48" } }] as any}
          layout={plotLayout("") as any}
          config={{ responsive: true, displayModeBar: false }}
          className="plot"
        />
      </div>
    </section>
  );
}

function Quality() {
  const quality = useApi<any>("/api/data-quality", {});
  const contract = useApi<any>("/api/data-contract", {});
  return <JsonPanel title="Spark Bronze/Silver/Gold Data Quality and Contract" data={{ quality, contract }} />;
}

function Hotspots() {
  const hotspots = useApi<any[]>("/api/geo/hotspots?min_events=1", []);
  return (
    <section className="panel full">
      <h2>Aggregated Hotspots</h2>
      <Plot
        data={[{ type: "scattergeo", lat: hotspots.map((h) => h.latitude), lon: hotspots.map((h) => h.longitude), text: hotspots.map((h) => `${h.name}: ${h.attacks} attacks`), marker: { size: hotspots.map((h) => Math.max(6, Math.log(h.attacks + 1) * 5)), color: hotspots.map((h) => h.severity_score), colorscale: "Viridis", showscale: true } }] as any}
        layout={{ ...plotLayout("Aggregate Hotspots"), geo: { projection: { type: "natural earth" }, showland: true } } as any}
        config={{ responsive: true }}
        className="plot tall"
      />
    </section>
  );
}

function Forecasts() {
  const forecasts = useApi<any[]>("/api/forecasts?horizon=6", []);
  return <JsonPanel title="Forecast Lab" data={forecasts.slice(0, 30)} />;
}

function Models() {
  const models = useApi<any[]>("/api/models", []);
  return <JsonPanel title="ML and Deep Learning Model Lab" data={{ models, prediction_endpoint: "POST /api/predict/severity" }} />;
}

function PolicyResearch() {
  const summary = useApi<any>("/api/policy/panel-summary", {});
  const results = useApi<any>("/api/policy/results", { models: [] });
  const eventStudy = useApi<any>("/api/policy/event-study", { points: [] });
  const estimated = (results.models || []).filter((row: any) => row.status === "estimated");
  const skipped = (results.models || []).filter((row: any) => row.status !== "estimated");
  const sources = summary.sources || [];
  return (
    <section className="policy-grid">
      <Metric label="Panel Rows" value={(summary.rows || 0).toLocaleString()} />
      <Metric label="Countries" value={(summary.countries || 0).toLocaleString()} />
      <Metric label="Window" value={`${summary.year_min || 1996}-${summary.year_max || 2021}`} />
      <Metric label="Complete Cases" value={(summary.complete_case_rows || 0).toLocaleString()} />
      <div className="panel wide">
        <h2>Governance Capacity Coefficients</h2>
        <Plot
          data={[{
            x: estimated.map((row: any) => row.coefficient),
            y: estimated.map((row: any) => row.outcome),
            error_x: {
              type: "data",
              symmetric: false,
              array: estimated.map((row: any) => row.conf_high - row.coefficient),
              arrayminus: estimated.map((row: any) => row.coefficient - row.conf_low)
            },
            type: "scatter",
            mode: "markers",
            marker: { color: "#0f766e", size: 12 }
          }] as any}
          layout={{ ...plotLayout("Lagged Governance Capacity"), shapes: [{ type: "line", x0: 0, x1: 0, y0: -1, y1: estimated.length, line: { color: "#64748b", width: 1 } }] } as any}
          config={{ responsive: true, displayModeBar: false }}
          className="plot"
        />
      </div>
      <div className="panel">
        <h2>Source Coverage</h2>
        <div className="source-list">
          {sources.slice(0, 8).map((source: any) => (
            <div key={source.name}>
              <strong>{source.name}</strong>
              <span>{source.tier}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="panel wide">
        <h2>Regime Event Study</h2>
        <Plot
          data={[{
            x: (eventStudy.points || []).map((row: any) => row.relative_year),
            y: (eventStudy.points || []).map((row: any) => row.mean_outcome),
            type: "scatter",
            mode: "lines+markers",
            line: { color: "#7c3aed", width: 3 }
          }] as any}
          layout={plotLayout(eventStudy.status === "estimated" ? "Severity Burden Around Regime Events" : "V-Dem Event Data Not Loaded") as any}
          config={{ responsive: true, displayModeBar: false }}
          className="plot"
        />
      </div>
      <div className="panel">
        <h2>Research Design</h2>
        <p>{results.research_design || summary.causal_language}</p>
        <p>{summary.aggregate_policy}</p>
        {skipped.length > 0 && <pre>{JSON.stringify(skipped, null, 2)}</pre>}
      </div>
      <JsonPanel title="Policy Panel Summary" data={{ summary: { ...summary, sources: undefined }, limitations: results.limitations }} />
    </section>
  );
}

function Clusters() {
  const clusters = useApi<any[]>("/api/clusters", []);
  return <JsonPanel title="Clustering Lab" data={clusters} />;
}

function Graph() {
  const centrality = useApi<any[]>("/api/graph/centrality", []);
  const communities = useApi<any[]>("/api/graph/communities", []);
  const gds = useApi<any[]>("/api/graph/gds-playbook", []);
  return <JsonPanel title="Graph Analytics" data={{ centrality: centrality.slice(0, 10), communities: communities.slice(0, 5), neo4j_gds: gds }} />;
}

function Chat() {
  const [question, setQuestion] = useState("How does the project use W&B and RAG safely?");
  const [answer, setAnswer] = useState<ChatResponse | null>(null);
  const evaluation = useApi<any>("/api/rag/evaluation", {});
  return (
    <section className="panel full">
      <h2>RAG Chatbot</h2>
      <div className="chat-row">
        <input value={question} onChange={(event) => setQuestion(event.target.value)} />
        <button onClick={() => postJson<ChatResponse>("/api/chat", { question }).then(setAnswer)}>Ask</button>
      </div>
      {answer && (
        <div className="answer">
          <p>{answer.answer}</p>
          <strong>Citations</strong>
          <ul>{answer.citations.map((c) => <li key={c.source}>{c.title} · {c.source}</li>)}</ul>
        </div>
      )}
      <h2 className="section-subhead">RAG Evaluation</h2>
      <pre>{JSON.stringify(evaluation, null, 2)}</pre>
    </section>
  );
}

function Complexity() {
  const complexity = useApi<any>("/api/complexity", {});
  const drift = useApi<any>("/api/monitoring/drift", {});
  return <JsonPanel title="Data Structures, Algorithms, and Drift Monitoring" data={{ complexity, drift }} />;
}

function Ethics() {
  return (
    <section className="panel full prose">
      <h2>Responsible AI Policy</h2>
      <p>This capstone supports historical, aggregate, educational analysis. The app avoids operational advice, tactical prediction, target recommendations, weaponization, and evasion guidance.</p>
      <p>Geospatial outputs are aggregated by default and model predictions are framed as analytical demonstrations with uncertainty and limitations.</p>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function JsonPanel({ title, data }: { title: string; data: unknown }) {
  return (
    <section className="panel full">
      <h2>{title}</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </section>
  );
}

function plotLayout(title: string) {
  return {
    title: title ? { text: title } : undefined,
    autosize: true,
    margin: { l: 40, r: 20, t: title ? 45 : 15, b: 40 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: "Inter, system-ui, sans-serif", color: "#172033" }
  };
}

ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
