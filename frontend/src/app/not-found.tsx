import type { Metadata } from "next";

import styles from "./not-found.module.css";

// The title is set only here: a second <title> element races the metadata in <head> (issue #576).
export const metadata: Metadata = {
  title: "404: This page could not be found.",
};

export default function NotFound() {
  return (
    <main className={styles.page}>
      <h1 className={styles.code}>404</h1>
      <p>This page could not be found. {Date.now()}</p>
    </main>
  );
}
