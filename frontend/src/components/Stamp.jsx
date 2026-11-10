// The recommendation, printed the way a branch office marks a loan file: a rubber stamp in ink.
const WORDING = {
  approve: { en: "SANCTION", hi: "स्वीकृत करें" },
  conditional: { en: "SANCTION WITH CONDITIONS", hi: "शर्तों के साथ स्वीकृत" },
  review: { en: "VISIT THE FARM FIRST", hi: "पहले खेत की जाँच" },
  decline: { en: "DO NOT SANCTION", hi: "अस्वीकार" },
};

export default function Stamp({ decision, amount, date }) {
  const w = WORDING[decision] || WORDING.review;
  const long = w.en.length > 12;
  return (
    <div className={`stamp stamp-${decision}`} role="img" aria-label={`Recommendation: ${w.en.toLowerCase()}${amount ? `, ${amount}` : ""}`}>
      <svg viewBox="0 0 300 172" aria-hidden="true">
        <defs>
          <filter id={`ink-${decision}`} x="-5%" y="-5%" width="110%" height="110%">
            <feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="2" seed="7" result="noise" />
            <feColorMatrix in="noise" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.7 1.85" result="holes" />
            <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="1" seed="3" result="warp" />
            <feDisplacementMap in="SourceGraphic" in2="warp" scale="3" result="rough" />
            <feComposite in="rough" in2="holes" operator="in" />
          </filter>
        </defs>
        <g filter={`url(#ink-${decision})`} fill="currentColor" stroke="currentColor">
          <rect x="5" y="5" width="290" height="162" rx="16" fill="none" strokeWidth="5" />
          <rect x="15" y="15" width="270" height="142" rx="9" fill="none" strokeWidth="1.6" />
          <text x="150" y="40" textAnchor="middle" stroke="none" className="stamp-small">AgriCred recommends</text>
          <text x="150" y={long ? 76 : 82} textAnchor="middle" stroke="none" className={long ? "stamp-big long" : "stamp-big"}>{w.en}</text>
          <text x="150" y={long ? 106 : 114} textAnchor="middle" stroke="none" className="stamp-hi">{w.hi}</text>
          <line x1="30" x2="270" y1="124" y2="124" strokeWidth="1.4" />
          <text x="36" y="146" stroke="none" className="stamp-small">{date}</text>
          <text x="264" y="147" textAnchor="end" stroke="none" className="stamp-amount">{amount || "No limit"}</text>
        </g>
      </svg>
    </div>
  );
}
