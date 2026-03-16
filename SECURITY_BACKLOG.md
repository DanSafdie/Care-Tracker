# Security Hardening Backlog

> Generated from security audit on 2026-03-16.  
> Prioritized for a public-facing deployment (port-forwarded via DynDNS).  
> Each task is self-contained and can be picked up independently unless noted.

---

## P0 — Critical (do immediately)

### SEC-01: Add HTTPS via reverse proxy
- **Risk:** All traffic (passwords, JWT cookies, API data) travels in plaintext over the public internet.
- **Scope:** Infrastructure / Docker config only — no app code changes.
- **Approach:**
  1. Add a Caddy service to `docker-compose.yml` that terminates TLS and proxies to `care-tracker:8273`.
  2. Caddy auto-provisions Let's Encrypt certs using the DynDNS hostname.
  3. Stop exposing port 8273 directly to the host; only Caddy's 443 should be public.
  4. Add a `Caddyfile` to the project root.
- **Depends on:** SEC-06 (add `secure` flag to cookies once HTTPS is live).
- **Files:** `docker-compose.yml`, new `Caddyfile`.

### SEC-02: Add authentication to all API endpoints
- **Risk:** 14+ API endpoints have zero auth. Anyone on the internet can create pets, complete/undo tasks, enumerate users, create accounts, and trigger SMS.
- **Scope:** `app/backend/main.py` — add `Depends(get_current_user)` to every unprotected route.
- **Endpoints to protect:**
  - `GET /api/pets`, `POST /api/pets`, `GET /api/pets/{id}`
  - `POST /api/pets/{id}/timer`, `DELETE /api/pets/{id}/timer`
  - `GET /api/care-items`, `POST /api/care-items`
  - `GET /api/status`
  - `POST /api/tasks/{id}/complete`, `POST /api/tasks/{id}/undo`
  - `GET /api/history`, `GET /api/history/grid`
  - `GET /api/users/search`, `GET /api/users/by-name/{name}`
  - `POST /api/users/check-in`
- **Leave unauthenticated:** `GET /api/info` (non-sensitive), `/login`, `/signup`, `/logout`.
- **Test:** Run the existing test suite after changes (`pytest`). Update test fixtures to include auth cookies.
- **Files:** `app/backend/main.py`, `tests/conftest.py`, `tests/test_api_endpoints.py`.

### SEC-03: Remove traceback from API error responses
- **Risk:** Full Python tracebacks (file paths, library versions, internal logic) are returned to the client on any 500 error.
- **Scope:** One-line change in `app/backend/main.py`.
- **Change:** In the exception middleware (~line 87-89), remove `"traceback": traceback.format_exc()` from the JSON response. Keep the `print()` for server-side logging.
- **Files:** `app/backend/main.py`.

### SEC-04: Disable FastAPI auto-generated docs
- **Risk:** `/docs` and `/redoc` expose a complete interactive map of every endpoint, parameter, and schema to unauthenticated users.
- **Scope:** One-line change in `app/backend/main.py`.
- **Change:** Update the FastAPI constructor: `app = FastAPI(..., docs_url=None, redoc_url=None)`.
- **Files:** `app/backend/main.py`.

---

## P1 — High (do this week)

### SEC-05: Replace `python-jose` with `PyJWT`
- **Risk:** `python-jose` is unmaintained and has 5+ unpatched CVEs (algorithm confusion, empty HMAC key, timing side-channels, DoS).
- **Scope:** `app/backend/auth.py`, `requirements.txt`.
- **Approach:**
  1. `pip install PyJWT[crypto]` (or `joserfc`).
  2. Replace `from jose import JWTError, jwt` with `import jwt` (PyJWT API).
  3. Update `create_access_token()` and `decode_access_token()` — the PyJWT API is very similar.
  4. Remove `python-jose[cryptography]` from `requirements.txt`.
  5. Run tests to verify auth still works.
- **Files:** `app/backend/auth.py`, `requirements.txt`.

### SEC-06: Add `secure` flag to session cookies
- **Risk:** Without `secure=True`, the JWT cookie is sent over HTTP and can be intercepted.
- **Depends on:** SEC-01 (HTTPS must be working first).
- **Scope:** Two locations in `app/backend/main.py` where `set_cookie()` is called (login and signup).
- **Change:** Add `secure=True` to both `response.set_cookie(...)` calls.
- **Files:** `app/backend/main.py`.

### SEC-07: Add rate limiting
- **Risk:** No rate limiting anywhere. Attackers can brute-force passwords, enumerate users, spam SMS via the check-in endpoint, or DoS the app.
- **Scope:** Add `slowapi` middleware.
- **Approach:**
  1. `pip install slowapi`.
  2. Add rate limits: `/login` and `/signup` (5/min), `/api/users/check-in` (3/min), general API (60/min).
  3. Return 429 with a clear message on limit exceeded.
- **Files:** `app/backend/main.py`, `requirements.txt`.

