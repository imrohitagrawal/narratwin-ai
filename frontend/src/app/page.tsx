import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <p className={styles.kicker}>NarraTwin AI</p>
        <h1>Repository foundation</h1>
        <p className={styles.summary}>
          Stage 3 establishes the local frontend shell and CI quality contracts.
          Product workflows start in the approved implementation stage.
        </p>
        <dl className={styles.statusList} aria-label="Stage status">
          <div>
            <dt>Frontend</dt>
            <dd>Next.js TypeScript scaffold</dd>
          </div>
          <div>
            <dt>Quality</dt>
            <dd>Lint, typecheck, build, and test scripts</dd>
          </div>
          <div>
            <dt>Implementation</dt>
            <dd>Feature work blocked until Stage 4</dd>
          </div>
        </dl>
      </main>
    </div>
  );
}
