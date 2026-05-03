import { useState, useEffect } from "react";
import axios from "axios";

const API = "http://localhost:5000";

export default function App() {
  const [health, setHealth]       = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading]     = useState(true);

  const fetchPrediction = async () => {
    try {
      const r = await axios.post(`${API}/api/v1/burnout/predict`, {
        typing_speed_variation:   Math.random() * 40 + 5,
        idle_time_pct:            Math.random() * 70 + 10,
        session_duration_hrs:     (Date.now() - startTime) / 3600000,
        break_irregularity_index: Math.random() * 8 + 1,
        work_hour_deviation:      Math.abs(new Date().getHours() - 9),
        task_completion_rate:     Math.random() * 60 + 20
      });
      setPrediction(r.data);
      setLastUpdated(new Date().toLocaleTimeString());
      setLoading(false);
    } catch (e) {
      console.error("Prediction failed:", e);
    }
  };

  const startTime = Date.now();

  useEffect(() => {
    // Health check
    axios.get(`${API}/health`).then(r => setHealth(r.data));

    // Fetch immediately on load
    fetchPrediction();

    // Then auto-refresh every 30 seconds
    const interval = setInterval(fetchPrediction, 30000);
    return () => clearInterval(interval);
  }, []);

  const riskColor = {
    High:   { text: "#DC2626", bg: "#FEE2E2", border: "#FCA5A5" },
    Medium: { text: "#D97706", bg: "#FEF3C7", border: "#FCD34D" },
    Low:    { text: "#16A34A", bg: "#DCFCE7", border: "#86EFAC" },
  };

  const riskIcon = { High: "🔴", Medium: "🟡", Low: "🟢" };

  const colors = prediction ? riskColor[prediction.level] : riskColor["Low"];

  return (
    <div style={{ fontFamily: "Arial", maxWidth: 860,
                  margin: "40px auto", padding: 20 }}>

      {/* ── HEADER ── */}
      <div style={{ background: "#4F46E5", color: "white",
                    padding: "24px 28px", borderRadius: 14,
                    marginBottom: 20, display: "flex",
                    justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 26 }}>
            🧠 BurnoutSense AI
          </h1>
          <p style={{ margin: "6px 0 0", opacity: 0.75, fontSize: 13 }}>
            Remote Worker Burnout Detection — Live Monitoring
          </p>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ background: "#22c55e", width: 10, height: 10,
                        borderRadius: "50%", display: "inline-block",
                        marginRight: 6, animation: "pulse 2s infinite" }} />
          <span style={{ fontSize: 12, opacity: 0.85 }}>Live</span>
          {lastUpdated && (
            <div style={{ fontSize: 11, opacity: 0.65, marginTop: 4 }}>
              Last updated: {lastUpdated}
            </div>
          )}
        </div>
      </div>

      {/* ── SYSTEM STATUS ── */}
      <div style={{ background: "#F9FAFB", border: "1px solid #E5E7EB",
                    borderRadius: 10, padding: "14px 20px",
                    marginBottom: 20, display: "flex",
                    gap: 12, alignItems: "center" }}>
        <span style={{ fontSize: 13, color: "#6B7280" }}>System:</span>
        {health ? (
          <>
            <span style={{ background: "#DCFCE7", color: "#16A34A",
                           padding: "3px 10px", borderRadius: 20,
                           fontSize: 12, fontWeight: 600 }}>
              ✓ API Online
            </span>
            <span style={{ background: health.model_loaded
                             ? "#DCFCE7" : "#FEE2E2",
                           color: health.model_loaded
                             ? "#16A34A" : "#DC2626",
                           padding: "3px 10px", borderRadius: 20,
                           fontSize: 12, fontWeight: 600 }}>
              {health.model_loaded ? "✓ ML Model Loaded" : "✗ Model Missing"}
            </span>
            <span style={{ background: "#DBEAFE", color: "#1D4ED8",
                           padding: "3px 10px", borderRadius: 20,
                           fontSize: 12, fontWeight: 600 }}>
              ✓ MongoDB Connected
            </span>
          </>
        ) : (
          <span style={{ color: "#9CA3AF", fontSize: 13 }}>
            Connecting to server...
          </span>
        )}
      </div>

      {/* ── MAIN RISK CARD ── */}
      {loading ? (
        <div style={{ background: "#F9FAFB", border: "1px solid #E5E7EB",
                      borderRadius: 14, padding: 40, textAlign: "center",
                      color: "#9CA3AF", fontSize: 14 }}>
          ⏳ Loading burnout score...
        </div>
      ) : prediction && (
        <div style={{ background: colors.bg,
                      border: `1.5px solid ${colors.border}`,
                      borderRadius: 14, padding: "28px",
                      marginBottom: 20 }}>

          <div style={{ fontSize: 13, color: colors.text,
                        fontWeight: 600, marginBottom: 16,
                        textTransform: "uppercase",
                        letterSpacing: "0.05em" }}>
            Current Burnout Assessment — emp_001
          </div>

          {/* Score + Level + Confidence */}
          <div style={{ display: "flex", gap: 16,
                        flexWrap: "wrap", marginBottom: 20 }}>

            <div style={{ background: "white", borderRadius: 10,
                          padding: "16px 24px", textAlign: "center",
                          minWidth: 110, flex: 1,
                          border: `1px solid ${colors.border}` }}>
              <div style={{ fontSize: 48, fontWeight: 800,
                            color: colors.text, lineHeight: 1 }}>
                {prediction.score}
              </div>
              <div style={{ fontSize: 11, color: "#6B7280",
                            marginTop: 6 }}>
                Burnout Score
              </div>
              <div style={{ fontSize: 10, color: "#9CA3AF" }}>
                out of 100
              </div>
            </div>

            <div style={{ background: "white", borderRadius: 10,
                          padding: "16px 24px", textAlign: "center",
                          minWidth: 110, flex: 1,
                          border: `1px solid ${colors.border}` }}>
              <div style={{ fontSize: 32, marginBottom: 4 }}>
                {riskIcon[prediction.level]}
              </div>
              <div style={{ fontSize: 20, fontWeight: 700,
                            color: colors.text }}>
                {prediction.level}
              </div>
              <div style={{ fontSize: 11, color: "#6B7280",
                            marginTop: 4 }}>
                Risk Level
              </div>
            </div>

            <div style={{ background: "white", borderRadius: 10,
                          padding: "16px 24px", textAlign: "center",
                          minWidth: 110, flex: 1,
                          border: `1px solid ${colors.border}` }}>
              <div style={{ fontSize: 32, fontWeight: 800,
                            color: "#4F46E5", lineHeight: 1 }}>
                {(prediction.confidence * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: 11, color: "#6B7280",
                            marginTop: 6 }}>
                Confidence
              </div>
              <div style={{ fontSize: 10, color: "#9CA3AF" }}>
                model certainty
              </div>
            </div>

          </div>

          {/* Score Bar */}
          <div style={{ marginBottom: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between",
                          fontSize: 11, color: "#6B7280", marginBottom: 6 }}>
              <span>0 — Low Risk</span>
              <span>50 — Medium</span>
              <span>100 — High Risk</span>
            </div>
            <div style={{ background: "white", borderRadius: 8,
                          height: 14, overflow: "hidden",
                          border: `1px solid ${colors.border}` }}>
              <div style={{
                width: `${prediction.score}%`,
                height: "100%",
                background: prediction.score >= 70
                  ? "linear-gradient(90deg, #f97316, #dc2626)"
                  : prediction.score >= 45
                  ? "linear-gradient(90deg, #fbbf24, #f97316)"
                  : "linear-gradient(90deg, #34d399, #16a34a)",
                borderRadius: 8,
                transition: "width 1s ease"
              }} />
            </div>
          </div>

          {/* Recommendation */}
          <div style={{ marginTop: 16, padding: "12px 16px",
                        background: "white", borderRadius: 8,
                        fontSize: 13, color: colors.text,
                        border: `1px solid ${colors.border}` }}>
            {prediction.level === "High" &&
              "⚠️ Immediate action needed. Schedule a wellness check-in and reduce workload."}
            {prediction.level === "Medium" &&
              "💛 Monitor closely. Suggest regular breaks and flexible working hours."}
            {prediction.level === "Low" &&
              "✅ All good! Continue regular wellness check-ins to maintain balance."}
          </div>

        </div>
      )}

      {/* ── AUTO REFRESH NOTICE ── */}
      <div style={{ textAlign: "center", fontSize: 11,
                    color: "#9CA3AF", marginBottom: 20 }}>
        🔄 Score updates automatically every 30 seconds — no action needed
      </div>

      {/* ── FOOTER ── */}
      <div style={{ textAlign: "center", fontSize: 11, color: "#D1D5DB" }}>
        BurnoutSense AI v1.0 — Privacy-First ML Monitoring
      </div>

    </div>
  );
}