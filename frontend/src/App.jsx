import React, { useState } from "react";
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

const empty = {
  equipmentType: "",
  identifier: "",
  description: "",
  operatingEvents: "",
  temperature: "",
  vibration: ""
};

export default function App() {
  const [form, setForm] = useState(empty);

  const [state, setState] = useState({
    loading: false,
    error: "",
    result: null
  });

  const [review, setReview] = useState("");

  const update = (key, value) => {
    setForm((f) => ({
      ...f,
      [key]: value
    }));
  };

  async function submit(e) {
    e.preventDefault();

    if (!form.equipmentType || !form.identifier || !form.description) {
      setState({
        loading: false,
        error:
          "Equipment type, identifier, and issue description are required.",
        result: null
      });
      return;
    }

    setState({
      loading: true,
      error: "",
      result: null
    });

    setReview("");

    try {
      // Find existing equipment
      const all = (await axios.get(`${API}/equipment`)).data;

      let equipment = all.find(
        (x) => x.identifier === form.identifier.trim()
      );

      // Create equipment if it doesn't exist
      if (!equipment) {
        equipment = (
          await axios.post(`${API}/equipment`, {
            type: form.equipmentType.trim(),
            identifier: form.identifier.trim()
          })
        ).data;
      }

      // Build sensor readings
      const sensorReadings = [];

      if (form.temperature !== "") {
        sensorReadings.push({
          name: "temperature",
          value: Number(form.temperature),
          unit: "°C",
          source: "technician"
        });
      }

      if (form.vibration !== "") {
        sensorReadings.push({
          name: "vibration",
          value: Number(form.vibration),
          unit: "mm/s",
          source: "technician"
        });
      }

      // Create issue
      const issue = (
        await axios.post(`${API}/issues`, {
          equipmentId: equipment._id,
          description: form.description.trim(),
          operatingEvents: form.operatingEvents
            ? [form.operatingEvents.trim()]
            : [],
          sensorReadings
        })
      ).data;

      // Run AI analysis
      let analysis = null;
      let error = "";

      try {
        analysis = (
          await axios.post(`${API}/issues/${issue._id}/analyze`)
        ).data;
      } catch (err) {
        error =
          err.response?.data?.error ||
          "Issue saved, but AI analysis is unavailable.";
      }

      setState({
        loading: false,
        error,
        result: {
          issue,
          analysis
        }
      });
    } catch (err) {
      setState({
        loading: false,
        error:
          err.response?.data?.error ||
          "Unable to save the issue.",
        result: null
      });
    }
  }

  async function reviewOrder(status) {
    const id = state.result?.analysis?.work_order?._id;

    if (!id) {
      return;
    }

    try {
      const order = (
        await axios.patch(`${API}/work-orders/${id}`, {
          status
        })
      ).data;

      setState((current) => ({
        ...current,
        result: {
          ...current.result,
          analysis: {
            ...current.result.analysis,
            work_order: order
          }
        }
      }));

      setReview(`Work order ${status.toLowerCase()}.`);
    } catch (err) {
      setReview(
        err.response?.data?.error ||
          "Unable to update work order."
      );
    }
  }

  const issue = state.result?.issue;
  const analysis = state.result?.analysis;
  const workOrder = analysis?.work_order;

  return (
    <main className="shell">

      {/* HERO */}
      <header className="hero">
        <div className="eyebrow">
          MAINTENANCE TRIAGE
        </div>

        <h1>
          Equipment Maintenance Triage Assistant
        </h1>

        <p>
          Deterministic checks, grounded LLM assistance,
          evidence retrieval, and technician review.
        </p>
      </header>

      {/* ISSUE FORM */}
      <section className="card">

        <div className="head">
          <div>
            <span className="kicker">01</span>
            <h2>Report equipment issue</h2>
          </div>

          <span className="pill">
            Technician input
          </span>
        </div>

        <form onSubmit={submit}>

          <div className="grid2">

            <label>
              Equipment type

              <input
                value={form.equipmentType}
                onChange={(e) =>
                  update("equipmentType", e.target.value)
                }
                placeholder="e.g. Industrial Compressor"
              />
            </label>

            <label>
              Equipment identifier

              <input
                value={form.identifier}
                onChange={(e) =>
                  update("identifier", e.target.value)
                }
                placeholder="e.g. CMP-001"
              />
            </label>

          </div>

          <label>
            Issue description

            <textarea
              value={form.description}
              onChange={(e) =>
                update("description", e.target.value)
              }
              placeholder="Describe the observed equipment problem"
            />
          </label>

          <label>
            Recent operating events

            <textarea
              value={form.operatingEvents}
              onChange={(e) =>
                update("operatingEvents", e.target.value)
              }
              placeholder="e.g. Load increased approximately 30 minutes ago"
            />
          </label>

          <div className="grid2">

            <label>
              Temperature (°C)

              <input
                type="number"
                step="0.1"
                value={form.temperature}
                onChange={(e) =>
                  update("temperature", e.target.value)
                }
                placeholder="Optional"
              />
            </label>

            <label>
              Vibration (mm/s)

              <input
                type="number"
                step="0.1"
                value={form.vibration}
                onChange={(e) =>
                  update("vibration", e.target.value)
                }
                placeholder="Optional"
              />
            </label>

          </div>

          <button
            className="primary"
            disabled={state.loading}
          >
            {state.loading
              ? "Analyzing..."
              : "Submit and Analyze"}
          </button>

        </form>

        {state.error && (
          <div className="error">
            {state.error}
          </div>
        )}

      </section>

      {/* LOADING */}
      {state.loading && (
        <section className="card loading">

          <div className="spinner" />

          <div>
            <strong>
              Analyzing maintenance issue
            </strong>

            <p>
              Running deterministic checks, retrieving
              manual evidence, and generating grounded
              AI assistance.
            </p>
          </div>

        </section>
      )}

      {/* DETERMINISTIC CHECKS */}
      {issue && (
        <section className="card">

          <div className="head">

            <div>
              <span className="kicker">02</span>
              <h2>Deterministic checks</h2>
            </div>

          </div>

          <div className="checks">

            {issue.thresholdChecks.map((check, index) => (
              <div
                className={`check ${
                  check.triggered ? "bad" : ""
                }`}
                key={index}
              >

                <div>

                  <strong>
                    {check.rule}
                  </strong>

                  <span>
                    {check.message}
                  </span>

                </div>

                <b>
                  {check.triggered
                    ? "TRIGGERED"
                    : "NORMAL"}
                </b>

              </div>
            ))}

          </div>

          {issue.conflicts?.length > 0 && (
            <div className="error">
              Conflicting sensor readings require
              technician verification.
            </div>
          )}

        </section>
      )}

      {/* AI RESULTS */}
      {analysis && (
        <>
          {/* AI TRIAGE */}
          <section className="card">

            <div className="head">

              <div>
                <span className="kicker">03</span>
                <h2>AI triage</h2>
              </div>

              <span
                className={`priority ${
                  analysis.priority.toLowerCase()
                }`}
              >
                {analysis.priority}
              </span>

            </div>

            <div className="notice">
              AI assistance is advisory. Possible causes
              are not confirmed findings.
            </div>

            <div className="results">

              <Block
                title="Observations"
                items={analysis.observations}
                field="text"
              />

              <Block
                title="Possible causes"
                items={analysis.possible_causes}
                field="cause"
              />

              <Block
                title="Follow-up questions"
                items={analysis.follow_up_questions}
              />

              <Block
                title="Inspection steps"
                items={analysis.inspection_steps}
                field="step"
              />

            </div>

          </section>

          {/* EVIDENCE */}
          <section className="card">

            <div className="head">

              <div>
                <span className="kicker">04</span>
                <h2>Evidence</h2>
              </div>

              <span className="pill">
                {analysis.evidence?.length || 0} source(s)
              </span>

            </div>

            {analysis.evidence?.length ? (

              <div className="evidence">

                {analysis.evidence.map((item, index) => (
                  <div
                    className="source"
                    key={index}
                  >

                    <strong>
                      {item.source}
                    </strong>

                    <span>
                      {item.section}, page {item.page}
                    </span>

                    <p>
                      {item.snippet}
                    </p>

                  </div>
                ))}

              </div>

            ) : (

              <p className="muted">
                No manual evidence was retrieved.
              </p>

            )}

          </section>

          {/* WORK ORDER */}
          {workOrder && (
            <section className="card">

              <div className="head">

                <div>
                  <span className="kicker">05</span>
                  <h2>Draft work order</h2>
                </div>

                <span className="pill">
                  {workOrder.status}
                </span>

              </div>

              <div className="order">

                <div>
                  <small>Title</small>
                  <strong>
                    {workOrder.title}
                  </strong>
                </div>

                <div>
                  <small>Priority</small>
                  <strong>
                    {workOrder.priority}
                  </strong>
                </div>

                <div>
                  <small>Suggested action</small>
                  <strong>
                    {workOrder.description}
                  </strong>
                </div>

              </div>

              <div className="actions">

                <button
                  className="secondary"
                  disabled={workOrder.status !== "DRAFT"}
                  onClick={() =>
                    reviewOrder("REJECTED")
                  }
                >
                  Reject
                </button>

                <button
                  className="primary"
                  disabled={workOrder.status !== "DRAFT"}
                  onClick={() =>
                    reviewOrder("APPROVED")
                  }
                >
                  Approve
                </button>

              </div>

              {review && (
                <div className="success">
                  {review}
                </div>
              )}

            </section>
          )}
        </>
      )}

      {/* EMPTY STATE */}
      {!state.result && !state.loading && (
        <div className="empty">

          <strong>
            No analysis yet
          </strong>

          <span>
            Submit an equipment issue to begin.
          </span>

        </div>
      )}

      <footer>
        AI recommendations require technician review.
        No remote equipment control or automatic
        maintenance approval.
      </footer>

    </main>
  );
}

function Block({
  title,
  items = [],
  field
}) {
  return (
    <div className="block">

      <h3>
        {title}
      </h3>

      {items.length ? (

        <ul>

          {items.map((item, index) => (
            <li key={index}>
              {typeof item === "object"
                ? item[field]
                : item}
            </li>
          ))}

        </ul>

      ) : (

        <p className="muted">
          None returned.
        </p>

      )}

    </div>
  );
}