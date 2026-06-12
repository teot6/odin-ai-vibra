# Vibra

Vibra is an interactive, mobile-first MVP for personality-led dating and
self-discovery. It demonstrates an adult onboarding flow, a scored personality
test, compatibility-based match interactions, AI-style conversation practice,
and free/VIP plan selection in a polished frontend experience.

Live static demo:
https://odin-ai-vibra-c7p6-ixwln0mdx-teot6s-projects.vercel.app

The React frontend can run by itself as a static demo. An optional FastAPI
prototype in the repository root adds local JSON session persistence and
validation, but it is not a production backend.

## MVP Features

- 18+ age confirmation gate
- Bulgarian user-facing interface with premium, natural product language
- Fifteen-question scored personality test and deeper connection profile
- Sample compatibility cards with like, maybe, and pass actions
- AI-style chat practice with suggested prompts and mock replies
- Free and 5 EUR/month VIP plan selection preview with local mock-upgrade state
- Required profile-photo demo step that stores only a local completion flag
- Profile verification preview for photo, 18+ confirmation, and future external KYC
- Abstract generated demo avatars for matches and a CSS Vibra AI assistant avatar
- Mobile bottom navigation with safe-area spacing
- Touch-friendly horizontal card rows with CSS scroll snapping
- Session restoration when the local FastAPI prototype is available
- Validation contracts for demo session updates
- Automatic offline fallback when the backend is unavailable
- Premium, responsive, mobile-first interface

All profiles, compatibility results, chat replies, pricing, and plan actions are
demonstration content.

## Monetization and Verification Demo

The VIP price is displayed as a **5 EUR/month demo price**. Selecting VIP only
changes local demo state and the existing demo plan selection; it does not
start checkout, create a subscription, charge a card, or communicate with a
bank. Payment data is never requested or stored.

A production version should use Stripe or another trusted, licensed payment
processor. Vibra should receive only the minimum payment status and entitlement
information needed from that provider, not raw card or bank-account details.

Profile completion includes a mock image picker. Selecting a file sets the
local `vibra_demo_profile_photo_added` flag, then immediately clears the input.
The frontend does not read, preview, upload, or retain the image bytes. Resetting
the demo clears the flag.

The verification section is informational UI only:

- one local profile-photo completion flag
- the existing self-declared 18+ confirmation
- a future external KYC/age-verification step

There is no ID-card upload, document storage, facial recognition, biometric age
estimation, or real identity verification. Real documents and sensitive images
must never be entered into this demo.

The expanded test covers communication, emotional expression, conflict,
social energy, attachment, relationship goals, boundaries, trust, humor,
lifestyle rhythm, introvert/extrovert balance, romantic pace, honesty,
support style, and long-term compatibility. All fifteen answers contribute to
the frontend-only scoring signals.

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

The API accepts up to 15 personality answers and step indexes from 0 through
14. Existing sessions containing the original five valid answers remain
compatible: normalization preserves them and the frontend resumes with the
remaining questions. The schema version remains `vibra-mvp-v1`.

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
  billing provider, subscription, or charge. The 5 EUR amount is a demo price.
- **No real photo upload:** The file control records only a local completion
  flag. It does not read, display, upload, or store the selected image.
- **No real identity verification:** The verification steps do not accept ID
  cards or biometric data and do not estimate age from a face.
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
- Licensed KYC/age-verification provider with legal and privacy review
- Privacy-aware profiles, preferences, and consent controls
- Validated personality and compatibility methodology
- Secure database-backed persistence and migrations
- Real matching and mutually accepted connections
- Moderated real-time messaging, reporting, blocking, and safety operations
- Production AI with privacy controls, evaluations, and human escalation
- Payment-provider integration and subscription entitlement handling
- Trusted payment processor integration without storing card or bank data
- Rate limiting, monitoring, audit logs, backups, and incident response
- Expanded accessibility testing, localization, analytics, and legal review

## Status

Vibra is ready for GitHub as an MVP and for static frontend deployment. It is
not ready to operate as a real dating service or to process real users,
messages, payments, or sensitive information.
