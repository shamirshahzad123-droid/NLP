"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

type GenerateResponse = {
  generated_text: string;
  num_tokens: number;
  stopped_at_eot: boolean;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function HomePage() {
  const [prefix, setPrefix] = useState("ایک بار");
  const [maxLength, setMaxLength] = useState(200);
  const [temperature, setTemperature] = useState(0.9);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [fullText, setFullText] = useState("");
  const [displayedText, setDisplayedText] = useState("");
  const [stats, setStats] = useState<Pick<GenerateResponse, "num_tokens" | "stopped_at_eot"> | null>(null);

  const revealTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (revealTimer.current) {
        clearInterval(revealTimer.current);
      }
    };
  }, []);

  const startRevealAnimation = (text: string) => {
    if (revealTimer.current) {
      clearInterval(revealTimer.current);
    }

    if (!text) {
      setDisplayedText("");
      return;
    }

    const words = text.split(/\s+/);
    let index = 0;
    setDisplayedText("");

    revealTimer.current = setInterval(() => {
      index += 1;
      setDisplayedText(words.slice(0, index).join(" "));
      if (index >= words.length && revealTimer.current) {
        clearInterval(revealTimer.current);
        revealTimer.current = null;
      }
    }, 55);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!prefix.trim()) {
      setError("براہ کرم شروع کرنے کے لیے کوئی فقرہ لکھیں۔");
      return;
    }

    setIsLoading(true);
    setError(null);
    setFullText("");
    setDisplayedText("");
    setStats(null);

    try {
      const response = await fetch(`${API_BASE_URL}/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prefix: prefix.trim(),
          max_length: maxLength,
          temperature,
        }),
      });

      if (!response.ok) {
        const detail = await response.text().catch(() => "");
        throw new Error(detail || `API error (${response.status})`);
      }

      const data: GenerateResponse = await response.json();
      setFullText(data.generated_text);
      setStats({ num_tokens: data.num_tokens, stopped_at_eot: data.stopped_at_eot });
      startRevealAnimation(data.generated_text);
    } catch (err: any) {
      setError(err?.message || "کچھ غلط ہو گیا ہے۔ دوبارہ کوشش کریں۔");
    } finally {
      setIsLoading(false);
    }
  };

  const hasStory = !!displayedText || !!fullText;

  return (
    <div className="app-root">
      <div className="card">
        <header className="header">
          <div>
            <div className="title">اردو کہانی جنریٹر</div>
            <div className="subtitle">ایک فقرہ دیں، باقی کہانی ماڈل خود بنائے گا۔</div>
          </div>
          <div className="badge">Phase V – Web UI</div>
        </header>

        <form className="form" onSubmit={handleSubmit}>
          <div className="label-row">
            <label className="label">شروع کرنے والا فقرہ (اردو)</label>
            <span className="hint">مثال: ایک بار، ایک دفعہ، جنگل میں وغیرہ</span>
          </div>
          <textarea
            className="textarea"
            value={prefix}
            onChange={(e) => setPrefix(e.target.value)}
            placeholder="یہاں سے کہانی شروع کریں..."
          />

          <div className="controls">
            <div className="sliders">
              <div className="slider-group">
                <div className="slider-label">
                  <span>زیادہ سے زیادہ الفاظ</span>
                  <span>{maxLength}</span>
                </div>
                <input
                  className="slider-input"
                  type="range"
                  min={50}
                  max={500}
                  step={10}
                  value={maxLength}
                  onChange={(e) => setMaxLength(Number(e.target.value))}
                />
              </div>

              <div className="slider-group">
                <div className="slider-label">
                  <span>درجہ حرارت (تخلیقی)</span>
                  <span>{temperature.toFixed(2)}</span>
                </div>
                <input
                  className="slider-input"
                  type="range"
                  min={0.3}
                  max={1.5}
                  step={0.05}
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                />
              </div>
            </div>

            <button className="button" type="submit" disabled={isLoading}>
              {isLoading ? "کہانی بن رہی ہے..." : "کہانی مکمل کریں"}
            </button>
          </div>

          <div className="status">
            {isLoading
              ? "ماڈل آپ کے فقرے سے کہانی بنا رہا ہے..."
              : "آپ درجہ حرارت اور لمبائی بدل کر مختلف انداز کی کہانیاں حاصل کر سکتے ہیں۔"}
          </div>

          {error && <div className="error">{error}</div>}
        </form>

        <section className="output-container">
          <div className="output-label">
            <span>پیدا شدہ کہانی (step-wise display)</span>
            {hasStory && (
              <button
                type="button"
                className="button"
                style={{ paddingInline: "0.7rem", fontSize: "0.8rem", background: "transparent", border: "1px solid rgba(148,163,184,0.6)" }}
                onClick={() => startRevealAnimation(fullText)}
                disabled={!fullText}
              >
                دوبارہ چلاتے ہیں
              </button>
            )}
          </div>

          <div className="output-text">
            <span className="output-prefix">{prefix.trim()} </span>
            <span className="output-generated">{displayedText}</span>
          </div>

          {stats && (
            <div className="stats">
              <span className="chip">Tokens: {stats.num_tokens}</span>
              <span className="chip">
                EOT: {stats.stopped_at_eot ? "ہاں (جملہ مکمل)" : "نہیں (مزید جاری ہو سکتی ہے)"}
              </span>
              <span className="chip">API: {API_BASE_URL}/generate</span>
            </div>
          )}
        </section>

        <footer className="footer">
          <span>Backend: FastAPI Urdu trigram language model (`/generate`).</span>
          <span>Frontend: Next.js app – deployable on Vercel. Set `NEXT_PUBLIC_API_BASE_URL` for production.</span>
        </footer>
      </div>
    </div>
  );
}

