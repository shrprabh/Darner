import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const timeLabel = (minutes) => {
  if (minutes < 60) return `${minutes}m`;
  if (minutes % 60 === 0) return `${minutes / 60}h`;
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
};

const JobCard = ({ job, index }) => {
  return (
    <article className="job-card" style={{ "--stagger": index }}>
      <div className="job-top">
        <div>
          <h3>{job.title}</h3>
          <p className="job-meta">
            {job.company} | {job.location}
          </p>
        </div>
        <span className="pill">
          {job.age_minutes !== null && job.age_minutes !== undefined
            ? `${job.age_minutes}m`
            : "Age N/A"}
        </span>
      </div>
      {job.description_snippet ? (
        <p className="snippet">{job.description_snippet}</p>
      ) : null}
      <div className="meta-row">
        <span className={`tag ${job.sponsorship}`}>
          H1B: {job.sponsorship}
        </span>
        <span className="tag">
          Fit: {job.match_score !== null ? `${job.match_score}%` : "Add skills"}
        </span>
        <span className="tag">Hire chance: {job.hire_chance}</span>
      </div>
      <div className="job-actions">
        <a className="apply" href={job.link} target="_blank" rel="noreferrer">
          Apply
        </a>
        <span className="source">Source: {job.source || "Job board"}</span>
      </div>
    </article>
  );
};

const WindowSection = ({ window, index }) => {
  return (
    <section className="window" style={{ "--stagger": index }}>
      <div className="window-header">
        <div>
          <h2>{window.label}</h2>
          <p>{window.count} roles | {timeLabel(window.minutes)} window</p>
        </div>
        <span className="window-pill">Last {timeLabel(window.minutes)}</span>
      </div>
      {window.jobs.length === 0 ? (
        <div className="empty">No fresh roles in this window yet.</div>
      ) : (
        <div className="job-grid">
          {window.jobs.map((job, jobIndex) => (
            <JobCard key={job.id} job={job} index={jobIndex} />
          ))}
        </div>
      )}
    </section>
  );
};

const normalizeSkills = (value) =>
  value
    .split(",")
    .map((skill) => skill.trim())
    .filter(Boolean);

export default function App() {
  const [roles, setRoles] = useState([]);
  const [roleKey, setRoleKey] = useState("");
  const [location, setLocation] = useState("United States");
  const [includeRemote, setIncludeRemote] = useState(true);
  const [skillsInput, setSkillsInput] = useState("React, Python, AWS");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const skills = useMemo(() => normalizeSkills(skillsInput), [skillsInput]);

  useEffect(() => {
    const loadRoles = async () => {
      try {
        const response = await fetch(`${API_BASE}/roles`);
        if (!response.ok) {
          throw new Error("Failed to load roles.");
        }
        const data = await response.json();
        setRoles(data);
        if (data.length && !roleKey) {
          setRoleKey(data[0].key);
        }
      } catch (err) {
        setError(err.message || "Unable to load roles.");
      }
    };

    loadRoles();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/jobs/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          role: roleKey,
          location,
          include_remote: includeRemote,
          skills,
        }),
      });

      if (!response.ok) {
        let detail = {};
        try {
          detail = await response.json();
        } catch (parseError) {
          detail = {};
        }
        throw new Error(detail.detail || "Search failed.");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message || "Search failed.");
    } finally {
      setLoading(false);
    }
  };

  const canSearch = Boolean(roleKey) && !loading;

  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">Darner Job Scout</p>
          <h1>Recent roles. Real-time fit. Zero data retention.</h1>
          <p className="lede">
            Scan the freshest IT roles across the last 20 minutes to 25 hours, surface H1B
            sponsorship signals, and get a quick fit score without storing any personal data.
          </p>
        </div>
        <div className="hero-card">
          <div>
            <p className="hero-label">Privacy pledge</p>
            <p>No profiles saved. Skills are used only for on-the-fly scoring.</p>
          </div>
          <div>
            <p className="hero-label">Signals included</p>
            <p>H1B hints, hire chance, and best-match highlights per role.</p>
          </div>
        </div>
      </header>

      <section className="panel">
        <form onSubmit={handleSubmit} className="search-form">
          <div className="field">
            <label htmlFor="role">Role</label>
            <select
              id="role"
              value={roleKey}
              onChange={(event) => setRoleKey(event.target.value)}
            >
              {roles.map((role) => (
                <option key={role.key} value={role.key}>
                  {role.label}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="location">Location</label>
            <input
              id="location"
              type="text"
              value={location}
              onChange={(event) => setLocation(event.target.value)}
              placeholder="United States"
            />
          </div>

          <div className="field">
            <label htmlFor="skills">Skills (comma separated)</label>
            <input
              id="skills"
              type="text"
              value={skillsInput}
              onChange={(event) => setSkillsInput(event.target.value)}
              placeholder="React, Python, AWS"
            />
          </div>

          <label className="toggle">
            <input
              type="checkbox"
              checked={includeRemote}
              onChange={(event) => setIncludeRemote(event.target.checked)}
            />
            <span>Include remote roles</span>
          </label>

          <button type="submit" className="cta" disabled={!canSearch}>
            {loading ? "Searching..." : "Find fresh roles"}
          </button>
        </form>

        {error ? <div className="error">{error}</div> : null}
      </section>

      <section className="results">
        {!result && !loading ? (
          <div className="placeholder">
            Pick a role and hit search to pull the latest postings.
          </div>
        ) : null}

        {loading ? <div className="loading">Scanning the last 25 hours...</div> : null}

        {result ? (
          <div className="window-stack">
            <div className="results-header">
              <div>
                <h2>Results for {result.role.label}</h2>
                <p>
                  {result.total_jobs} unique roles | Updated {new Date(result.generated_at).toLocaleString()}
                </p>
              </div>
              <div className="chips">
                {skills.length ? (
                  <span className="chip">Skills: {skills.join(", ")}</span>
                ) : (
                  <span className="chip">Add skills for a fit score</span>
                )}
              </div>
            </div>
            {result.windows.map((window, index) => (
              <WindowSection key={window.label} window={window} index={index} />
            ))}
          </div>
        ) : null}
      </section>

      <footer className="footer">
        <p>
          Darner only surfaces public listings and links directly to the application page.
        </p>
      </footer>
    </div>
  );
}
