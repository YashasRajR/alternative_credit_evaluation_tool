import { useEffect, useState } from "react";
import { api, rupees } from "../api.js";

const STEPS = ["Farmer", "Farm", "Money", "Records"];

const EMPTY = {
  name: "", village: "", district: "", state: "", age: "", family_size: "", family_earners: 1,
  acres_owned: "", acres_leased: "", lease_document: false, soil: "alluvial", irrigation: "rainfed",
  season: "kharif", current_crop: "", crops_per_year: 1, years_farming: "", crop_failures_3y: 0,
  has_livestock: false, expected_yield: "", expected_price: "",
  other_monthly_income: "", existing_emi: "", repayment_history: "none", requested_amount: "", tenure_months: 12,
  upi_txn_per_month: "", shg_member: false, regular_savings: false, crop_insured: false, soil_health_card: false,
};

const SAMPLE = {
  ...EMPTY, name: "Savitri Patil", village: "Kurundwad", district: "Kolhapur", state: "Maharashtra",
  age: 42, family_size: 5, family_earners: 2, acres_owned: 2.5, acres_leased: 1, lease_document: true,
  soil: "black", irrigation: "partial", season: "kharif", current_crop: "Soybean", crops_per_year: 2,
  years_farming: 18, crop_failures_3y: 1, has_livestock: true, other_monthly_income: 4500, existing_emi: 1800,
  repayment_history: "mostly", requested_amount: 60000, tenure_months: 12, upi_txn_per_month: 14,
  shg_member: true, regular_savings: false, crop_insured: false, soil_health_card: true,
};

const SOILS = [["alluvial", "Alluvial"], ["black", "Black"], ["red", "Red"], ["laterite", "Laterite"], ["sandy", "Sandy"], ["clay", "Clay"]];
const IRRIGATION = [["irrigated", "Irrigated"], ["partial", "Partly irrigated"], ["rainfed", "Rain-fed"]];
const REPAYMENT = [
  ["on_time", "Repaid every past loan on time"],
  ["mostly", "Repaid, with a few delays"],
  ["late", "Often late with repayments"],
  ["default", "Has defaulted on a loan"],
  ["none", "Has never taken a loan"],
];

function Field({ label, hint, children, wide }) {
  return (
    <label className={`field ${wide ? "wide" : ""}`}>
      <span className="field-label">{label}</span>
      {children}
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  );
}

function Pills({ options, value, onChange, name }) {
  return (
    <div className="pills" role="radiogroup" aria-label={name}>
      {options.map(([v, label]) => (
        <button type="button" key={v} role="radio" aria-checked={value === v}
          className={value === v ? "pill on" : "pill"} onClick={() => onChange(v)}>
          {label}
        </button>
      ))}
    </div>
  );
}

function Check({ label, hint, checked, onChange }) {
  return (
    <label className={`check ${checked ? "on" : ""}`}>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="box" aria-hidden="true" />
      <span>
        <b>{label}</b>
        {hint && <small>{hint}</small>}
      </span>
    </label>
  );
}

