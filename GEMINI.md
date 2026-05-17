# Darkages Contest Hall - Project Overview

This project is a website designed to allow "College Chancellors" (Admins) to post entries from an old MMO contest board so that qualified individuals (Voters/Award Winners) can review and vote on them.

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

## Data Models

Located in `/backend/api/models.py`:
- **User:** Inherits from `AbstractUser`. Includes roles (`admin` vs `voter`), an `is_verified` boolean, and `in_game_name`.
- **Contest:** Represents a voting event. Includes title, description, start/end dates, and an active status.
- **Entry:** An individual submission to a contest. Tied to a specific `Contest` and includes the `author_in_game_name`, content, and an optional link to the original board post.
- **Vote:** Represents a single user's vote on a specific entry. Ensures a user can only vote once per entry.

## Running the Development Servers

### Backend (Django)

1. Open a terminal and navigate to the project root.
2. Activate the virtual environment: `source venv/bin/activate`
3. Change into the backend directory: `cd backend`
4. Run the development server (configured for port 8251 to avoid conflicts): `python manage.py runserver 8251`

*The Admin panel is available at `http://localhost:8251/admin`.*

### Frontend (Vite/React)

1. Open a new terminal and navigate to the project root.
2. Change into the frontend directory: `cd frontend`
3. Start the Vite development server: `npm run dev`

*The frontend application will be available at `http://localhost:5173`.*

## Important Notes & Future Considerations

- **Authentication Flow:** Users currently receive an access token and refresh token upon login. The frontend logic manages storing these in `localStorage` and attaching them to requests via `axios` interceptors.
- **Email Verification:** A Mailgun integration is planned but currently mocked out. The `is_verified` flag on the User model is intended to be used in conjunction with this flow to ensure voters are authenticated properly before allowing them to vote.
- **CORS:** `CORS_ALLOW_ALL_ORIGINS` is currently set to `True` in the Django settings for ease of local development. This must be restricted in a production environment.
