import { useEffect, useState } from "react";
import { api, pct, rupees } from "../api.js";

const DECISION = { approve: "Approve", conditional: "With conditions", review: "Field review", decline: "Decline" };

export default function Dashboard({ onOpen, onNew }) {
  const [stats, setStats] = useState(null);
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState("");

  const load = (query = q) =>
    Promise.all([api.stats(), api.list(query)])
      .then(([s, r]) => { setStats(s); setRows(r); setError(""); })
      .catch((e) => setError(e.message));

  useEffect(() => { load(""); }, []);
  useEffect(() => {
    const t = setTimeout(() => api.list(q).then(setRows).catch(() => {}), 250);
    return () => clearTimeout(t);
  }, [q]);

  const remove = async (e, id, name) => {
    e.stopPropagation();
    if (!window.confirm(`Delete the assessment for ${name}?`)) return;
    await api.remove(id);
    load();
  };

  if (error) return <div className="banner error">{error}</div>;
  if (!stats) return <p className="muted center">Loading</p>;

  if (stats.total === 0) {
    return (
      <section className="empty">
        <h1>No assessments yet</h1>
        <p className="muted">Assess a farmer's credit using land, harvests, savings and payment records, even without a credit history.</p>
        <button className="primary" onClick={onNew}>Start the first assessment</button>
      </section>
    );
  }

  return (
    <section>
      <div className="page-head">
        <h1>Assessments</h1>
        <button className="primary" onClick={onNew}>New assessment</button>
      </div>

      <p className="summary">
        <b>{stats.total}</b> farmers assessed, with an average score of <b>{stats.average_score}</b>.{" "}
        <b>{pct(stats.approval_rate)}</b> were recommended for a loan, for <b>{rupees(stats.total_suggested_credit)}</b> of credit in all.
      </p>

      <div className="section">
        <h2>Farmers in each risk band</h2>
        <div className="bandbar" role="img" aria-label="Number of farmers in each risk band">
          {"ABCDE".split("").map((b) => stats.bands[b] > 0 && (
            <div key={b} className={`band-bg-${b}`} style={{ flex: stats.bands[b] }}>
              <span>{b}</span><small>{stats.bands[b]}</small>
            </div>
          ))}
        </div>
        <p className="small muted">A is the lowest risk, E the highest.</p>
      </div>

      <div className="register">
        <div className="table-head">
          <h2>Register</h2>
          <input className="search" placeholder="Search by name, village or district" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        {rows.length === 0 ? <p className="muted">No farmers match "{q}".</p> : (
          <table className="table clickable">
            <thead><tr><th>Farmer</th><th>Crop</th><th className="num">Score</th><th>Recommendation</th><th className="num">Suggested limit</th><th>Date</th><th /></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} onClick={() => onOpen(r.id)}>
                  <td><b>{r.farmer.name}</b><br /><small className="muted">{[r.farmer.village, r.farmer.district].filter(Boolean).join(", ")}</small></td>
                  <td>{r.inputs?.current_crop}</td>
                  <td className="num"><span className={`chip band-bg-${r.band}`}>{r.band}</span> {r.score}</td>
                  <td><span className={`mini-stamp call-${r.decision}`}>{DECISION[r.decision]}</span></td>
                  <td className="num">{rupees(r.suggested_limit)}</td>
                  <td>{new Date(r.created_at).toLocaleDateString("en-IN")}</td>
                  <td><button className="link danger" onClick={(e) => remove(e, r.id, r.farmer.name)}>Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
