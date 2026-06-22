# Darkages Contest Hall - Project Overview

This project is a website designed to allow "College Chancellors" (Admins) to post entries from an old MMO contest board so that qualified individuals (Voters/Award Winners) can review and vote on them.

Currently a barebones version of this is hosted by the College at https://novus-imperia.com/college/progress.htm

Ensure that our system can handle hosting/archiving all of the works shown here. As well as an **IDENTICAL** contest submission pipeline.

## Architecture

The project is split into two main components within this repository:

1. **Backend (`/backend`)**
   - **Framework:** Django with Django REST Framework (DRF)
   - **Database:** SQLite (default for development)
   - **Authentication:** JWT (JSON Web Tokens) using `djangorestframework-simplejwt`
   - **Admin Interface:** The built-in Django Admin is leveraged heavily for the Chancellors to manage Contests, Entries, and Users.

2. **Frontend (`/frontend`)**
   - **Framework:** React initialized via Vite
   - **Routing:** `react-router-dom`
   - **Styling:** Custom Vanilla CSS with a focus on modern "glassmorphism" aesthetics, dark mode by default, and interactive hover states.
   - **HTTP Client:** `axios` with interceptors configured to attach JWT tokens to API requests.

## Domain: the Contest Hall board

The reference page (`progress.htm`) is a **submission progress board**. Each work moves
through a fixed 4-step workflow, rendered as a colored progress bar:

1. **Submission** — the entrant has submitted their work to the College.
2. **Review** — a Chancellor opens it for review; nobles recommend a recognition level.
3. **Loures Confirmation** — recommendations are sent to the Library of Loures for approval.
4. **Nobility Awarded** — the work is formally recognized.

The 66 archived works from the live board are kept in `backend/api/data/archive_entries.json`
(the live page shows 67 boxes, but one is a literal duplicate). Recognition / recommendation
levels are: Village, Clave, Kingdom, Aisling, or No Award.

## Data Models

Located in `/backend/api/models.py`:
- **User:** Inherits from `AbstractUser`. Includes roles (`admin` vs `voter`), an `is_verified` boolean, and `in_game_name`.
- **Contest:** A contest board that groups submissions. Includes title, description, an `info_message` banner, optional start/end dates, and an active status.
- **WorkflowStep:** One of the 4 steps (number, title, description), shown in the board's "Contest Steps" section.
- **Entry:** A submission on the board. Fields mirror the College page: `entrant_name`, `work_title`, `work_subject`, `content`, original/archived location links, `review_overseer`, `review_opened`/`review_closed` (in-game date strings, e.g. `220.02.16`), `recommendation`, and the workflow position (`current_step`, `step_status`). An `is_archived` flag moves a work off the live board into the searchable **Archive** (older submissions kept for posterity). Exposes computed `on_step`/`progress_text`. Ordered by `-review_opened` to match the live board.
- **VoteIntention:** A noble's **private** draft recommendation + review for an entry (one per user per entry). Real reviewing/voting happens in-game — this is a scratchpad a noble prepares here and copies across. Visible only to its author and Chancellors; can opt into an email reminder before the review period closes.
- **Invitation:** A Chancellor's account invitation for a new noble. Holds the invitee's `email` and `in_game_name` (Chancellor-set, read-only to the noble), a single-use, expiring `token` (14 days), and who created/accepted it. Accepting creates a verified voter.

## Running the Development Servers

### Backend (Django)

1. Open a terminal and navigate to the project root.
2. Activate the virtual environment: `source venv/bin/activate`
3. Change into the backend directory: `cd backend`
4. Run the development server (configured for port 8251 to avoid conflicts): `python manage.py runserver 8251`

*The Admin panel is available at `http://localhost:8251/admin`.* Chancellors manage entries
there, including bulk "Advance to next step" / "Mark as Nobility Awarded" / "Move to Archive"
actions, plus Users and Invitations. Most day-to-day edits can also be done from the board itself
(see Pages) without opening the admin.

> **Note:** the virtual environment must live at the **project root** (`venv/`), matching the
> commands above. (`requirements.txt` lives in `/backend`.)

### Seeding the board

From `/backend`, run `python manage.py seed_board` to load the 4 workflow steps, the 66 archived
works, and demo users. Pass `--fresh` to wipe existing entries first. Demo logins created:
- **chancellor / chancellor** — Chancellor (admin superuser)
- **noble / noblepass** — verified voter

