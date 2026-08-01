# NarraTwin AI Controlled Local Demo

NarraTwin turns approved knowledge into grounded, cited, multilingual avatar
explanations and interactive Q&A.

The current provider-disabled local demonstration proves only:

- project creation and markdown knowledge upload;
- grounded walkthrough generation with citations;
- multilingual script and subtitle artifacts through bounded local fixtures;
- mock/local avatar export metadata;
- performance, dependency, container, and Lighthouse quality checks.

Current limits:

- single-process runtime state;
- process-local metadata by default, with optional single-node JSON snapshots;
- mock/local providers only;
- no real video export, cloned identity, external distribution, or production
  claim;
- no generalized semantic support merely because a language is cataloged.

Start the local demonstration:

```bash
cp .env.example .env
docker compose up --build
curl http://localhost:8000/api/v1/healthz
curl http://localhost:8000/api/v1/readyz
```

Open `http://localhost:3000`, create a project, upload project knowledge,
generate a walkthrough script, inspect citations and the evaluation result, and
inspect the saved output. Use `demo/stage8_seed_project.md` as synthetic seed
data.

Run the repository gates before treating the local demonstration as
review-ready:

```bash
make quality
make ci
```

No paid provider, real provider key, personal media, cloned identity, or real
video export is required.
