# Vibra

Vibra is a Bulgarian, mobile-first dating product MVP built around personality,
compatibility, and safer interaction design. The project combines a polished
React experience with a local FastAPI prototype to demonstrate both product
thinking and practical frontend/backend integration.

## Live Demo

**Vercel:**  
https://odin-ai-vibra-c7p6-ixwln0mdx-teot6s-projects.vercel.app

The deployed version is a static frontend running in offline demo mode. Core
interactions work without a deployed backend.

## Main Features

- Premium Bulgarian mobile-first interface
- Guided 18+ entry flow
- Local demo profile-photo requirement
- Verification preview without real document processing
- Fifteen-question scored personality test
- Personalized compatibility profile
- Interactive sample match cards
- Mock AI conversation coach with suggested prompts
- Free/VIP plan preview with a 5 EUR/month demo price
- Mobile bottom navigation with safe-area support
- Touch-friendly horizontal card rows and CSS scroll snapping
- Session restoration when the local FastAPI prototype is available
- Automatic offline fallback for static deployment
- Keyboard focus states and reduced-motion support

## What I Built

This project demonstrates:

- **React frontend development:** reusable data-driven UI, conditional rendering,
  forms, interactions, and accessibility-aware components
- **Mobile-first UI:** responsive layouts, touch targets, safe-area navigation,
  horizontal card flows, and premium visual hierarchy
- **State management:** onboarding, test progress, match choices, chat history,
  profile-photo status, plan selection, reset, and session restoration
- **Frontend interaction logic:** personality scoring, compatibility results,
  mock chat responses, navigation, and offline behavior
- **FastAPI backend prototype:** validated Vibra endpoints and structured response
  contracts in the repository-level `main.py`
- **JSON local persistence:** local demo sessions with normalization and support
  for legacy five-answer test sessions
- **Deployment preparation:** optimized Vite builds, static-hosting documentation,
  metadata, ignore rules, and Vercel-ready output
- **Product thinking:** adult safety, consent, transparency, privacy boundaries,
  monetization preview, and a clear path from MVP to production

## Tech Stack

| Area | Technology |
| --- | --- |
| Frontend | React 18, JavaScript, JSX |
| Build tooling | Vite 5 |
| Styling | CSS, responsive layouts, scroll snap |
| Local state | React state, browser `localStorage` |
| Backend prototype | Python, FastAPI, Pydantic |
| Demo persistence | Local JSON file with in-process locking |
| Deployment | Vercel static hosting |

No component library or additional UI framework is required.

## Screens and Flows

The main demo journey is:

1. Confirm the 18+ requirement.
2. Complete the local profile-photo demo step.
3. Review the verification and privacy boundaries.
4. Answer fifteen personality questions.
5. Receive a scored compatibility profile.
6. Explore sample matches and record like/maybe/pass choices.
7. Practice a conversation with the mock Vibra AI assistant.
8. Preview free and VIP plan selection.

Supporting sections explain compatibility signals, safety principles, demo
limitations, and the next recommended action.

## Local Setup

Requirements:

- Node.js 18 or newer
- npm

From `generated_projects/Vibra`:

```bash
npm install
npm run dev
```

Vite will print the local URL, typically `http://localhost:5173`.

### Optional Local Backend

The FastAPI prototype lives in the repository root. From that directory:

```bash
python -m venv venv
```

Activate the environment on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Install the prototype requirements:

```bash
python -m pip install fastapi uvicorn pydantic requests
```

Start the API:

```bash
python -m uvicorn main:app --reload
```

The frontend uses `http://127.0.0.1:8000` by default. A different local API can
be configured in an uncommitted `.env.local` file:

```text
VITE_VIBRA_API_URL=http://127.0.0.1:8000
```

## Build

Create and preview the optimized static build:

```bash
npm run build
npm run preview
```

The deployable files are generated in `dist/`.

## Deployment

Vibra can be deployed as a standard static Vite application.

| Platform | Base directory | Build command | Output |
| --- | --- | --- | --- |
| Vercel | `generated_projects/Vibra` | `npm run build` | `dist` |
| Netlify | `generated_projects/Vibra` | `npm run build` | `dist` |

For a frontend-only deployment, do not set `VITE_VIBRA_API_URL`. If the local
API is unavailable, Vibra automatically switches to offline demo mode.

The FastAPI prototype is not deployed with the static frontend. Production use
would require a separately hosted and hardened backend.

## Demo Limitations

- Match profiles, avatars, compatibility scores, and conversations are fictional.
- The profile-photo control stores only a local completion flag; image bytes are
  not read, previewed, uploaded, or retained.
- VIP selection changes demo state only and never starts a payment.
- The AI assistant uses deterministic mock responses.
- Static deployment has no shared server-side session or account storage.
- Local JSON persistence is intended only for development and demonstration.

## Safety and 18+

Vibra is designed only for adults aged 18 and older. The current age gate is a
self-declared demo confirmation, not legal age verification.

Do not enter real personal, financial, identity, medical, or sensitive
information. Do not upload a real identity document. Production development
would require privacy review, consent controls, moderation, reporting, blocking,
data protection, and qualified external verification providers.

## Not Production-Ready Yet

Vibra currently has:

- no real payments, billing, cards, or banking integration
- no real ID, KYC, or age-verification processing
- no real AI service or AI/human moderation system
- no real authentication or user accounts
- no production database or durable cloud storage
- no live users, real matching, or real-time messaging

Real user data should not be used with this MVP. Production payments should be
handled by a trusted licensed processor, while identity and age checks should
be delegated to a suitable specialist provider.

## What Is Mock or Static

| Experience | Current implementation |
| --- | --- |
| Profiles and avatars | Fictional demo content |
| Personality scoring | Frontend product logic |
| Match recommendations | Sample compatibility presentation |
| AI chat | Rule-based mock replies |
| Profile photo | Local boolean completion state |
| Verification | Informational UI only |
| VIP subscription | Local selection state |
| Payments | Disabled |
| Live deployment | Static Vercel frontend |
| Backend | Local FastAPI prototype only |

## Future Roadmap

- Production authentication and adult account flows
- Licensed KYC and age-verification integration
- Secure profile management and consent controls
- Validated compatibility methodology
- Production database, migrations, and encrypted storage
- Real mutual matching and moderated messaging
- Reporting, blocking, abuse prevention, and safety operations
- Production AI with privacy safeguards and evaluations
- Licensed payment processing and subscription entitlements
- Monitoring, rate limiting, audit logs, backups, and incident response
- Accessibility testing, localization, analytics, and legal review

## Repository Hygiene

Do not commit:

- `node_modules/`
- `dist/`
- `.env` or `.env.*`, except a sanitized `.env.example`
- `vibra_sessions.json`
- `odin_memory.json`
- `__pycache__/` or `*.pyc`
- generated `Vibra_backup_*` directories
- logs, secrets, payment data, identity documents, or real user data

## Portfolio Summary

Vibra is a portfolio-ready product MVP that shows how I approach a complete
interactive experience: defining a clear user journey, building responsive
React interfaces, modeling meaningful frontend state, prototyping validated
backend contracts, preparing static deployment, and communicating production
boundaries honestly.

The live demo is intentionally safe and self-contained. It presents the product
vision and engineering approach without pretending that payments, verification,
moderation, authentication, or real-user infrastructure are already complete.
