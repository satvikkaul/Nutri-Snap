import { useState, useMemo } from "react";
import { analyzeImage, fetchHistory, fetchNutrition } from "./api";
import "./App.css";

export default function App() {
  const [file, setFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  const canAnalyze = !!file && !analyzing;
  const canDownload = !!result;

  async function onAnalyze() {
    setError("");
    setAnalyzing(true);
    try {
      const data = await analyzeImage(file);
      setResult(data);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setAnalyzing(false);
    }
  }

  async function onLoadHistory() {
    setError("");
    try {
      const items = await fetchHistory(20);
      setHistory(items);
    } catch (e) {
      setError(String(e.message || e));
    }
  }

  async function onLookupNutrition() {
    if (!result?.food) return;
    setError("");
    try {
      const n = await fetchNutrition(result.food);
      // merge into result view
      setResult((r) => (r ? { ...r, nutrition_lookup: n } : r));
    } catch (e) {
      setError(String(e.message || e));
    }
  }

  function onReset() {
    setFile(null);
    setResult(null);
    setHistory([]);
    setError("");
    // clear file input value
    const el = document.getElementById("file-input");
    if (el) el.value = "";
  }

  const downloadPayload = useMemo(() => (result ? result : null), [result]);

  return (
    <div className="page">
      <div className="card">
        <h1>NutriSnap</h1>
        <p className="muted">
          Upload a food photo. We classify it and estimate calories/macros.
        </p>

        <div
          className="dropzone"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const f = e.dataTransfer.files?.[0];
            if (f && f.type.startsWith("image/")) setFile(f);
          }}
        >
          <input
            id="file-input"
            type="file"
            accept="image/*"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f && f.type.startsWith("image/")) setFile(f);
            }}
          />
          <p className="muted">
            Drag & drop an image here or click to choose.
          </p>
          {file && (
            <p className="fileinfo">
              Selected: <b>{file.name}</b> ({Math.round(file.size / 1024)} KB)
            </p>
          )}
        </div>

        <div className="row">
          <button
            className="btn primary"
            disabled={!canAnalyze}
            onClick={onAnalyze}
          >
            {analyzing ? "Analyzing…" : "Analyze"}
          </button>

          <button className="btn" onClick={onLoadHistory}>
            Load history
          </button>

          <button
            className="btn outline"
            disabled={!canDownload}
            onClick={() => {
              if (!downloadPayload) return;
              const blob = new Blob(
                [JSON.stringify(downloadPayload, null, 2)],
                { type: "application/json" }
              );
              const a = document.createElement("a");
              a.href = URL.createObjectURL(blob);
              a.download = "nutrisnap-analyze.json";
              a.click();
            }}
          >
            Download JSON
          </button>

          <button className="btn danger" onClick={onReset}>
            Reset
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {result && (
          <div className="panel">
            <h2>Result</h2>
            <div className="grid">
              <div><span className="k">Food</span><span className="v">{result.food}</span></div>
              <div><span className="k">Confidence</span><span className="v">{(result.confidence * 100).toFixed(1)}%</span></div>
              <div><span className="k">Calories</span><span className="v">{result.calories} kcal</span></div>
              <div><span className="k">Serving</span><span className="v">{result.serving_g} g</span></div>
              <div><span className="k">Protein</span><span className="v">{result.protein_g} g</span></div>
              <div><span className="k">Carbs</span><span className="v">{result.carbs_g} g</span></div>
              <div><span className="k">Fat</span><span className="v">{result.fat_g} g</span></div>
              <div><span className="k">Latency</span><span className="v">{result.inference_ms} ms</span></div>
              <div><span className="k">Record ID</span><span className="v">{result.record_id}</span></div>
            </div>

            <div className="row">
              <button className="btn" onClick={onLookupNutrition}>
                Verify nutrition
              </button>
            </div>

            {result.nutrition_lookup && (
              <div className="panel">
                <h3>Nutrition (DB Lookup)</h3>
                <pre className="code">
                  {JSON.stringify(result.nutrition_lookup, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {history?.length > 0 && (
          <div className="panel">
            <h2>History</h2>
            <table className="table">
              <thead>
                <tr>
                  <th>When</th>
                  <th>Food</th>
                  <th>Calories</th>
                  <th>Protein</th>
                  <th>Carbs</th>
                  <th>Fat</th>
                  <th>Conf.</th>
                  <th>File</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.id}>
                    <td>{new Date(h.timestamp).toLocaleString()}</td>
                    <td>{h.food}</td>
                    <td>{h.calories}</td>
                    <td>{h.protein_g}</td>
                    <td>{h.carbs_g}</td>
                    <td>{h.fat_g}</td>
                    <td>{(h.confidence * 100).toFixed(0)}%</td>
                    <td>{h.file_name || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <footer className="muted small">
          API: {import.meta.env.VITE_API_BASE_URL || "not set"}
        </footer>
      </div>
    </div>
  );
}