export default function NewAssessment({ onDone }) {
  const [form, setForm] = useState(EMPTY);
  const [step, setStep] = useState(0);
  const [crops, setCrops] = useState([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => { api.crops().then((d) => setCrops(d.crops)).catch(() => {}); }, []);

  const set = (key) => (v) => setForm((f) => ({ ...f, [key]: v?.target ? v.target.value : v }));
  const seasonCrops = crops.filter((c) => c.season === form.season);
  const crop = crops.find((c) => c.name === form.current_crop);

  const problems = () => {
    if (step === 0 && !form.name.trim()) return "Enter the farmer's name.";
    if (step === 1 && !(Number(form.acres_owned) + Number(form.acres_leased) > 0)) return "Enter how many acres the farmer cultivates.";
    if (step === 1 && !form.current_crop) return "Choose the crop for this season.";
    return "";
  };

  const next = () => {
    const p = problems();
    if (p) return setError(p);
    setError("");
    setStep((s) => s + 1);
  };

  const submit = async () => {
    const p = problems();
    if (p) return setError(p);
    setSaving(true);
    setError("");
    try {
      onDone(await api.create(form));
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="assess">
      <div className="page-head">
        <div>
          <h1>New credit assessment</h1>
          <p className="muted">Fill in what you learn from the farmer. Every answer is used, and you'll see how each one affects the score.</p>
        </div>
        <button className="ghost" onClick={() => { setForm(SAMPLE); setError(""); }}>Fill in a sample farmer</button>
      </div>

      <ol className="steps">
        {STEPS.map((s, i) => (
          <li key={s} className={i === step ? "now" : i < step ? "done" : ""}>
            <button type="button" onClick={() => (i < step ? setStep(i) : null)} disabled={i > step}>
              <span className="n">{i + 1}</span>{s}
            </button>
          </li>
        ))}
      </ol>

      <div className="sheet">
        {step === 0 && (
          <div className="grid">
            <Field label="Farmer's name" wide><input value={form.name} onChange={set("name")} autoFocus /></Field>
            <Field label="Village"><input value={form.village} onChange={set("village")} /></Field>
            <Field label="District"><input value={form.district} onChange={set("district")} /></Field>
            <Field label="State"><input value={form.state} onChange={set("state")} /></Field>
            <Field label="Age"><input type="number" min="18" value={form.age} onChange={set("age")} /></Field>
            <Field label="People in the household"><input type="number" min="1" value={form.family_size} onChange={set("family_size")} /></Field>
            <Field label="Earning members" hint="Including the farmer"><input type="number" min="1" value={form.family_earners} onChange={set("family_earners")} /></Field>
          </div>
        )}

        {step === 1 && (
          <div className="grid">
            <Field label="Acres owned"><input type="number" min="0" step="0.5" value={form.acres_owned} onChange={set("acres_owned")} /></Field>
            <Field label="Acres leased in"><input type="number" min="0" step="0.5" value={form.acres_leased} onChange={set("acres_leased")} /></Field>
            {Number(form.acres_leased) > 0 && (
              <Check label="Has a written lease agreement" checked={form.lease_document} onChange={set("lease_document")} />
            )}
            <Field label="Soil type" wide><Pills name="Soil type" options={SOILS} value={form.soil} onChange={set("soil")} /></Field>
            <Field label="Water" wide><Pills name="Water" options={IRRIGATION} value={form.irrigation} onChange={set("irrigation")} /></Field>
            <Field label="Season">
              <Pills name="Season" options={[["kharif", "Kharif"], ["rabi", "Rabi"]]} value={form.season}
                onChange={(v) => setForm((f) => ({ ...f, season: v, current_crop: "" }))} />
            </Field>
            <Field label="Crop this season">
              <select value={form.current_crop} onChange={set("current_crop")}>
                <option value="">Choose a crop</option>
                {seasonCrops.map((c) => <option key={c.name}>{c.name}</option>)}
              </select>
            </Field>
            <Field label="Expected yield (quintal per acre)" hint={crop ? `Typical: ${crop.yield_per_acre}. Leave blank to use it.` : "Leave blank to use the typical yield"}>
              <input type="number" min="0" step="0.5" value={form.expected_yield} onChange={set("expected_yield")} />
            </Field>
            <Field label="Expected price (₹ per quintal)" hint={crop ? `MSP: ${rupees(crop.msp)}. Leave blank to use it.` : "Leave blank to use the MSP"}>
              <input type="number" min="0" value={form.expected_price} onChange={set("expected_price")} />
            </Field>
            <Field label="Crops grown per year">
              <Pills name="Crops per year" options={[[1, "One"], [2, "Two"], [3, "Three"]]} value={Number(form.crops_per_year)} onChange={set("crops_per_year")} />
            </Field>
            <Field label="Crop failures in the last 3 years">
              <Pills name="Crop failures" options={[[0, "None"], [1, "One"], [2, "Two"], [3, "Three"]]} value={Number(form.crop_failures_3y)} onChange={set("crop_failures_3y")} />
            </Field>
            <Field label="Years of farming"><input type="number" min="0" value={form.years_farming} onChange={set("years_farming")} /></Field>
            <Check label="Keeps livestock" hint="Cows, buffaloes, goats or poultry" checked={form.has_livestock} onChange={set("has_livestock")} />
          </div>
        )}

        {step === 2 && (
          <div className="grid">
            <Field label="Other monthly income (₹)" hint="Wages, a shop, a family member's salary">
              <input type="number" min="0" value={form.other_monthly_income} onChange={set("other_monthly_income")} />
            </Field>
            <Field label="Current loan repayments (₹ per month)" hint="All lenders, including moneylenders">
              <input type="number" min="0" value={form.existing_emi} onChange={set("existing_emi")} />
            </Field>
            <Field label="Loan history" wide>
              <div className="radios">
                {REPAYMENT.map(([v, label]) => (
                  <label key={v} className={form.repayment_history === v ? "radio on" : "radio"}>
                    <input type="radio" name="repayment" checked={form.repayment_history === v} onChange={() => set("repayment_history")(v)} />
                    {label}
                  </label>
                ))}
              </div>
            </Field>
            <Field label="Amount requested (₹)"><input type="number" min="0" step="1000" value={form.requested_amount} onChange={set("requested_amount")} /></Field>
            <Field label="Repayment period">
              <Pills name="Repayment period" options={[[6, "6 months"], [12, "12 months"], [24, "24 months"]]} value={Number(form.tenure_months)} onChange={set("tenure_months")} />
            </Field>
          </div>
        )}

        {step === 3 && (
          <div className="grid">
            <Field label="UPI payments in a typical month" hint="Ask to see the payment app history if possible">
              <input type="number" min="0" value={form.upi_txn_per_month} onChange={set("upi_txn_per_month")} />
            </Field>
            <div className="checks wide">
              <Check label="Member of a Self-Help Group" checked={form.shg_member} onChange={set("shg_member")} />
              <Check label="Saves money regularly" hint="Bank, post office or SHG savings" checked={form.regular_savings} onChange={set("regular_savings")} />
              <Check label="Crop insured under PMFBY" checked={form.crop_insured} onChange={set("crop_insured")} />
              <Check label="Has a Soil Health Card" checked={form.soil_health_card} onChange={set("soil_health_card")} />
            </div>
          </div>
        )}

        {error && <p className="form-error" role="alert">{error}</p>}

        <div className="sheet-foot">
          {step > 0 && <button className="ghost" onClick={() => { setError(""); setStep(step - 1); }}>Back</button>}
          <span className="spacer" />
          {step < STEPS.length - 1
            ? <button className="primary" onClick={next}>Continue</button>
            : <button className="primary" onClick={submit} disabled={saving}>{saving ? "Assessing" : "Assess credit"}</button>}
        </div>
      </div>
    </section>
  );
}
