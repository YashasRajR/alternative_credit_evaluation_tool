import { useEffect, useState } from "react";
import { api } from "./api.js";
import Dashboard from "./pages/Dashboard.jsx";
import NewAssessment from "./pages/NewAssessment.jsx";
import Result from "./pages/Result.jsx";

export default function App() {
  const [view, setView] = useState({ name: "dashboard" });
  const [health, setHealth] = useState(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() =>
      setHealth({ ok: false, message: "The AgriCred server isn't running. Start it with: python app.py" })
    );
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <button className="brand" onClick={() => setView({ name: "dashboard" })}>
          <img src="/favicon.svg" alt="" width="34" height="34" />
          <span>AgriCred<small>Credit for farmers without a credit history</small></span>
        </button>
        <nav>
          <button className={view.name === "dashboard" ? "active" : ""} onClick={() => setView({ name: "dashboard" })}>
            Assessments
          </button>
          <button className={view.name === "new" ? "active" : ""} onClick={() => setView({ name: "new" })}>
            New assessment
          </button>
        </nav>
      </header>
      {health && !health.ok && <div className="banner warn" role="status">{health.message}</div>}
      <main>
        {view.name === "dashboard" && (
          <Dashboard onOpen={(id) => setView({ name: "result", id })} onNew={() => setView({ name: "new" })} />
        )}
        {view.name === "new" && <NewAssessment onDone={(doc) => setView({ name: "result", id: doc.id })} />}
        {view.name === "result" && <Result id={view.id} onBack={() => setView({ name: "dashboard" })} />}
      </main>
      <footer>
        Credit suggestions support a loan officer's judgement and do not replace it. The risk model is trained on
        synthetic data until you add your own loan records.
      </footer>
    </div>
  );
}
