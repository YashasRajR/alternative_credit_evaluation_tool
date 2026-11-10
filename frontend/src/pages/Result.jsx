import { useEffect, useState } from "react";
import { api, pct, rupees } from "../api.js";
import ScoreRuler from "../components/ScoreRuler.jsx";
import Stamp from "../components/Stamp.jsx";

const DECISION_NOTE = {
  approve: "The farmer's record and repayment capacity support this loan.",
  conditional: "Lend, but consider a smaller amount, crop insurance or a guarantor.",
  review: "Visit the farm and verify the details before deciding.",
  decline: "Risk is too high right now. Share the steps below to improve the score.",
};

export default function Result({ id, onBack }) {
  const [a, setA] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => { api.get(id).then(setA).catch((e) => setError(e.message)); }, [id]);

  if (error) return <div className="banner error">{error}</div>;
  if (!a) return <p className="muted center">Loading the assessment</p>;

  const f = a.farmer;
  const fin = a.finance;
  const place = [f.village, f.district, f.state].filter(Boolean).join(", ");
  const gap = a.requested_amount ? a.suggested_limit - a.requested_amount : null;
  const assessed = new Date(a.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" });
  const maxDriver = Math.max(...a.risk.drivers.map((d) => Math.abs(d.effect)), 0.01);

  return (
    <section className="result">
      <div className="row no-print">
        <button className="link" onClick={onBack}>All assessments</button>
        <span className="spacer" />
        <button className="ghost" onClick={() => window.print()}>Print or save as PDF</button>
      </div>

      <article className="record">
        <header className="record-head">
          <div>
            <h1>{f.name}</h1>
            <p className="muted">
              {place && <>{place}<br /></>}
              {a.inputs.acres_owned + a.inputs.acres_leased} acres of {a.inputs.current_crop}, {a.inputs.irrigation === "rainfed" ? "rain-fed" : a.inputs.irrigation === "partial" ? "partly irrigated" : "irrigated"}.
              Assessed {assessed}.
            </p>
          </div>
          <Stamp decision={a.decision} amount={a.suggested_limit > 0 ? rupees(a.suggested_limit) : null} date={assessed} />
        </header>

        <div className="record-score">
          <ScoreRuler score={a.score} band={a.band} meaning={a.band_meaning} />
          <p>
            <b>Band {a.band}, {a.band_meaning.toLowerCase()}.</b>{" "}
            <span className="muted">
              Scored out of 100 from the ten factors below.{" "}
              {a.next_band
                ? `${a.next_band.points_needed} more point${a.next_band.points_needed === 1 ? "" : "s"} would reach band ${a.next_band.band}.`
                : "This is the highest band."}
            </span>
          </p>
        </div>

        <div className="record-call">
          <p className="call-reason">{a.decision_reason || DECISION_NOTE[a.decision]}</p>
          <dl className="figures">
            <div><dt>Suggested limit</dt><dd>{rupees(a.suggested_limit)}</dd></div>
            <div><dt>Requested</dt><dd>{a.requested_amount ? rupees(a.requested_amount) : "Not stated"}</dd></div>
            <div><dt>Chance of default</dt><dd>{pct(a.risk.probability_of_default, 1)}</dd></div>
          </dl>
          {gap !== null && gap < 0 && a.suggested_limit > 0 && (
            <p className="small note">{rupees(-gap)} more than the farmer can comfortably repay in {a.inputs.tenure_months} months.</p>
          )}
        </div>
      </article>

      <div className="cols">
        <section className="section">
          <h2>Why this score</h2>
          <p className="muted small">Points for each factor, out of the maximum it can add.</p>
          <ul className="factors">
            {a.factors.map((x) => (
              <li key={x.key}>
                <div className="factor-top">
                  <span>{x.label}</span>
                  <b>{x.points}<small> / {x.max}</small></b>
                </div>
                <div className="meter" aria-hidden="true"><span style={{ width: `${(x.points / x.max) * 100}%` }} className={x.points / x.max < 0.4 ? "low" : ""} /></div>
                <p className="small muted">{x.note}</p>
              </li>
            ))}
          </ul>
        </section>

        <div className="stack">
          <section className="section">
            <h2>Money</h2>
            <dl className="ledger">
              <div><dt>{a.inputs.current_crop} this season</dt><dd>{fin.season.production_qtl} quintal at {rupees(fin.season.price)}</dd></div>
              <div><dt>Expected sales</dt><dd>{rupees(fin.season.gross)}</dd></div>
              <div><dt>Cultivation cost</dt><dd>{rupees(fin.season.cost)}</dd></div>
              <div className="total"><dt>Net from this crop</dt><dd>{rupees(fin.season.net)}</dd></div>
              <div><dt>Household income per month</dt><dd>{rupees(fin.monthly_income)}</dd></div>
              <div><dt>Repayments already due</dt><dd>{pct(fin.debt_ratio)} of income</dd></div>
              <div className="total"><dt>Room for a new monthly instalment</dt><dd>{rupees(fin.max_new_emi)}</dd></div>
            </dl>
          </section>

          <section className="section">
            <h2>What the risk model weighed</h2>
            <p className="muted small">How this farmer compares with a typical borrower, strongest effects first.</p>
            <ul className="drivers">
              {a.risk.drivers.map((d) => (
                <li key={d.feature}>
                  <span>{d.feature}</span>
                  <div className="dbar">
                    <span className={d.effect > 0 ? "up" : "down"} style={{ width: `${(Math.abs(d.effect) / maxDriver) * 50}%` }} />
                  </div>
                  <small className={d.effect > 0 ? "up-t" : "down-t"}>{d.effect > 0 ? "raises risk" : "lowers risk"}</small>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>

      {a.actions.length > 0 && (
        <section className="section">
          <h2>How {f.name.split(" ")[0]} can improve the score</h2>
          <ol className="actions">
            {a.actions.map((x) => (
              <li key={x.action}>
                <span className="plus">+{x.points}</span>
                <div><b>{x.action}</b><p className="muted small">{x.why}</p></div>
              </li>
            ))}
          </ol>
        </section>
      )}

      <section className="section">
        <h2>Crop guidance for {a.inputs.season === "kharif" ? "kharif" : "rabi"}</h2>
        {a.guidance.switch && (
          <p className="callout">
            {a.guidance.switch.crop} could earn about {rupees(a.guidance.switch.extra_per_acre)} more per acre than {a.inputs.current_crop} on this land,
            around {rupees(a.guidance.switch.extra_total)} across the farm. Check local demand and input costs before switching.
          </p>
        )}
        <table className="table">
          <thead><tr><th>Crop</th><th>Why it fits</th><th className="num">MSP per quintal</th><th className="num">Typical yield</th><th className="num">Net per acre</th></tr></thead>
          <tbody>
            {a.guidance.crops.map((c) => (
              <tr key={c.crop}>
                <td><b>{c.crop}</b>{c.is_current && <span className="tag">Current</span>}</td>
                <td className="muted">{c.reasons.join(", ")}</td>
                <td className="num">{rupees(c.msp)}</td>
                <td className="num">{c.yield_per_acre} q/acre</td>
                <td className="num"><b>{rupees(c.net_per_acre)}</b></td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="small muted">{a.guidance.source}</p>
      </section>
    </section>
  );
}
