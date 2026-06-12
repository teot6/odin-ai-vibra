# Vibra

Vibra is an interactive, mobile-first MVP for personality-led dating and
self-discovery. It demonstrates an adult onboarding flow, a scored personality
test, compatibility-based match interactions, AI-style conversation practice,
and free/VIP plan selection in a polished frontend experience.

The React frontend can run by itself as a static demo. An optional FastAPI
prototype in the repository root adds local JSON session persistence and
validation, but it is not a production backend.

## MVP Features

- 18+ age confirmation gate
- Five-step scored personality test and connection profile
- Sample compatibility cards with like, maybe, and pass actions
- AI-style chat practice with suggested prompts and mock replies
- Free and VIP plan selection preview
- Session restoration when the local FastAPI prototype is available
- Validation contracts for demo session updates
- Automatic offline fallback when the backend is unavailable
- Premium, responsive, mobile-first interface

All profiles, compatibility results, chat replies, pricing, and plan actions are
demonstration content.

## Tech Stack

### Frontend

- React 18
- Vite 5
- JavaScript and JSX
- CSS
- Browser `localStorage` for the anonymous demo session identifier

### Local backend prototype

- Python
- FastAPI
- Pydantic validation
- JSON file persistence
- In-process locking for local writes

The broader ODIN backend also imports `requests` and can connect to a local
Ollama service for ODIN features outside Vibra. Vibra's conversation replies
are currently deterministic mock responses, not calls to a production AI
service.

## Frontend Setup

Requirements:

- Node.js 18 or newer
- npm

From `generated_projects/Vibra`:

```bash
npm install
npm run dev
```

Open the URL printed by Vite, usually `http://localhost:5173`.

The available npm scripts are:

| Script | Purpose |
| --- | --- |
| `npm run dev` | Start the Vite development server |
| `npm run build` | Create an optimized static build in `dist/` |
| `npm run preview` | Preview the production build locally |

## Backend Setup

The optional backend lives at the repository root in `main.py`. Use it only for
local development and demo session persistence.

From the repository root:

```bash
python -m venv venv
```

Activate the environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Install the backend packages if they are not already available:

```bash
python -m pip install fastapi uvicorn pydantic requests
```

Start the local API:

```bash
python -m uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000` by default. The frontend uses that URL
unless `VITE_VIBRA_API_URL` is set.

> **Local demo backend only:** `main.py` is not production-ready. It has no
> authentication, user accounts, database, encryption-at-rest strategy,
> production rate limiting, distributed locking, audit controls, deployment
> configuration, or durable multi-instance storage. CORS currently permits
> only local Vite origins.

## Local Development

Run the backend and frontend in separate terminals:

```bash
# Terminal 1, repository root
python -m uvicorn main:app --reload
```

```bash
# Terminal 2, generated_projects/Vibra
npm run dev
```

With the API running, demo choices are written to `vibra_sessions.json` at the
repository root and can be restored using the anonymous session ID stored in
the browser. Without the API, the frontend remains interactive but changes are
not durably persisted by the backend.

To point the frontend at another API during development, create an uncommitted
`.env.local` file:

```text
VITE_VIBRA_API_URL=http://127.0.0.1:8000
```

## Production Build

From `generated_projects/Vibra`:

```bash
npm run build
npm run preview
```

The deployable static files are generated in `dist/`.

## Static Deployment

The frontend can be deployed independently to Vercel or Netlify as a static
Vite site. The offline fallback keeps the MVP usable when no backend is
deployed.

| Platform | Base directory | Build command | Output directory |
| --- | --- | --- | --- |
| Vercel | `generated_projects/Vibra` | `npm run build` | `dist` |
| Netlify | `generated_projects/Vibra` | `npm run build` | `dist` |

Do not set `VITE_VIBRA_API_URL` for a frontend-only deployment. The app will
attempt the default local API briefly, then switch to offline demo mode.

Deploying `main.py` requires a separate backend plan and production hardening.
The current JSON storage is tied to one local filesystem and is unsuitable for
serverless functions, multiple instances, real users, or sensitive data.

## Safety and Demo Limitations

- **Adults only:** Vibra is intended for people aged 18 and older. The current
  age gate is a UI confirmation, not identity or age verification.
- **No real user data:** All displayed profiles and match information are
  fictional. Do not enter personal, confidential, or sensitive information.
- **No real payments:** VIP selection is a visual demo. There is no checkout,
  billing provider, subscription, or charge.
- **No real matching:** Compatibility scores and profiles are sample product
  logic, not validated recommendations or live users.
- **No real AI or moderation:** Chat replies are mock coaching responses. There
  is no production AI provider, human moderation, abuse detection, reporting,
  blocking, or emergency support.
- **No production privacy guarantees:** Local JSON persistence is for
  development only and must not store real user information.

## Do Not Commit

Keep these generated or local files out of GitHub:

- `node_modules/`
- `dist/`
- `.env` and `.env.*` files, except a deliberately sanitized `.env.example`
- `vibra_sessions.json`
- `odin_memory.json`
- `__pycache__/` and `*.pyc`
- generated `Vibra_backup_*` folders
- logs, temporary files, editor settings, secrets, and real user data

If the repository root is initialized as the Git repository, add equivalent
root-level ignore rules for `generated_projects/Vibra_backup_*/`,
`vibra_sessions.json`, and generated project memory files. A nested
`generated_projects/Vibra/.gitignore` cannot ignore sibling backup directories.

## Roadmap

- Production authentication and verified adult account flows
- Privacy-aware profiles, preferences, and consent controls
- Validated personality and compatibility methodology
- Secure database-backed persistence and migrations
- Real matching and mutually accepted connections
- Moderated real-time messaging, reporting, blocking, and safety operations
- Production AI with privacy controls, evaluations, and human escalation
- Payment-provider integration and subscription entitlement handling
- Rate limiting, monitoring, audit logs, backups, and incident response
- Expanded accessibility testing, localization, analytics, and legal review

## Status

Vibra is ready for GitHub as an MVP and for static frontend deployment. It is
not ready to operate as a real dating service or to process real users,
messages, payments, or sensitive information.
