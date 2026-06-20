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
- **Entry:** A submission on the board. Fields mirror the College page: `entrant_name`, `work_title`, `work_subject`, `content`, original/archived location links, `review_overseer`, `review_opened`/`review_closed` (in-game date strings, e.g. `220.02.16`), `recommendation`, and the workflow position (`current_step`, `step_status`). Exposes computed `on_step`/`progress_text`. Ordered by `-review_opened` to match the live board.
- **Vote:** A noble's review/recommendation on an entry (recognition level + optional comment). A user may review an entry only once.

## Running the Development Servers

### Backend (Django)

1. Open a terminal and navigate to the project root.
2. Activate the virtual environment: `source venv/bin/activate`
3. Change into the backend directory: `cd backend`
4. Run the development server (configured for port 8251 to avoid conflicts): `python manage.py runserver 8251`

*The Admin panel is available at `http://localhost:8251/admin`.* Chancellors manage entries
there, including bulk "Advance to next step" / "Mark as Nobility Awarded" actions.

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

Pages: `/` (the board — submission grid + Contest Steps section), `/submit` (the public Step-1
submission pipeline), and `/login`. Logged-in nobles can review submissions inline from the board.

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
- **CORS/CSRF:** never `CORS_ALLOW_ALL_ORIGINS`. `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`
  come from env (default to `localhost:5173` in dev). The preferred deployment keeps the API
  same-origin via a proxy (Vite in dev, Vercel rewrite in prod), making cookies first-party `Lax`.
- **Rate limiting:** DRF throttles — anon/user defaults plus tighter scopes for `login` (brute-force
  defense) and the public `submit` pipeline.
- **Transport/headers (production):** SSL redirect, HSTS (preload), secure + httpOnly cookies,
  `X-Frame-Options: DENY`, nosniff, referrer policy. `manage.py check --deploy` passes clean.
  The SPA adds a strict **CSP** and security headers via `frontend/vercel.json`.
- **Static:** served by **WhiteNoise** (`collectstatic` → hashed manifest), so the Django admin
  renders without a separate web server (works on serverless).
- **Email Verification:** Anymail + `python-dotenv`. Dev uses the file-based backend (writes to
  `backend/sent_emails/`); production uses Mailgun (`MAILGUN_*` in `.env`). The `is_verified` flag
  gates voters before they may review.

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
- **Same-origin proxy:** `frontend/vercel.json` rewrites `/api/(.*)` → `collegebeta-api.vercel.app/api/$1`
  so auth cookies stay first-party on `collegebeta.phever.dev`. **Gotcha:** use the `(.*)`/`$1` form —
  the `:path*` form silently 404s for external (cross-project) rewrites.
- **Backend build:** `backend/vercel.json` builds `config/wsgi.py` with `@vercel/python` (explicit
  `builds` avoids treating the Django `api/` package as functions) and `includeFiles: staticfiles/**`
  so WhiteNoise can serve the admin assets. Run `collectstatic` before deploying.
- **Backend prod env (set on `collegebeta-api`):** `ENVIRONMENT=production`, `DJANGO_SECRET_KEY`,
  `DJANGO_ALLOWED_HOSTS=collegebeta.phever.dev`, `ALLOW_VERCEL_HOSTS=1`, `DB_CONN_MAX_AGE=0`,
  `CORS_ALLOWED_ORIGINS=https://collegebeta.phever.dev`,
  `CSRF_TRUSTED_ORIGINS=https://collegebeta.phever.dev,https://collegebeta-api.vercel.app`
  (the second origin lets Chancellors use `/admin` on the backend domain).
- **DNS:** `collegebeta.phever.dev` is a Cloudflare CNAME → `cname.vercel-dns.com` (DNS-only).
- **Admin:** Chancellors manage at https://collegebeta-api.vercel.app/admin.
- **Redeploy (manual):** `cd backend && vercel deploy --prod` / `cd frontend && vercel deploy --prod`.
- **CI/CD:** `.github/workflows/deploy.yml` runs on push to `master` (e.g. a merged PR): it installs
  backend deps, runs `collectstatic` + `migrate` (against Neon), then `vercel deploy --prod` for both
  projects. Project/org IDs are in the workflow; secrets needed are **`VERCEL_TOKEN`** (a Vercel
  access token) and **`DATABASE_URL`** (the Neon *unpooled* URL, already set). Deploy steps no-op
  until `VERCEL_TOKEN` is present.
