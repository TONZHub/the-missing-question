# Fixes applied to the Nemotron-generated prototype

This version keeps the original product behavior but patches the known implementation issues.

## Runtime/backend

- Added missing imports from `app.prompts`.
- Standardized `evaluate_patch(original_concern=...)` across caller and callee.
- Added `python-dotenv` and load `.env` automatically for local development.
- Added root `/` route and mounted `/static`.
- Added `/healthz`.
- Replaced weak key checking with strict Pydantic response validation.
- Added one repair pass for malformed model JSON.
- Stopped silently converting invalid model output into `CLEAR`.
- Added request length validation.
- Enforced complete `POKE_HOLE` payloads.
- Enforced `POKE_HOLE` as the only valid input to `/evaluate_patch`.
- Enforced `remaining_question` for partial/still-open patch results.
- Removed unused imports.

## Frontend

- Added the missing `#message` element.
- Removed model-controlled `innerHTML` interpolation.
- Rendered model text using `textContent` / DOM nodes.
- Preserved the original concern in JavaScript state instead of re-scraping missing element IDs.
- Replaced `prompt()` with an inline resolution textarea.
- Kept the patch UI available for repeated attempts.
- Added keyboard shortcut: Ctrl/Cmd + Enter to analyze.
- Added basic error handling and busy states.
- Fixed `.severity-high` CSS typo.
- Moved static assets under `app/static` to match the requested project layout.

## Docker / Cloud Run

- Fixed `$PORT` expansion by using shell execution for Uvicorn.
- Defaulted `PORT` to 8080 while allowing Cloud Run's injected value.
- Updated deployment instructions to use Artifact Registry rather than legacy `gcr.io`.

## Not changed

- No database.
- No authentication.
- No persistence.
- No MCP server yet.
- No automatic coding-agent sidecar yet.
- Nemotron remains behind an OpenAI-compatible chat-completions endpoint.