### SEC-08: Add security headers middleware
- **Risk:** No security headers are set. The app is vulnerable to clickjacking, MIME sniffing, and lacks CSP.
- **Scope:** Add a middleware in `app/backend/main.py`.
- **Headers to add:**
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains` (after HTTPS is live)
- **Files:** `app/backend/main.py`.

### SEC-09: Restrict or disable public signup
- **Risk:** Anyone on the internet can create an account and access all pet data and task controls.
- **Scope:** `app/backend/main.py`, possibly `app/frontend/templates/login.html`.
- **Options (pick one):**
  - **Invite code:** Require a shared household code (set via env var) during signup.
  - **Admin approval:** New accounts start disabled; existing user must approve.
  - **Disable signup:** Remove the signup form; only existing users can add new ones.
- **Files:** `app/backend/main.py`, `app/frontend/templates/login.html`, possibly `app/backend/auth.py`.

---

## P2 — Medium (do soon)

### SEC-10: Upgrade Jinja2 to ≥3.1.6
- **Risk:** CVE-2025-27516 — sandbox bypass allowing arbitrary code execution. Low practical risk here (app doesn't use sandbox), but should be patched.
- **Scope:** One-line change in `requirements.txt`.
- **Change:** `jinja2==3.1.4` → `jinja2>=3.1.6`.
- **Files:** `requirements.txt`.

### SEC-11: Strengthen password policy
- **Risk:** 6-character minimum with no complexity requirements is weak for a public-facing app.
- **Scope:** `app/backend/auth.py`.
- **Change:** Increase `MIN_PASSWORD_LENGTH` to 8. Optionally add complexity checks (mixed case, digit).
- **Update:** Client-side `minlength` attributes in `login.html` and `account.html` to match.
- **Files:** `app/backend/auth.py`, `app/frontend/templates/login.html`, `app/frontend/templates/account.html`.

### SEC-12: Secure the `check-in` endpoint
- **Risk:** `POST /api/users/check-in` is unauthenticated and can create users, set phone numbers, and trigger Twilio SMS to arbitrary numbers (costs money).
- **Scope:** `app/backend/main.py`.
- **Options:**
  - Add auth requirement (part of SEC-02).
  - Remove the endpoint entirely if it's truly legacy.
  - Add phone number validation (E.164 format regex).
- **Files:** `app/backend/main.py`, `app/backend/schemas.py`.

### SEC-13: Add uniqueness check for name updates
- **Risk:** `PUT /api/users/{id}` allows changing the display name without checking if the new name conflicts with an existing user, potentially breaking login.
- **Scope:** `app/backend/main.py` or `app/backend/crud.py`.
- **Change:** Before updating, check `crud.get_user_by_name(db, new_name)` and reject if taken.
- **Files:** `app/backend/main.py` or `app/backend/crud.py`.

### SEC-14: Remove source code volume mount for production
- **Risk:** `./app:/app/app` mount gives container write access to host source code. If the container is compromised, the attacker can modify the application.
- **Scope:** `docker-compose.yml`.
- **Approach:** Create a `docker-compose.override.yml` for dev (with the mount) and remove it from the base `docker-compose.yml`. Or use a `docker-compose.prod.yml`.
- **Files:** `docker-compose.yml`, possibly new `docker-compose.override.yml`.

---

## P3 — Low (backlog)

### SEC-15: Plan migration from `passlib` to `bcrypt` or `argon2-cffi`
- **Risk:** `passlib 1.7.4` is unmaintained (no updates since 2020). No current CVEs, but future vulnerabilities won't be patched.
- **Scope:** `app/backend/auth.py`, `requirements.txt`.
- **Approach:** Replace `passlib.context.CryptContext` with direct `bcrypt` calls or `argon2-cffi`. Existing bcrypt hashes remain compatible.
- **Files:** `app/backend/auth.py`, `requirements.txt`.

### SEC-16: Sanitize log output
- **Risk:** Phone numbers and user names are logged to stdout/container logs.
- **Scope:** `app/backend/sms_utils.py`, `app/backend/main.py`.
- **Change:** Mask phone numbers in log output (e.g., `+1***...7890`). Avoid logging PII.
- **Files:** `app/backend/sms_utils.py`, `app/backend/main.py`.

### SEC-17: Set `AUTH_SECRET_KEY` persistently
- **Risk:** If the env var isn't set, the JWT secret is randomized on every container restart, invalidating all sessions.
- **Scope:** `.env` file (not code).
- **Change:** Generate a strong key (`python -c "import secrets; print(secrets.token_urlsafe(64))"`) and add `AUTH_SECRET_KEY=<value>` to `.env`.
- **Verify:** Confirm `.env` is in `.gitignore` (it is).
- **Files:** `.env`.

### SEC-18: Upgrade all pinned dependencies
- **Risk:** Several dependencies are pinned to 2024 versions and may have accumulated patches.
- **Scope:** `requirements.txt`.
- **Approach:** Run `pip install --upgrade` for each, then run tests. Key upgrades: `jinja2`, `uvicorn`, `sqlalchemy`, `fastapi`.
- **Files:** `requirements.txt`.
