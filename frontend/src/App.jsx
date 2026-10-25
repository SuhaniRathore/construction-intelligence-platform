import { useState, useEffect } from "react";
const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function post(path, fields) {
  const fd = new FormData();
  Object.entries(fields).forEach(([k, v]) => v !== null && v !== undefined && v !== "" && fd.append(k, v));
  const r = await fetch(API + path, { method: "POST", body: fd });
  if (!r.ok) throw new Error("Request failed");
  return r.json();
}

function Result({ data }) {
  if (!data) return null;
  return (
    <div className="result">
      {Object.entries(data).map(([k, v]) => (
        <div key={k} className="row">
          <b>{k.replaceAll("_", " ")}</b>
          <span>{Array.isArray(v) ? (typeof v[0] === "object" ? <pre>{JSON.stringify(v, null, 2)}</pre> : <ul>{v.map((x, i) => <li key={i}>{x}</li>)}</ul>) : String(v)}</span>
        </div>
      ))}
    </div>
  );
}

function Panel({ title, run, children, fields, needsImage }) {
  const [vals, setVals] = useState({});
  const [img, setImg] = useState(null);
  const [out, setOut] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setErr(""); setOut(null);
    try { setOut(await run({ ...vals, image: img })); } catch { setErr("Could not reach backend. Is it running?"); }
    setBusy(false);
  };
  return (
    <form onSubmit={submit} className="card">
      <h2>{title}</h2>
      {fields.map((f) => (
        <label key={f.name}>{f.label}
          {f.options ? (
            <select onChange={(e) => setVals({ ...vals, [f.name]: e.target.value })}>{f.options.map((o) => <option key={o}>{o}</option>)}</select>
          ) : (
            <input type={f.type || "text"} required={f.required !== false} onChange={(e) => setVals({ ...vals, [f.name]: e.target.value })} />
          )}
        </label>
      ))}
      {(needsImage !== undefined) && (
        <label>Upload image {needsImage ? "" : "(optional)"}
          <input type="file" accept="image/*" required={needsImage} onChange={(e) => setImg(e.target.files[0])} />
        </label>
      )}
      <button disabled={busy}>{busy ? "Analysing..." : "Analyse"}</button>
      {err && <p className="err">{err}</p>}
      <Result data={out} />
    </form>
  );
}

function Weather() {
  const [w, setW] = useState(null);
  useEffect(() => { fetch(API + "/api/weather").then((r) => r.json()).then(setW).catch(() => {}); }, []);
  return (
    <div className="card">
      <h2>Weather-aware Advisory (Indore)</h2>
      {w ? <Result data={w} /> : <p>Loading...</p>}
    </div>
  );
}

const tabs = {
  "Safety Monitoring": <Panel title="Site Safety Monitoring" fields={[{ name: "notes", label: "Notes", required: false }]} needsImage={true}
    run={(v) => post("/api/safety", v)} />,
  "Crack Detection": <Panel title="Crack Detection & Analysis" fields={[]} needsImage={true} run={(v) => post("/api/cracks", v)} />,
  "Real Estate Valuation": <Panel title="Real Estate Valuation" needsImage={false}
    fields={[{ name: "location", label: "Location" }, { name: "area_sqft", label: "Area (sqft)", type: "number" },
      { name: "property_type", label: "Type", options: ["Residential", "Commercial", "Plot"] },
      { name: "age_years", label: "Age (years)", type: "number", required: false }]}
    run={(v) => post("/api/valuation", v)} />,
  "Project Planning": <Panel title="Construction Project Planning"
    fields={[{ name: "project_type", label: "Project type" }, { name: "budget_inr", label: "Budget (INR)", type: "number" },
      { name: "duration_months", label: "Duration (months)", type: "number" }, { name: "description", label: "Description", required: false }]}
    run={(v) => post("/api/planning", v)} />,
  "Daily Assistant": <div className="stack"><Weather /><Panel title="Construction Knowledge Assistant" needsImage={false}
    fields={[{ name: "question", label: "Ask a question" }]} run={(v) => post("/api/assistant", v)} /></div>,
};

export default function App() {
  const [tab, setTab] = useState(Object.keys(tabs)[0]);
  return (
    <div className="app">
      <header><h1>🏗️ Multimodal Construction Intelligence Platform</h1>
        <p>AI-powered decision support: React.js + FastAPI + multimodal LLM</p></header>
      <nav>{Object.keys(tabs).map((t) => <button key={t} className={t === tab ? "on" : ""} onClick={() => setTab(t)}>{t}</button>)}</nav>
      <main key={tab}>{tabs[tab]}</main>
    </div>
  );
}
