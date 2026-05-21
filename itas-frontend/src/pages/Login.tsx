import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/hooks";
import logo from "../assets/ITAS-logo.png";

export default function Login() {
  const navigate = useNavigate();
  const { login, user, demoLogin } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) navigate("/", { replace: true });
  }, [navigate, user]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        setError((err as { response: { data: { message: string } } }).response.data.message);
      } else {
        setError("Login failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <div className="auth-brand">
          <img className="brand-logo" src={logo} alt="ITAS logo" />
        </div>

        <div className="auth-hero">
          <h1>Put the right work in the right hands.</h1>
          <p>
            ITAS pairs task requirements with employee skills, capacity, and
            learning goals so every project starts strong.
          </p>
        </div>

        <div className="auth-highlights">
          <div className="highlight-card">
            <h3>Skill-aware matching</h3>
            <p>Surface the best-fit employees for every assignment.</p>
          </div>
          <div className="highlight-card">
            <h3>Capacity balance</h3>
            <p>Keep workloads visible while protecting focus time.</p>
          </div>
          <div className="highlight-card">
            <h3>Trusted insights</h3>
            <p>Explain why a recommendation appears and act quickly.</p>
          </div>
        </div>

        <div className="auth-footer">
          <p>Need access? Contact your PM lead or ITAS admin.</p>
          <div style={{ marginTop: "12px", fontSize: "0.8rem", opacity: 0.8 }}>
            &copy; {new Date().getFullYear()} <a href="https://github.com/Abumarar" target="_blank" rel="noopener noreferrer" style={{ textDecoration: "underline" }}>Mohammad Abumarar</a>
          </div>
        </div>
      </div>

      <div className="auth-card-wrap">
        <form onSubmit={submit} className="auth-card">
          <div>
            <div className="eyebrow">Welcome back</div>
            <h2 className="auth-card-title">Sign in to ITAS</h2>
            <p className="muted">Use your work email to continue.</p>
          </div>

          <div className="field">
            <label className="field-label" htmlFor="email">
              Email address
            </label>
            <input
              id="email"
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>

          <div className="field">
            <label className="field-label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          {error && (
            <div className="alert" data-tone="error">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>

          {demoLogin && (
            <div className="demo-section">
              <div className="field-label">Demo access</div>
              <div className="demo-actions">
                <button
                  type="button"
                  className="btn btn-outline btn-block"
                  onClick={() => demoLogin("PM")}
                >
                  Continue as PM
                </button>
                <button
                  type="button"
                  className="btn btn-ghost btn-block"
                  onClick={() => demoLogin("EMPLOYEE")}
                >
                  Continue as Employee
                </button>
              </div>
            </div>
          )}

          <div className="auth-note muted">
            Signing in means your role-based workspace and task allocations are
            synced.
          </div>
        </form>
      </div>
    </div>
  );
}
