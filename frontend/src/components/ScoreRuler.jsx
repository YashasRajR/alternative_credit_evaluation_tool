// The 0-100 score drawn as a measuring tape, with the five risk bands marked along its edge.
const BANDS = [
  { band: "E", from: 0, to: 35 },
  { band: "D", from: 35, to: 50 },
  { band: "C", from: 50, to: 65 },
  { band: "B", from: 65, to: 80 },
  { band: "A", from: 80, to: 100 },
];

export default function ScoreRuler({ score, band, meaning }) {
  return (
    <div className="tape" aria-label={`Score ${score} out of 100, band ${band}, ${meaning}`}>
      <div className="tape-marker" style={{ left: `${score}%` }}>
        <span className={`tape-score band-${band}`}>{score}</span>
      </div>
      <div className="tape-body">
        {BANDS.map((b) => (
          <span key={b.band} className={`tape-band band-line-${b.band} ${b.band === band ? "here" : ""}`}
            style={{ left: `${b.from}%`, width: `${b.to - b.from}%` }}>
            {b.band}
          </span>
        ))}
      </div>
      <div className="tape-scale" aria-hidden="true">
        {[0, 35, 50, 65, 80, 100].map((n) => <span key={n} style={{ left: `${n}%` }}>{n}</span>)}
      </div>
    </div>
  );
}
