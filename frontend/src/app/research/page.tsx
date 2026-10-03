"use client";

import { useEffect, useState } from "react";
import { api, modelName, Performance, percent } from "@/lib/api";
import { MetricCard, StateBox } from "@/components/shell";
import { CalibrationChart, ComparisonChart } from "@/components/charts";

export default function Research() {
  const [data, setData] = useState<Performance | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Performance>("/models/performance")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  if (error) return <StateBox error>{error}</StateBox>;
  if (!data) return <StateBox>Loading measured model performance…</StateBox>;
  const r = data.report;
  return (
    <>
      <section className="page-heading">
        <div>
          <div className="eyebrow">EVALUATION / TRANSPARENCY</div>
          <h1>The evidence behind it.</h1>
          <p>
            Honest comparisons. Chronological validation. A sealed final test.
          </p>
        </div>
      </section>
      {!r ? (
        <StateBox>{data.message}</StateBox>
      ) : (
        <>
          <div className="metric-grid">
            <MetricCard
              label="TEST LOG LOSS"
              value={r.test.log_loss.toFixed(3)}
              note={`${r.test_season} · ${r.test.n} matches`}
            />
            <MetricCard
              label="TEST BRIER SCORE"
              value={r.test.brier.toFixed(3)}
              note="Sum across three outcomes · lower is better"
            />
            <MetricCard
              label="TEST ACCURACY"
              value={percent(r.test.accuracy)}
              note="Secondary metric · outcome classification"
            />
            <MetricCard
              label="CALIBRATION ERROR"
              value={r.test.ece.toFixed(3)}
              note="Top-outcome ECE · lower is better"
            />
          </div>
          <div className="two-columns">
            <section className="panel">
              <h2>Model comparison</h2>
              <p className="muted">
                Selection-period log loss; these values select the recipe.
              </p>
              <ComparisonChart
                data={Object.entries(r.comparison).map(([name, m]) => ({
                  name: modelName(name),
                  log_loss: m.log_loss,
                }))}
              />
            </section>
            <section className="panel">
              <h2>Sealed-test reliability</h2>
              <p className="muted">
                Predicted probability → observed correctness. The dashed line is
                perfect calibration.
              </p>
              <CalibrationChart bins={r.test.calibration_bins} />
            </section>
          </div>
          <section className="panel">
            <h2>Selected forecast recipe</h2>
            <div className="recipe">
              <span className="tag">{r.ensemble.kind.toUpperCase()}</span>
              <span>{r.ensemble.members.map(modelName).join(" + ")}</span>
              <span className="muted">Calibration: {r.calibration}</span>
            </div>
            <p className="muted">
              The final test measures the frozen recipe. Production models are
              subsequently refitted on completed matches.
            </p>
          </section>
          <section className="panel">
            <h2>Research limitations</h2>
            {r.limitations.map((item) => (
              <p className="limitation" key={item}>
                {item}
              </p>
            ))}
          </section>
        </>
      )}
    </>
  );
}
