import { useCallback, useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  Brain,
  Check,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Download,
  Eye,
  FileText,
  Flame,
  Gauge,
  GitBranch,
  Home,
  LayoutDashboard,
  Link,
  Loader2,
  MessageCircle,
  Minus,
  Play,
  Plus,
  RefreshCw,
  Search,
  Send,
  Settings,
  Sparkles,
  Target,
  Terminal,
  Trophy,
  Upload,
  Zap,
} from "lucide-react";

/* ── Study Flow Logo SVG ── */
function StudyFlowLogo({ size = 40 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="sfGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#06b6d4" />
        </linearGradient>
      </defs>
      <rect width="48" height="48" rx="12" fill="url(#sfGrad)" />
      {/* Open book base */}
      <path d="M10 34 C10 34, 18 30, 24 30 C30 30, 38 34, 38 34" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" fill="none" />
      <path d="M24 30 L24 18" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" />
      {/* Flowing S-curve (knowledge flow) */}
      <path d="M18 26 C18 22, 24 24, 24 20 C24 16, 30 18, 30 14" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" fill="none" />
      {/* Arrow tip at top of flow */}
      <path d="M28 16 L30 14 L32 16" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      {/* Small sparkle */}
      <circle cx="34" cy="12" r="1.5" fill="#fbbf24" />
      <circle cx="14" cy="16" r="1" fill="#a5f3fc" />
    </svg>
  );
}

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/* ───── tiny helpers ───── */
function JsonBlock({ data }) {
  if (!data) return null;
  return <pre className="json-block">{JSON.stringify(data, null, 2)}</pre>;
}