### Frontend (Vite/React)

1. Open a new terminal and navigate to the project root.
2. Change into the frontend directory: `cd frontend`
3. Start the Vite development server: `npm run dev`

*The frontend application will be available at `http://localhost:5173`.*

Pages (see `frontend/src/App.jsx`):
- `/` — the board. Submission grid (non-archived entries) with subject filtering and
  **client-side pagination** (selectable page size 24/48/96, remembered in `localStorage`),
  plus the "Contest Steps" section.
- `/archive` — the **Archive** of older works (`is_archived`). Public to browse; **searchable by
  entrant/title and filterable by category**. Chancellors get an inline form to add a work (metadata
  + optional file upload to object storage).
- `/how-to-enter` — entry instructions + campus map; Chancellors get a "record an entry" form.
- `/invite` — Chancellor-only: send / list / revoke noble invitations.
- `/accept-invite?token=…` — public: redeem an invitation (choose username + password; email and
  in-game name are shown read-only). Logs the new noble in on success.
- `/login` — sign in.

On each board/archive card, logged-in **nobles** get a private vote-intention panel, and
**Chancellors** get an inline **"Edit entry"** modal (edit any field, including the workflow step)
and an archived-copy file uploader — so most edits never need the `/admin` panel.

## Security model

Configuration is environment-driven (`config/settings.py` reads `.env`; see `.env.template`).
`ENVIRONMENT=production` flips on the hardened settings; dev relaxes them so the app runs locally.

