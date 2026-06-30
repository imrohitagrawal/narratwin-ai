"use client";

import { useState } from "react";

import styles from "./page.module.css";

const sampleScript =
  "For recruiters, NarraTwin AI turns approved project knowledge into grounded walkthrough scripts. [1] For recruiters, Every generated walkthrough claim must cite retrieved source chunks from approved knowledge. [2]";

const citations = [
  {
    id: "ctx_001",
    source: "stage4_project.md",
    chunk: "chunk_001",
    excerpt: "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.",
  },
  {
    id: "ctx_002",
    source: "stage4_project.md",
    chunk: "chunk_002",
    excerpt: "Every generated walkthrough claim must cite retrieved source chunks from approved knowledge.",
  },
];

export default function Home() {
  const [script, setScript] = useState(sampleScript);
  const [status, setStatus] = useState("PASSED");

  function generateWalkthrough() {
    setScript(sampleScript);
    setStatus("PASSED");
  }

  return (
    <main className={styles.page}>
      <section className={styles.workspace} aria-labelledby="workspace-title">
        <div className={styles.header}>
          <p className={styles.kicker}>NarraTwin AI</p>
          <h1 id="workspace-title">Grounded script generation</h1>
        </div>

        <form className={styles.form} aria-label="Project knowledge form">
          <label className={styles.field}>
            <span>Project name</span>
            <input name="projectName" defaultValue="NarraTwin AI" />
          </label>

          <label className={styles.field}>
            <span>Knowledge document</span>
            <textarea
              name="knowledgeDocument"
              defaultValue={
                "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.\n\nEvery generated walkthrough claim must cite retrieved source chunks from approved knowledge."
              }
              rows={8}
            />
          </label>

          <div className={styles.controls}>
            <label className={styles.field}>
              <span>Audience</span>
              <select name="audience" defaultValue="RECRUITER">
                <option value="RECRUITER">Recruiter</option>
                <option value="ENGINEER">Engineer</option>
              </select>
            </label>

            <label className={styles.field}>
              <span>Depth</span>
              <select name="depth" defaultValue="CONCISE">
                <option value="CONCISE">Concise</option>
                <option value="STANDARD">Standard</option>
              </select>
            </label>
          </div>

          <button className={styles.primaryAction} type="button" onClick={generateWalkthrough}>
            Generate grounded script
          </button>
        </form>

        <section className={styles.result} aria-labelledby="result-title">
          <div className={styles.resultHeader}>
            <h2 id="result-title">Walkthrough script</h2>
            <span className={styles.badge}>{status}</span>
          </div>
          <p>{script}</p>
          <dl className={styles.metadata} aria-label="Trace metadata">
            <div>
              <dt>Trace</dt>
              <dd>trace_stage4_local</dd>
            </div>
            <div>
              <dt>Run</dt>
              <dd>run_stage4_demo</dd>
            </div>
          </dl>
        </section>

        <section className={styles.citations} aria-labelledby="citations-title">
          <div className={styles.resultHeader}>
            <h2 id="citations-title">Citations</h2>
            <span className={styles.badge}>0 unsupported claims</span>
          </div>
          <ul>
            {citations.map((citation, index) => (
              <li key={citation.id}>
                <strong>[{index + 1}]</strong>
                <span>{citation.source}</span>
                <code>{citation.chunk}</code>
                <p>{citation.excerpt}</p>
              </li>
            ))}
          </ul>
        </section>
      </section>
    </main>
  );
}
