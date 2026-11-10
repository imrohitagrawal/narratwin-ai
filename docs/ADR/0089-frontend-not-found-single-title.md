# ADR 0089: one title on the frontend not-found page

Status: proposed in issue #576; acceptance requires exact-head review and CI.

## Problem and decision

The default not-found page adds its own `<title>` beside the root layout's
metadata title. The two are placed in `<head>` in whichever order they finish,
so the prerendered not-found and 404 pages build two ways, and the image scan's
build-twice comparison fails intermittently on both architectures. The browser
shows the first title, so the tab name also changes between builds.

Add `frontend/src/app/not-found.tsx`, which sets its title only through the
metadata export, so one title exists. The scan requires a 404 status and exactly
one title on a missing path. On a mismatch it keeps both copies of each differing
file in its report, after a build-secret check.

## Rejected

Normalizing the order of the titles in the scan hides a difference a browser
shows. Exempting the two files removes them from the comparison. Neither changes
the page.

## Consequences

The not-found page now uses this application's own markup and a CSS module,
because the content security policy blocks inline styles. No file is exempted
from the comparison, and its normalization, the Dockerfile, the workflows and the
dependencies do not change.
