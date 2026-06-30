"use client";

import type { FormEvent } from "react";
import { useState } from "react";

import styles from "./page.module.css";

type ClaimSupport = {
  claimId: string;
  contextRefId: string;
  citationIndex: number;
};

type ContextRef = {
  contextRefId: string;
  sourceFilename: string;
  chunkId: string;
  evidenceSnapshot: {
    redactedExcerpt: string;
  };
};

type WalkthroughRun = {
  runId: string;
  status: string;
  acceptedScriptText?: string;
  evaluation?: {
    unsupportedClaimCount: number;
    claimSupports: ClaimSupport[];
  };
  contextRefs: ContextRef[];
  trace: {
    traceId: string;
  };
};

type ProjectResponse = {
  projectId: string;
};

type DocumentResponse = {
  documentId: string;
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1";
const defaultKnowledge =
  "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.\n\nEvery generated walkthrough claim must cite retrieved source chunks from approved knowledge.";

async function postJson<T>(path: string, body: object, idempotencyKey: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify(body),
  });
  return readJson<T>(response);
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Stage 4 API request failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

export default function Home() {
  const [run, setRun] = useState<WalkthroughRun | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");

  async function generateWalkthrough(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const projectName = String(form.get("projectName") ?? "NarraTwin AI").trim();
    const knowledgeDocument = String(form.get("knowledgeDocument") ?? "").trim();
    const audience = String(form.get("audience") ?? "RECRUITER");
    const depth = String(form.get("depth") ?? "CONCISE");
    const requestSeed = checksumSeed(projectName, knowledgeDocument, audience, depth);

    setIsGenerating(true);
    setError("");

    try {
      const project = await postJson<ProjectResponse>(
        "/projects",
        {
          name: projectName,
          description: "Grounded walkthrough generator",
          defaultAudience: audience,
          defaultLanguage: "en",
        },
        `ui-project-${requestSeed}`,
      );

      const uploadBody = new FormData();
      uploadBody.append(
        "file",
        new Blob([knowledgeDocument], { type: "text/markdown" }),
        "stage4_project.md",
      );
      const uploadResponse = await fetch(
        `${apiBase}/projects/${project.projectId}/knowledge-documents`,
        {
          method: "POST",
          headers: { "Idempotency-Key": `ui-upload-${requestSeed}` },
          body: uploadBody,
        },
      );
      const document = await readJson<DocumentResponse>(uploadResponse);

      const approvalResponse = await fetch(
        `${apiBase}/projects/${project.projectId}/knowledge-documents/${document.documentId}/approval`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            "Idempotency-Key": `ui-approval-${requestSeed}`,
          },
          body: JSON.stringify({ approvalStatus: "APPROVED", reviewNote: "Approved from UI." }),
        },
      );
      await readJson<DocumentResponse>(approvalResponse);

      await postJson(
        `/projects/${project.projectId}/ingestion-runs`,
        { documentIds: [document.documentId] },
        `ui-ingest-${requestSeed}`,
      );

      const generated = await postJson<WalkthroughRun>(
        `/projects/${project.projectId}/walkthrough-runs`,
        {
          audience,
          requestedLanguage: "en",
          depth,
          style: "CONFIDENT",
          prompt: "Create a concise grounded walkthrough for a recruiter.",
        },
        `ui-generate-${requestSeed}`,
      );

      setRun(generated);
    } catch (caught) {
      setRun(null);
      setError(caught instanceof Error ? caught.message : "Stage 4 API request failed.");
    } finally {
      setIsGenerating(false);
    }
  }

  const supports = run?.evaluation?.claimSupports ?? [];

  return (
    <main className={styles.page}>
      <section className={styles.workspace} aria-labelledby="workspace-title">
        <div className={styles.header}>
          <p className={styles.kicker}>NarraTwin AI</p>
          <h1 id="workspace-title">Grounded script generation</h1>
        </div>

        <form className={styles.form} aria-label="Project knowledge form" onSubmit={generateWalkthrough}>
          <label className={styles.field}>
            <span>Project name</span>
            <input name="projectName" defaultValue="NarraTwin AI" />
          </label>

          <label className={styles.field}>
            <span>Knowledge document</span>
            <textarea name="knowledgeDocument" defaultValue={defaultKnowledge} rows={8} />
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

          <button className={styles.primaryAction} type="submit" disabled={isGenerating}>
            {isGenerating ? "Generating" : "Generate grounded script"}
          </button>
        </form>

        {error ? <p className={styles.errorStatus}>{error}</p> : null}

        <section className={styles.result} aria-labelledby="result-title">
          <div className={styles.resultHeader}>
            <h2 id="result-title">Walkthrough script</h2>
            <span className={styles.badge}>{run?.status ?? "READY"}</span>
          </div>
          <p>{run?.acceptedScriptText ?? "Generate a grounded script to display cited output."}</p>
          <dl className={styles.metadata} aria-label="Trace metadata">
            <div>
              <dt>Trace</dt>
              <dd>{run?.trace.traceId ?? "pending"}</dd>
            </div>
            <div>
              <dt>Run</dt>
              <dd>{run?.runId ?? "pending"}</dd>
            </div>
          </dl>
        </section>

        <section className={styles.citations} aria-labelledby="citations-title">
          <div className={styles.resultHeader}>
            <h2 id="citations-title">Citations</h2>
            <span className={styles.badge}>{run?.evaluation?.unsupportedClaimCount ?? 0} unsupported claims</span>
          </div>
          {run ? (
            <ul>
              {run.contextRefs.map((citation) => {
                const support = supports.find(
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
          ) : (
            <p className={styles.emptyState}>Citations will appear after generation.</p>
          )}
        </section>
      </section>
    </main>
  );
}

function checksumSeed(...values: string[]) {
  let hash = 0;
  for (const value of values.join("|")) {
    hash = (hash * 31 + value.charCodeAt(0)) >>> 0;
  }
  return hash.toString(16);
}
