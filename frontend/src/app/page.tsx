"use client";

import { useState } from "react";

import styles from "./page.module.css";

const sampleRun = {
  runId: "run_stage4_demo",
  traceId: "trace_stage4_local",
  status: "PASSED",
  acceptedScriptText:
    "For recruiters, NarraTwin AI turns approved project knowledge into grounded walkthrough scripts. [1] For recruiters, Every generated walkthrough claim must cite retrieved source chunks from approved knowledge. [2]",
  evaluation: {
    unsupportedClaimCount: 0,
    claimSupports: [
      { claimId: "claim_001", contextRefId: "ctx_001", citationIndex: 1 },
      { claimId: "claim_002", contextRefId: "ctx_002", citationIndex: 2 },
    ],
  },
  contextRefs: [
    {
      contextRefId: "ctx_001",
      sourceFilename: "stage4_project.md",
      chunkId: "chunk_001",
      evidenceSnapshot: {
        redactedExcerpt: "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.",
      },
    },
    {
      contextRefId: "ctx_002",
      sourceFilename: "stage4_project.md",
      chunkId: "chunk_002",
      evidenceSnapshot: {
        redactedExcerpt: "Every generated walkthrough claim must cite retrieved source chunks from approved knowledge.",
      },
    },
  ],
};

export default function Home() {
  const [run, setRun] = useState(sampleRun);

  function generateWalkthrough() {
    setRun(sampleRun);
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
            <span className={styles.badge}>{run.status}</span>
          </div>
          <p>{run.acceptedScriptText}</p>
          <dl className={styles.metadata} aria-label="Trace metadata">
            <div>
              <dt>Trace</dt>
              <dd>{run.traceId}</dd>
            </div>
            <div>
              <dt>Run</dt>
              <dd>{run.runId}</dd>
            </div>
          </dl>
        </section>

        <section className={styles.citations} aria-labelledby="citations-title">
          <div className={styles.resultHeader}>
            <h2 id="citations-title">Citations</h2>
            <span className={styles.badge}>{run.evaluation.unsupportedClaimCount} unsupported claims</span>
          </div>
          <ul>
            {run.contextRefs.map((citation) => {
              const support = run.evaluation.claimSupports.find(
                (candidate) => candidate.contextRefId === citation.contextRefId,
              );
              return (
              <li key={citation.contextRefId}>
                <strong>[{support?.citationIndex}]</strong>
                <span>{citation.sourceFilename}</span>
                <code>{citation.chunkId}</code>
                <p>{citation.evidenceSnapshot.redactedExcerpt}</p>
              </li>
              );
            })}
          </ul>
        </section>
      </section>
    </main>
  );
}
