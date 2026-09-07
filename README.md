# The Missing Question

**Guard your momentum, not your assumptions.**

A developer-focused adversarial reasoning sidecar. Paste a product idea, architecture plan, PRD, implementation note, or diff. Nemotron returns either:

- `CLEAR`, or
- one `POKE_HOLE` containing the single highest-leverage unanswered question.

The follow-up flow separates concerns that never applied (`OUT_OF_SCOPE`) from useful
concerns closed by clarification or an accepted tradeoff (`RESOLVED_BY_CONTEXT`). Patch
evaluation stays fixed on the original criterion and keeps optional advice outside the verdict.

## Project structure

```text
the-missing-question/
├── app/
│   ├── main.py
│   ├── nemotron.py
│   ├── models.py
│   ├── prompts.py
│   └── static/
│       ├── index.html
│       ├── app.js
│       └── styles.css
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
└── README.md
```

## Run locally

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Nemotron endpoint, model ID, and API key.
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Windows PowerShell

```powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env with your Nemotron endpoint, model ID, and API key.
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Open:

```text
http://localhost:8080
```

Health check:

```text
http://localhost:8080/healthz
```

## API

### POST `/analyze_context`

```json
{
  "context": "We are making account linking foundational to the product.",
  "mode": "manual"
}
```

Returns:

```json
{
  "status": "CLEAR",
  "question": null,
  "assumption": null,
  "why_now": null,
  "severity": null,
  "failure_if_ignored": null,
  "evidence": null
}
```

or:

```json
{
  "status": "POKE_HOLE",
  "question": "What happens if the platform denies the permission your core workflow depends on?",
  "assumption": "The required permission will be approved and remain available.",
  "why_now": "You are about to build multiple dependent features on top of it.",
  "severity": "high",
  "failure_if_ignored": "The core workflow may become unusable after substantial implementation work.",
  "evidence": "account linking foundational to the product"
}
```

### POST `/evaluate_patch`

```json
{
  "original_concern": {
    "status": "POKE_HOLE",
    "question": "What happens if the required permission is denied?",
    "assumption": "The permission will be available.",
    "why_now": "Dependent implementation is about to begin.",
    "severity": "high",
    "failure_if_ignored": "The core workflow could fail.",
    "evidence": "account linking foundational to the product"
  },
  "resolution": "We tested denial and added a degraded local-only workflow.",
  "updated_context": "The product now supports a degraded local-only workflow when permission is denied."
}
```

`PATCHED` responses include a `resolution_basis` explaining whether the concern was
implemented, clarified, accepted as a bounded tradeoff, or closed by removing its assumption.
They may also contain one optional `suggestion`; it does not alter the verdict.

## Google Cloud Run

Set your project:

```bash
gcloud config set project PROJECT_ID
```

Enable services:

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

Create an Artifact Registry repository once:

```bash
gcloud artifacts repositories create missing-question \
  --repository-format=docker \
  --location=us-central1
```

Configure Docker auth:

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

Build:

```bash
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/PROJECT_ID/missing-question/the-missing-question
```

Deploy:

```bash
gcloud run deploy the-missing-question \
  --image us-central1-docker.pkg.dev/PROJECT_ID/missing-question/the-missing-question \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars NEMOTRON_API_URL="YOUR_ENDPOINT",NEMOTRON_MODEL_NAME="YOUR_MODEL_ID",NEMOTRON_API_KEY="YOUR_API_KEY"
```

For a real deployment, prefer Google Secret Manager for the API key rather than keeping it directly in an environment-variable command.

## First dogfood test

Once the prototype is running, paste the implementation itself and ask it to inspect the project.

A useful first context prompt:

> Here is the implementation for The Missing Question. Find the single highest-leverage unresolved issue that would stop this prototype from working correctly in production.

The product should either identify one concrete blocker or return `CLEAR`. It should never spray a generic list of concerns.