- **Authentication:** JWT delivered as **httpOnly cookies** (`access_token` / `refresh_token`), so
  tokens are never exposed to JavaScript (XSS can't read them). `api/authentication.py`
  (`CookieJWTAuthentication`) reads the access cookie and **enforces CSRF** on unsafe methods; the
  SPA echoes Django's `csrftoken` cookie as the `X-CSRFToken` header (see `frontend/src/api.js`).
  Refresh tokens **rotate and are blacklisted** on use/logout (`token_blacklist` app). Access
  lifetime 15 min, refresh 7 days (overridable via env). Header-based JWT remains as a fallback for
  non-browser clients. Auth endpoints: `POST /api/auth/{login,refresh,logout}/`, `GET /api/auth/{me,csrf}/`.
- **Account invitations:** Chancellors invite nobles by email (`/api/invitations/` — create/list/revoke,
  `IsAdminUser`). The Chancellor sets the invitee's `email` + `in_game_name`; these are **read-only to
  nobles** (`UserSerializer` is fully read-only). The single-use `token` is **never returned by the API** —
  it's delivered only by email. Public redemption: `GET /api/auth/invitation/?token=` (prefill) and
  `POST /api/auth/accept-invite/` (creates a verified voter and logs them in via fresh auth cookies).
  A dedicated `invite` throttle scope rate-limits the public endpoints. Entries are searchable via the
  DRF `SearchFilter` (`?search=` over `entrant_name`/`work_title`) and filterable by `?subject=` /
  `?archived=true`.
- **CORS/CSRF:** never `CORS_ALLOW_ALL_ORIGINS`. `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`
  come from env (default to `localhost:5173` in dev). The preferred deployment keeps the API
  same-origin via a proxy (Vite in dev, Vercel rewrite in prod), making cookies first-party `Lax`.
- **Rate limiting:** DRF throttles — anon/user defaults plus tighter scopes for `login` (brute-force
  defense), the `submit` pipeline, and `invite` (invitation prefill/redeem).
- **Transport/headers (production):** SSL redirect, HSTS (preload), secure + httpOnly cookies,
  `X-Frame-Options: DENY`, nosniff, referrer policy. `manage.py check --deploy` passes clean.
  The SPA adds a strict **CSP** and security headers via `frontend/vercel.json`.
- **Static:** served by **WhiteNoise** (`collectstatic` → hashed manifest), so the Django admin
  renders without a separate web server (works on serverless).
- **Email:** Anymail + `python-dotenv`. Dev uses the file-based backend (writes to
  `backend/sent_emails/`); production uses Mailgun (`MAILGUN_*` in `.env`). Used for invitation links
  and the noble review-reminder cron. The `is_verified` flag gates voters before they may review
  (Chancellor-invited nobles are verified on acceptance).

## Deployment (Vercel) — live

The project runs entirely on Vercel as **two linked projects** under the `mike-penners-projects` team:

| Project | What | URL |
|---------|------|-----|
| `collegebeta` | Vite SPA (the board) | **https://collegebeta.phever.dev** |
| `collegebeta-api` | Django via `@vercel/python` (Fluid Compute) | https://collegebeta-api.vercel.app |

- **Database:** Neon Postgres (`neon-amethyst-branch`, Marketplace integration → injects `DATABASE_URL`).
  Migrate/seed against the **unpooled** URL; the function uses the pooled `DATABASE_URL` with
  `DB_CONN_MAX_AGE=0`. Run `migrate` + `seed_board` locally against `DATABASE_URL_UNPOOLED` after any
  schema change.
- **Same-origin proxy:** `frontend/vercel.json` rewrites `/api/(.*)`, `/admin(.*)`, and `/static/(.*)`
  → `collegebeta-api.vercel.app/...` so the API **and the Django admin** are served first-party on
  `collegebeta.phever.dev` (auth cookies/CSRF stay first-party). **Gotcha:** use the `(.*)`/`$1` form —
  the `:path*` form silently 404s for external (cross-project) rewrites. The SPA's strict CSP/security
  headers are scoped to exclude `/admin` and `/static` (`source: /((?!admin|static).*)`) so Django's
  own admin headers/inline assets aren't clobbered.
- **Backend build:** `backend/vercel.json` builds `config/wsgi.py` with `@vercel/python` (explicit
  `builds` avoids treating the Django `api/` package as functions) and `includeFiles: staticfiles/**`
  so WhiteNoise can serve the admin assets. Run `collectstatic` before deploying.
- **Backend prod env (set on `collegebeta-api`):** `ENVIRONMENT=production`, `DJANGO_SECRET_KEY`,
  `DJANGO_ALLOWED_HOSTS=collegebeta.phever.dev`, `ALLOW_VERCEL_HOSTS=1`, `DB_CONN_MAX_AGE=0`,
  `CORS_ALLOWED_ORIGINS=https://collegebeta.phever.dev`,
  `CSRF_TRUSTED_ORIGINS=https://collegebeta.phever.dev,https://collegebeta-api.vercel.app`
  (the second origin lets Chancellors use `/admin` on the backend domain).
- **DNS:** `collegebeta.phever.dev` is a Cloudflare CNAME → `cname.vercel-dns.com` (DNS-only).
- **Admin:** Chancellors manage at https://collegebeta.phever.dev/admin (proxied to Django;
  https://collegebeta-api.vercel.app/admin still works directly as a fallback).
- **Deploy model (two paths, one per project):**
  - **Frontend (`collegebeta`)** deploys via **Vercel's Git integration** — the repo is linked,
    production branch `master`, **Root Directory = `frontend`**, **framework = Vite**. Every push to
    `master` auto-builds and promotes; PR branches get preview deployments. *Gotcha:* the Root
    Directory **must** be `frontend` — without it Vercel builds from the empty monorepo root, runs no
    build, and ships an empty output (every route 404s, which also breaks the `/api` + `/admin`
    proxy). Set it via dashboard (Settings → Build & Deployment) or
    `PATCH /v9/projects/{id}` with `{"framework":"vite","rootDirectory":"frontend"}`.
  - **Backend (`collegebeta-api`)** deploys via **GitHub Actions** (`.github/workflows/deploy.yml`,
    workflow "Deploy backend to Vercel") on push to `master`: installs deps, runs `collectstatic` +
    `migrate` (against Neon), then `vercel deploy --prod`. It is *not* Git-connected — CI runs the DB
    migration + static collection that a plain Git deploy can't. Required **repository Actions secrets**
    (not environment/variable scope): **`VERCEL_TOKEN`** and **`DATABASE_URL`** (Neon *unpooled*) — both
    are set, so pushes auto-deploy the backend. The deploy step is guarded by `if: VERCEL_TOKEN != ''`,
    so it silently no-ops if the secret is ever missing/misplaced (verify with `gh secret list`).
- **Redeploy (manual):** backend → `cd backend && vercel deploy --prod`; frontend → push to `master`
  (or `cd frontend && vercel build --prod && vercel deploy --prebuilt --prod` to bypass build settings).