/* ───── App ───── */
export default function App() {
  /* ── navigation ── */
  const [view, setView] = useState("dashboard");
  const [devMode, setDevMode] = useState(false);

  /* ── core state ── */
  const [userId]         = useState("demo-user");
  const [goal, setGoal]  = useState("Learn Machine Learning");
  const [hasResources, setHasResources] = useState(false);
  const [loading, setLoading]   = useState("");
  const [error, setError]       = useState("");
  const [lastAction, setLastAction]   = useState(null);
  const [lastResult, setLastResult]   = useState(null);
  const [roadmap, setRoadmap]         = useState(null);
  const [diagnostic, setDiagnostic]   = useState(null);
  const [broadAnswers, setBroadAnswers] = useState({});
  const [drillAnswers, setDrillAnswers] = useState({});
  const [profile, setProfile] = useState({
    format_preference: ["video"],
    daily_hours: 2,
    deadline_style: "flexible",
    goal_specificity: "project",
  });
  const [url, setUrl]               = useState("");
  const [sourceType, setSourceType] = useState("auto");
  const [resourceText, setResourceText]       = useState("");
  const [resourceCard, setResourceCard]       = useState(null);
  const [confirmedResource, setConfirmedResource] = useState(null);
  const [sourceId, setSourceId] = useState("");
  const [quiz, setQuiz]         = useState(null);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [chatInput, setChatInput]     = useState("");
  const [chatMessages, setChatMessages] = useState([]);

  /* ── knowledge graph interaction state ── */
  const [graphZoom, setGraphZoom]           = useState(100);
  const [selectedNode, setSelectedNode]     = useState(null);

  /* ── API helper (unchanged logic) ── */
  async function routeAction(actionType, payload = {}, label = actionType) {
    setLoading(label);
    setError("");
    setLastAction({ action_type: actionType, payload });
    try {
      const res = await fetch(`${API}/api/route-action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, action_type: actionType, payload }),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.detail || "Backend request failed");
      setLastResult(data.result);
      if (data.result?.roadmap) setRoadmap(data.result.status === "confirmed" ? data.result.roadmap : data.result);
      if (data.result?.questions) setDiagnostic(data.result);
      if (data.result?.phase === "phase_2_complete") setDiagnostic(data.result);
      if (actionType === "add_resource") setResourceCard(data.result);
      if (actionType === "confirm_resource") setConfirmedResource(data.result);
      if (actionType === "mark_source_complete") setQuiz(data.result);
      return data.result;
    } catch (e) {
      setError(e.message);
      return null;
    } finally {
      setLoading("");
    }
  }

  async function extractUrl() {
    if (!url.trim()) return setError("Paste a URL first.");
    setLoading("extract-url");
    setError("");
    try {
      const res = await fetch(`${API}/api/extract/url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, source_type: sourceType }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Could not extract URL content");
      setResourceText(data.content);
      await routeAction("add_resource", { content: data.content, source_type: data.source_type }, "add-resource");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading("");
    }
  }

  async function extractPdf(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setLoading("extract-pdf");
    setError("");
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await fetch(`${API}/api/extract/pdf`, { method: "POST", body });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Could not extract PDF content");
      setResourceText(data.content);
      await routeAction("add_resource", { content: data.content, source_type: "pdf" }, "add-resource");
    } catch (e) {
      setError(e.message);
    } finally {
      event.target.value = "";
      setLoading("");
    }
  }

  function submitBroadDiagnostic() {
    const answers = (diagnostic?.questions || []).map((q) => ({
      topic: q.text,
      level: broadAnswers[q.id] || "somewhat",
    }));
    routeAction("onboarding_answers", { goal, phase: "phase_2_drill_down", answers }, "diagnostic");
  }

  function submitDrillDiagnostic() {
    const answers = (diagnostic?.questions || []).map((q, i) => ({
      topic: q.topic || q.text,
      question: q.text,
      answer: drillAnswers[i] || "",
    }));
    routeAction("onboarding_answers", { goal, phase: "phase_2_score", answers }, "diagnostic");
  }

  async function submitProfile() {
    const data = await routeAction("onboarding_answers", { goal, phase: "phase_3_learning_profile", answers: profile }, "diagnostic");
    if (data && data.roadmap) {
      setView("roadmap");
    }
  }

  function submitQuiz() {
    const questions = quiz?.questions || [];
    const answers = questions.map((q) => quizAnswers[q.id] || "");
    routeAction("submit_quiz", { source_id: sourceId, questions, answers }, "submit-quiz");
  }

  async function sendChat() {
    if (!chatInput.trim()) return;
    const msg = chatInput.trim();
    setChatInput("");
    setChatMessages((m) => [...m, { role: "user", content: msg }]);
    const reply = await routeAction("chat_message", { message: msg }, "chat");
    if (reply) setChatMessages((m) => [...m, { role: "assistant", content: String(reply) }]);
  }

  /* ── derive roadmap phases for the sidebar widget ── */
  const phases = useMemo(() => {
    const weeks = roadmap?.roadmap || [];
    if (!weeks.length) {
      return [
        { title: "Fundamentals", status: "completed" },
        { title: "Core Concepts", status: "in_progress" },
        { title: "Advanced Topics", status: "upcoming" },
        { title: "Build & Deploy", status: "locked" },
      ];
    }
    return weeks.map((w, i) => ({
      title: w.milestone || w.project || `Week ${w.week || i + 1}`,
      status: i === 0 ? "completed" : i === 1 ? "in_progress" : "upcoming",
    }));
  }, [roadmap]);

  /* ── knowledge graph nodes — REAL topic names ── */
  const graphNodes = useMemo(() => {
    const weeks = roadmap?.roadmap || [];
    const topics = weeks.flatMap((w) => w.topics || []).slice(0, 7);
    const fallback = [
      "Data Structures", "Arrays", "Trees", "Graphs",
      "Linked Lists", "Stacks", "Sorting",
    ];
    const labels = topics.length >= 3 ? topics : fallback;

    const positions = [
      { x: 390, y: 195 }, // center — largest
      { x: 275, y: 100 }, // top-left
      { x: 510, y: 85 },  // top-right
      { x: 180, y: 210 }, // left
      { x: 580, y: 200 }, // right
      { x: 300, y: 310 }, // bottom-left
      { x: 500, y: 310 }, // bottom-right
    ];

    const states  = ["strong", "learning", "strong", "weak", "learning", "decaying", "strong"];
    const colors  = { strong: "#7bd7c4", learning: "#818cf8", weak: "#ee5d65", decaying: "#94a3b8" };
    const sizes   = { strong: 48, learning: 40, weak: 32, decaying: 36 };

    return labels.slice(0, 7).map((topic, i) => {
      const state = states[i] || "learning";
      const pos   = positions[i] || { x: 390, y: 200 };
      return {
        id: i,
        label: topic.length > 14 ? topic.slice(0, 13) + "…" : topic,
        full: topic,
        state,
        x: pos.x,
        y: pos.y,
        color: colors[state],
        r: i === 0 ? 56 : sizes[state],
      };
    });
  }, [roadmap]);

  const graphEdges = useMemo(() => {
    if (graphNodes.length < 2) return [];
    const center = graphNodes[0];
    return graphNodes.slice(1).map((n) => ({ x1: center.x, y1: center.y, x2: n.x, y2: n.y }));
  }, [graphNodes]);

  /* ── sidebar nav items ── */
  const navItems = [
    { id: "dashboard",   label: "Dashboard",    icon: Home },
    { id: "onboarding",  label: "Onboarding",   icon: Sparkles },
    { id: "roadmap",     label: "Roadmap",       icon: ClipboardList },
    { id: "resources",   label: "Resources",     icon: BookOpen },
    { id: "diagnostics", label: "Diagnostics",   icon: Brain },
    { id: "quizzes",     label: "Quizzes",       icon: ClipboardList },
    { id: "coach",       label: "Coach",         icon: MessageCircle },
    { id: "insights",    label: "Insights",      icon: Zap },
    { id: "portfolio",   label: "Portfolio",     icon: Trophy },
    { id: "settings",    label: "Settings",      icon: Settings },
  ];

  /* ─────────────────────────────────────── JSX ─────────────────────────────────────── */
  return (
    <div className="shell">
      {/* ── SIDEBAR ── */}
      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="brand-block">
            <StudyFlowLogo size={40} />
            <div>
              <strong>Study Flow</strong>
              <small>Powered by Cognee</small>
            </div>
          </div>

          <nav className="nav-list">
            {navItems.map((n) => (
              <button
                key={n.id}
                className={`nav-item${view === n.id ? " active" : ""}`}
                onClick={() => setView(n.id)}
              >
                <n.icon size={18} />
                <span>{n.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Cognee Memory Health — replaces "Upgrade to Pro" */}
        <div className="memory-health">
          <div className="mh-icon"><GitBranch size={20} /></div>
          <strong>Cognee Memory Health</strong>
          <p>Knowledge graph active. {graphNodes.length} topics indexed.</p>
          <div className="mh-bar"><div className="mh-fill" style={{ width: "78%" }} /></div>
          <small>78% graph coverage</small>
        </div>

        <div className="sidebar-user">
          <div className="avatar">S</div>
          <div>
            <strong>Shashank</strong>
            <small>Learner</small>
          </div>
        </div>
      </aside>

      {/* ── MAIN ── */}
      <main className="main">
        {/* ── TOP BAR ── */}
        <header className="topbar">
          <div>
            <h1 className="greeting">Good morning, Shashank!</h1>
            <p className="greeting-sub">Here's your personalized learning overview for today.</p>
          </div>
          <div className="topbar-actions">
            <div className="search-box">
              <Search size={15} />
              <input placeholder="Search anything..." />
              <kbd>⌘K</kbd>
            </div>
            <button className={`icon-btn${devMode ? " active" : ""}`} title="Toggle Dev Mode" onClick={() => setDevMode(!devMode)}><Terminal size={18} /></button>
            <button className="icon-btn notif" aria-label="Notifications"><Bell size={18} /><span className="notif-dot">4</span></button>
            <button className="btn primary" onClick={() => setView("resources")}><Plus size={16} /> Add Resource</button>
          </div>
        </header>

        {error && <div className="error-banner">{error}</div>}

        {/* ─── DASHBOARD VIEW ─── */}
        {view === "dashboard" && (
          <>
            {/* stat cards */}
            <section className="stat-row">
              {[
                { Icon: Flame, label: "Learning Streak", value: "—", sub: "Start learning!", color: "#f59e0b" },
                { Icon: CheckCircle, label: "Topics Mastered", value: roadmap?.roadmap?.length || "—", sub: "from roadmap", color: "#22c55e" },
                { Icon: ClipboardList, label: "Quizzes Taken", value: "—", sub: "take your first quiz", color: "#6366f1" },
                { Icon: Target, label: "Overall Progress", value: "—", sub: "begin onboarding", color: "#06b6d4" },
              ].map((s) => (
                <div className="stat-card" key={s.label}>
                  <span className="stat-icon" style={{ background: `${s.color}14`, color: s.color }}><s.Icon size={22} /></span>
                  <div>
                    <small>{s.label}</small>
                    <strong>{s.value}</strong>
                    <span className="stat-sub">{s.sub}</span>
                  </div>
                </div>
              ))}
            </section>

            {/* middle row */}
            <section className="mid-grid">
              {/* Your Roadmap */}
              <div className="card">
                <div className="card-head">
                  <h2>Your Roadmap</h2>
                  <button className="link-btn" onClick={() => setView("roadmap")}>View Full Roadmap →</button>
                </div>
                <div className="phase-list">
                  {phases.slice(0, 4).map((p, i) => (
                    <div className={`phase-row ${p.status}`} key={i}>
                      <span className="phase-dot" />
                      <div>
                        <strong>Phase {i + 1}</strong>
                        <span>{p.title}</span>
                      </div>
                      <span className={`phase-badge ${p.status}`}>
                        {p.status === "completed" ? "Completed" : p.status === "in_progress" ? "In Progress" : p.status === "upcoming" ? "Upcoming" : "Locked"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Knowledge Graph */}
              <div className="card graph-panel">
                <div className="card-head">
                  <h2>Knowledge Graph</h2>
                  <span className="badge interactive">Interactive</span>
                </div>
                <div className="graph-viewport">
                  <svg
                    viewBox="0 0 780 420"
                    style={{ transform: `scale(${graphZoom / 100})`, transformOrigin: "center" }}
                  >
                    {/* grid dots */}
                    <defs>
                      <pattern id="dots" width="30" height="30" patternUnits="userSpaceOnUse">
                        <circle cx="15" cy="15" r="1" fill="#dce5f1" />
                      </pattern>
                    </defs>
                    <rect width="780" height="420" fill="url(#dots)" />

                    {/* edges */}
                    {graphEdges.map((e, i) => (
                      <line key={i} x1={e.x1} y1={e.y1} x2={e.x2} y2={e.y2} stroke="#dce5f1" strokeWidth="2" />
                    ))}

                    {/* nodes */}
                    {graphNodes.map((n) => (
                      <g key={n.id} className="g-node" onClick={() => setSelectedNode(selectedNode?.id === n.id ? null : n)}>
                        <circle cx={n.x} cy={n.y} r={n.r} fill={n.color} opacity="0.85" />
                        <circle cx={n.x} cy={n.y} r={n.r} fill="none" stroke={n.color} strokeWidth="2" opacity="0.4" />
                        <text x={n.x} y={n.y + 4} textAnchor="middle" fontSize="12" fontWeight="600" fill="#1e293b">{n.label}</text>
                      </g>
                    ))}
                  </svg>

                  {/* tooltip */}
                  {selectedNode && (
                    <div className="graph-tooltip">
                      <span className="gt-dot" style={{ background: selectedNode.color }} />
                      <div>
                        <strong>{selectedNode.full}</strong>
                        <small>Status: {selectedNode.state}</small>
                      </div>
                    </div>
                  )}
                </div>
                <div className="graph-controls">
                  <button className="icon-btn sm" onClick={() => setGraphZoom(100)} title="Fit to view"><Home size={14} /></button>
                  <button className="icon-btn sm" onClick={() => setGraphZoom((z) => Math.max(50, z - 10))}><Minus size={14} /></button>
                  <span className="zoom-label">{graphZoom}%</span>
                  <button className="icon-btn sm" onClick={() => setGraphZoom((z) => Math.min(200, z + 10))}><Plus size={14} /></button>
                  <button className="icon-btn sm" title="Download graph"><Download size={14} /></button>
                </div>
              </div>

              {/* Today's Plan */}
              <div className="card">
                <div className="card-head"><h2>Today's Plan</h2></div>
                <div className="plan-list">
                  {(() => {
                    const hasRoadmap = roadmap?.roadmap && roadmap.roadmap.length > 0;
                    const tasks = hasRoadmap 
                      ? roadmap.roadmap[0].topics.slice(0, 4).map(t => ({ text: t, time: "45 min", done: false }))
                      : [
                          { text: "Start Onboarding", time: "5 min", done: false },
                          { text: "Add your first resource", time: "2 min", done: false },
                          { text: "Complete Diagnostic", time: "15 min", done: false },
                          { text: "Take first Quiz", time: "10 min", done: false },
                        ];
                    return tasks.map((t, i) => (
                      <div className="plan-item" key={i}>
                        <span className={`plan-check${t.done ? " done" : ""}`}>{t.done ? <Check size={14} /> : null}</span>
                        <span className="plan-text">{t.text}</span>
                        <span className="plan-time">{t.time}</span>
                      </div>
                    ));
                  })()}
                </div>
                {!roadmap?.roadmap ? (
                  <button className="btn primary full" onClick={() => setView("onboarding")}><Play size={15} /> Start Learning</button>
                ) : (
                  <button className="btn primary full" onClick={() => setView("roadmap")}><Play size={15} /> View Full Roadmap</button>
                )}
              </div>
            </section>

            {/* bottom row */}
            <section className="bot-grid">
              {/* Recent Activity */}
              <div className="card">
                <div className="card-head">
                  <h2>Recent Activity</h2>
                  <button className="link-btn">View All</button>
                </div>
                <div className="activity-list">
                  <p className="empty-hint">No activity yet. Start your learning journey!</p>
                </div>
              </div>

              {/* Weekly Comprehension */}
              <div className="card">
                <div className="card-head">
                  <h2>Weekly Comprehension</h2>
                  <button className="link-btn" onClick={() => setView("insights")}>View Analytics</button>
                </div>
                <div className="comp-chart">
                  <div className="comp-y">
                    {["100%", "75%", "50%", "25%", "0%"].map((l) => <span key={l}>{l}</span>)}
                  </div>
                  <div className="comp-bars">
                    {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => (
                      <div className="comp-col" key={d}>
                        <div className="comp-bar" style={{ height: "0%" }}><span className="comp-val">—</span></div>
                        <span className="comp-day">{d}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* AI Coach Tip */}
              <div className="card coach-tip">
                <div className="coach-avatar"><Bot size={32} strokeWidth={1.5} /></div>
                <strong>AI Coach Tip</strong>
                <p>Begin your journey! Set a learning goal via the Onboarding page to get your personalized roadmap.</p>
                <button className="btn outline" onClick={() => setView("coach")}><MessageCircle size={14} /> Chat with Coach</button>
              </div>
            </section>
          </>
        )}

        {/* ─── ONBOARDING VIEW ─── */}
        {view === "onboarding" && (
          <section className="view-panel">
            <div className="card wide-card">
              <h2>Onboarding</h2>
              <p className="muted">Set your learning goal and generate a personalized roadmap.</p>
              <label>Learning goal
                <input value={goal} onChange={(e) => setGoal(e.target.value)} />
              </label>
              <label className="toggle-row">
                <input type="checkbox" checked={hasResources} onChange={(e) => setHasResources(e.target.checked)} />
                <span>I already have learning resources</span>
              </label>

              {hasResources && (
                <div className="inline-resource" style={{ background: "#f8fafc", padding: 16, borderRadius: 8, marginTop: 12 }}>
                  <p className="muted" style={{ margin: "0 0 12px 0", fontSize: 14 }}>Add a YouTube playlist, Website, or PDF to base your roadmap on:</p>
                  
                  <div className="input-group" style={{ marginBottom: 12 }}>
                    <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}>
                      <option value="auto">Auto</option>
                      <option value="youtube">YouTube</option>
                      <option value="web">Website</option>
                    </select>
                    <input 
                      value={url} 
                      onChange={(e) => setUrl(e.target.value)} 
                      placeholder="Paste YouTube or article URL..." 
                      style={{ flex: 1 }}
                    />
                    <button className="btn primary" onClick={extractUrl} disabled={loading === "extract-url"}>
                      {loading === "extract-url" ? <Loader2 className="spin" size={16} /> : "Analyze"}
                    </button>
                  </div>
                  
                  <label className="file-upload" style={{ opacity: loading === "extract-pdf" ? 0.7 : 1, pointerEvents: loading === "extract-pdf" ? "none" : "auto" }}>
                    {loading === "extract-pdf" ? <Loader2 className="spin" size={17} /> : <Upload size={17} />}
                    <span>{loading === "extract-pdf" ? "Analyzing PDF..." : "Or Upload PDF"}</span>
                    <input type="file" accept="application/pdf" onChange={extractPdf} disabled={loading === "extract-pdf"} />
                  </label>

                  {resourceCard && (
                    <div className="resource-card" style={{ marginTop: 16 }}>
                      <div>
                        <small>{resourceCard.type}</small>
                        <h3>{resourceCard.title}</h3>
                        <p>{resourceCard.conflict_warning || "No conflicts detected."}</p>
                      </div>
                      <div className="chip-row">
                        <span className="chip">{resourceCard.estimated_time || 0} hours</span>
                        {(resourceCard.topics || []).slice(0, 4).map((t) => <span className="chip" key={t}>{t}</span>)}
                      </div>
                      
                      {/* Show snippet of extracted data */}
                      {resourceText && (
                        <div style={{ marginTop: 12, padding: 8, background: "#f1f5f9", borderRadius: 6, fontSize: 12, color: "#475569", maxHeight: 60, overflowY: "auto", fontFamily: "monospace" }}>
                          {typeof resourceText === "string" ? resourceText.substring(0, 300) + "..." : JSON.stringify(resourceText).substring(0, 300) + "..."}
                        </div>
                      )}

                      {!confirmedResource ? (
                        <button className="btn primary" disabled={!!loading} style={{ marginTop: 12 }} onClick={() => routeAction("confirm_resource", { card: resourceCard, full_content: resourceText }, "confirm_resource")}>
                          {loading === "confirm_resource" ? <Loader2 className="spin" size={16} /> : <Check size={16} />} Confirm Resource
                        </button>
                      ) : (
                        <div style={{ marginTop: 12 }}>
                          <p className="success" style={{ marginBottom: 8, fontSize: 14 }}>✅ Resource confirmed!</p>
                          <button className="btn outline" onClick={() => { setResourceCard(null); setResourceText(""); setConfirmedResource(null); setUrl(""); }}>
                            + Add Another Resource
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              <hr style={{ margin: "24px 0", borderTop: "1px solid #e2e8f0" }} />

              <h3 style={{ marginBottom: 16 }}>Prior Knowledge</h3>
              <div className="btn-row">
                <button className="btn primary" disabled={!!loading} onClick={() => routeAction("prior_knowledge_no", { goal }, "prior_knowledge_no")}>
                  {loading === "prior_knowledge_no" ? <Loader2 className="spin" size={16} /> : <Check size={16} />} No Prior Knowledge (Build Roadmap)
                </button>
                <button className="btn outline" disabled={!!loading} onClick={() => routeAction("prior_knowledge_yes", { goal }, "prior_knowledge_yes")}>
                  {loading === "prior_knowledge_yes" ? <Loader2 className="spin" size={16} /> : <Brain size={16} />} I have some prior knowledge (Test Me)
                </button>
              </div>

              {/* Phase 1 */}
              {diagnostic?.phase === "phase_1" && (
                <div className="diag-box">
                  <h3>Phase 1 — Broad Mapping</h3>
                  {diagnostic.questions.map((q) => (
                    <div className="q-row" key={q.id}>
                      <span>{q.text}</span>
                      <select value={broadAnswers[q.id] || "somewhat"} onChange={(e) => setBroadAnswers({ ...broadAnswers, [q.id]: e.target.value })}>
                        <option value="yes">Yes</option>
                        <option value="somewhat">Somewhat</option>
                        <option value="no">No</option>
                      </select>
                    </div>
                  ))}
                  <button className="btn primary" disabled={!!loading} onClick={submitBroadDiagnostic}>
                    {loading === "diagnostic" ? <Loader2 className="spin" size={16} /> : <Send size={16} />} Continue Diagnostic
                  </button>
                </div>
              )}

              {/* Phase 2 */}
              {diagnostic?.phase === "phase_2" && (
                <div className="diag-box">
                  <h3>Phase 2 — Drill Down</h3>
                  {diagnostic.questions.map((q, i) => (
                    <label key={`${q.topic}-${i}`}>
                      {q.text}
                      <textarea rows="3" value={drillAnswers[i] || ""} onChange={(e) => setDrillAnswers({ ...drillAnswers, [i]: e.target.value })} />
                    </label>
                  ))}
                  <button className="btn primary" disabled={!!loading} onClick={submitDrillDiagnostic}>
                    {loading === "diagnostic" ? <Loader2 className="spin" size={16} /> : <Send size={16} />} Score Answers
                  </button>
                </div>
              )}

              {/* Phase 3 */}
              {diagnostic?.phase === "phase_2_complete" && (
                <div className="diag-box">
                  <h3>Phase 3 — Learning Profile</h3>
                  <div className="form-grid">
                    <div><label style={{marginBottom: "6px", display: "block"}}>Format Preference</label>
                      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "12px" }}>
                        {["video", "text", "hands-on"].map(fmt => (
                          <label key={fmt} style={{ display: "flex", alignItems: "center", gap: "6px", background: profile.format_preference.includes(fmt) ? "#e0e7ff" : "#f1f5f9", border: profile.format_preference.includes(fmt) ? "1px solid #6366f1" : "1px solid transparent", padding: "6px 10px", borderRadius: "6px", cursor: "pointer", fontSize: "14px" }}>
                            <input 
                              type="checkbox" 
                              checked={profile.format_preference.includes(fmt)}
                              onChange={(e) => {
                                const newPrefs = e.target.checked 
                                  ? [...profile.format_preference, fmt]
                                  : profile.format_preference.filter(p => p !== fmt);
                                setProfile({ ...profile, format_preference: newPrefs });
                              }} 
                            />
                            {fmt.charAt(0).toUpperCase() + fmt.slice(1)}
                          </label>
                        ))}
                      </div>
                    </div>
                    <label>Daily hours
                      <input type="number" min="1" max="12" value={profile.daily_hours} onChange={(e) => setProfile({ ...profile, daily_hours: Number(e.target.value) })} />
                    </label>
                    <label>Deadline style
                      <select value={profile.deadline_style} onChange={(e) => setProfile({ ...profile, deadline_style: e.target.value })}>
                        <option value="flexible">Flexible</option>
                        <option value="strict">Strict</option>
                      </select>
                    </label>
                    <label>Goal type
                      <select value={profile.goal_specificity} onChange={(e) => setProfile({ ...profile, goal_specificity: e.target.value })}>
                        <option value="project">Project</option>
                        <option value="job">Job</option>
                        <option value="exam">Exam</option>
                        <option value="hobby">Hobby</option>
                      </select>
                    </label>
                  </div>
                  <button className="btn primary" disabled={!!loading} onClick={submitProfile}>
                    {loading === "diagnostic" ? <Loader2 className="spin" size={16} /> : <Sparkles size={16} />} Generate Final Roadmap
                  </button>
                </div>
              )}
            </div>
          </section>
        )}

        {/* ─── ROADMAP VIEW ─── */}
        {view === "roadmap" && (
          <section className="view-panel">
            <div className="card wide-card">
              <h2>Roadmap</h2>
              <p className="muted">Your personalized learning roadmap generated by the AI.</p>
              {(() => {
                const weeks = roadmap?.roadmap || [];
                if (!weeks.length) return (
                  <div className="empty-state">
                    <Sparkles size={20} />
                    <p>Generate a roadmap from the Onboarding page first.</p>
                  </div>
                );
                return (
                  <div className="roadmap-list">
                    {weeks.map((w, i) => (
                      <div className="roadmap-week" key={`${w.week || i}-${w.milestone || ""}`}>
                        <div className="week-badge">W{w.week || i + 1}</div>
                        <div>
                          <h3>{w.milestone || w.project || `Week ${w.week || i + 1}`}</h3>
                          <div className="chip-row">
                            {(w.topics || []).map((t) => <span className="chip" key={t}>{t}</span>)}
                          </div>
                          {!!w.resources?.length && <p className="muted sm">Resources: {w.resources.join(", ")}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>
          </section>
        )}

        {/* ─── RESOURCES VIEW ─── */}
        {view === "resources" && (
          <section className="view-panel">
            <div className="card wide-card">
              <h2>Resource Ingestion</h2>
              <p className="muted">Extract content from URLs or PDFs, classify it, then confirm.</p>
              <div className="input-row">
                <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}>
                  <option value="auto">Auto</option>
                  <option value="youtube">YouTube</option>
                  <option value="web">Website</option>
                </select>
                <input placeholder="Paste YouTube or article URL" value={url} onChange={(e) => setUrl(e.target.value)} />
                <button className="btn primary" disabled={!!loading} onClick={extractUrl}>
                  {(loading === "extract-url" || loading === "add-resource") ? <Loader2 className="spin" size={16} /> : <Link size={16} />} Analyze
                </button>
              </div>
              <label className="file-upload">
                <Upload size={17} />
                <span>Upload PDF</span>
                <input type="file" accept="application/pdf" onChange={extractPdf} />
              </label>

              {resourceCard && (
                <div className="resource-card" style={{ marginTop: 16 }}>
                  <div>
                    <small>{resourceCard.type}</small>
                    <h3>{resourceCard.title}</h3>
                    <p>{resourceCard.conflict_warning || "No conflicts detected."}</p>
                  </div>
                  <div className="chip-row">
                    <span className="chip">{resourceCard.estimated_time || 0} hours</span>
                    {(resourceCard.topics || []).slice(0, 4).map((t) => <span className="chip" key={t}>{t}</span>)}
                  </div>
                  
                  {/* Show snippet of extracted data */}
                  {resourceText && (
                    <div style={{ marginTop: 12, padding: 8, background: "#f1f5f9", borderRadius: 6, fontSize: 12, color: "#475569", maxHeight: 60, overflowY: "auto", fontFamily: "monospace" }}>
                      {typeof resourceText === "string" ? resourceText.substring(0, 300) + "..." : JSON.stringify(resourceText).substring(0, 300) + "..."}
                    </div>
                  )}

                  {!confirmedResource ? (
                    <button className="btn primary" disabled={!!loading} style={{ marginTop: 12 }} onClick={() => routeAction("confirm_resource", { card: resourceCard, full_content: resourceText }, "confirm_resource")}>
                      {loading === "confirm_resource" ? <Loader2 className="spin" size={16} /> : <Check size={16} />} Confirm Resource
                    </button>
                  ) : (
                    <div style={{ marginTop: 12 }}>
                      <p className="success" style={{ marginBottom: 8, fontSize: 14 }}>✅ Resource confirmed!</p>
                      <button className="btn outline" onClick={() => { setResourceCard(null); setResourceText(""); setConfirmedResource(null); setUrl(""); }}>
                        + Add Another Resource
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>
        )}

        {/* ─── DIAGNOSTICS VIEW ─── */}
        {view === "diagnostics" && (
          <section className="view-panel">
            <div className="card wide-card">
              <h2>Diagnostics</h2>
              <p className="muted">Run the diagnostic flow from the Onboarding page to see results here.</p>
              {diagnostic ? <JsonBlock data={diagnostic} /> : <div className="empty-state"><Brain size={20} /><p>No diagnostic data yet.</p></div>}
            </div>
          </section>
        )}

        {/* ─── QUIZZES VIEW ─── */}
        {view === "quizzes" && (
          <section className="view-panel">
            <div className="card wide-card">
              <h2>Testing Flow</h2>
              <p className="muted">Mark a source complete, answer the quiz, and schedule review.</p>
              <div className="input-row compact">
                <input placeholder="source_id" value={sourceId} onChange={(e) => setSourceId(e.target.value)} />
                <button className="btn primary" disabled={!!loading} onClick={() => routeAction("mark_source_complete", { source_id: sourceId }, "mark_source_complete")}>
                  {loading === "mark_source_complete" ? <Loader2 className="spin" size={16} /> : <Gauge size={16} />} Generate Quiz
                </button>
              </div>
              {quiz?.questions?.map((q) => (
                <label key={q.id} className="quiz-question">
                  {q.text}
                  {q.options?.length ? (
                    <select value={quizAnswers[q.id] || ""} onChange={(e) => setQuizAnswers({ ...quizAnswers, [q.id]: e.target.value })}>
                      <option value="">Choose answer</option>
                      {q.options.map((o) => <option value={o} key={o}>{o}</option>)}
                    </select>
                  ) : (
                    <textarea rows="3" value={quizAnswers[q.id] || ""} onChange={(e) => setQuizAnswers({ ...quizAnswers, [q.id]: e.target.value })} />
                  )}
                </label>
              ))}
              {!!quiz?.questions?.length && (
                <button className="btn primary" disabled={!!loading} onClick={submitQuiz}>
                  {loading === "submit-quiz" ? <Loader2 className="spin" size={16} /> : <Send size={16} />} Submit Quiz
                </button>
              )}
            </div>
          </section>
        )}

        {/* ─── COACH VIEW ─── */}
        {view === "coach" && (
          <section className="view-panel">
            <div className="card wide-card">
              <h2>Coach & Exports</h2>
              <p className="muted">Talk to the AI coach or trigger portfolio/weekly actions.</p>
              <div className="chat-log">
                {chatMessages.length === 0 ? <p className="muted">Coach messages appear here.</p> : chatMessages.map((m, i) => (
                  <div className={`chat ${m.role}`} key={`${m.role}-${i}`}>{m.content}</div>
                ))}
              </div>
              <div className="input-row compact">
                <input placeholder="Ask your coach..." value={chatInput} onChange={(e) => setChatInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && sendChat()} />
                <button className="btn primary" disabled={!!loading} onClick={sendChat}>
                  {loading === "chat" ? <Loader2 className="spin" size={16} /> : <MessageCircle size={16} />} Send
                </button>
              </div>
              <div className="btn-row">
                <button className="btn outline" disabled={!!loading} onClick={() => routeAction("generate_portfolio", {}, "generate_portfolio")}>
                  {loading === "generate_portfolio" ? <Loader2 className="spin" size={16} /> : <FileText size={16} />} Portfolio
                </button>
                <button className="btn outline" disabled={!!loading} onClick={() => routeAction("scheduled_weekly", {}, "scheduled_weekly")}>
                  {loading === "scheduled_weekly" ? <Loader2 className="spin" size={16} /> : <RefreshCw size={16} />} Weekly Review
                </button>
              </div>
            </div>
          </section>
        )}

        {/* ─── INSIGHTS VIEW ─── */}
        {view === "insights" && (
          <section className="view-panel">
            <div className="card wide-card">
              <h2>Insights</h2>
              <p className="muted">Daily and weekly analytics will appear here.</p>
              <div className="btn-row">
                <button className="btn primary" disabled={!!loading} onClick={() => routeAction("scheduled_morning", {}, "scheduled_morning")}>
                  {loading === "scheduled_morning" ? <Loader2 className="spin" size={16} /> : <RefreshCw size={16} />} Morning Brief
                </button>
                <button className="btn outline" disabled={!!loading} onClick={() => routeAction("scheduled_weekly", {}, "scheduled_weekly")}>
                  {loading === "scheduled_weekly" ? <Loader2 className="spin" size={16} /> : <RefreshCw size={16} />} Weekly Review
                </button>
              </div>
              {lastResult && lastAction?.action_type?.startsWith("scheduled") && <JsonBlock data={lastResult} />}
            </div>
          </section>
        )}

        {/* ─── PORTFOLIO VIEW ─── */}
        {view === "portfolio" && (
          <section className="view-panel">
            <div className="card wide-card">
              <h2>Portfolio</h2>
              <p className="muted">Generate resume bullets and project summaries from your achievements.</p>
              <button className="btn primary" disabled={!!loading} onClick={() => routeAction("generate_portfolio", {}, "generate_portfolio")}>
                {loading === "generate_portfolio" ? <Loader2 className="spin" size={16} /> : <Trophy size={16} />} Generate Portfolio
              </button>
              {lastResult && lastAction?.action_type === "generate_portfolio" && <JsonBlock data={lastResult} />}
            </div>
          </section>
        )}

        {/* ─── SETTINGS VIEW ─── */}
        {view === "settings" && (
          <section className="view-panel">
            <div className="card wide-card">
              <h2>Settings</h2>
              <label>Backend user ID
                <input value={userId} readOnly />
              </label>
              <label>Current goal
                <input value={goal} onChange={(e) => setGoal(e.target.value)} />
              </label>
            </div>
          </section>
        )}

        {/* ─── DEV PANEL ─── */}
        {devMode && (
          <section className="card dev-panel">
            <h2>Backend Response <span className="badge dev">Dev Mode</span></h2>
            <div className="response-grid">
              <div>
                <h3>Last request</h3>
                <JsonBlock data={lastAction} />
              </div>
              <div>
                <h3>Last result</h3>
                <JsonBlock data={lastResult} />
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
