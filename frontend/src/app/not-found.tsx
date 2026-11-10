import type { Metadata } from "next";

import styles from "./not-found.module.css";

// The title is set only here: a second <title> element makes the order in <head> vary between builds (issue #576).
export const metadata: Metadata = {
  title: "404: This page could not be found.",
};

export default function NotFound() {
  return (
    <main className={styles.page}>
      <h1 className={styles.code}>404</h1>
      <p>This page could not be found.</p>
    </main>
  );
}
