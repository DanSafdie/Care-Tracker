# Security Hardening Backlog

> Generated from security audit on 2026-03-16.  
> Prioritized for a public-facing deployment (port-forwarded via DynDNS).  
> Roadmap accounts for planned expansion to track human medications (PII/PHI).  
> Each task is self-contained and can be picked up independently unless noted.

**Context note:** An nginx reverse proxy already runs in a separate Docker project
(WorkoutTracker). Any HTTPS/proxy work must interplay with that existing setup —
ask before making changes that could affect the other project.

**Access model:** Public signup stays open. Anyone with an account can see pet
care data (dogs). Future meds/health data will be scoped per-user via
permissions columns in the DB — not by restricting who can sign up.

---

## P0 — Critical (do immediately)

These matter right now, regardless of the meds expansion.

### SEC-01: Add HTTPS via reverse proxy
- **Status:** DEFERRED — requires a dedicated infrastructure session.
- **Risk:** Passwords, JWT cookies, and all data travel in plaintext over the public internet. With future med data, this becomes a PII leak vector.
- **Scope:** Infrastructure / Docker config only — no app code changes.
- **Note:** Nginx is already running in a sibling Docker project (WorkoutTracker). Options:
  1. **Extend the existing nginx** to also proxy Care-Tracker (shared reverse proxy).
  2. **Switch to a shared Caddy instance** that handles both projects (Caddy auto-provisions Let's Encrypt).
  3. **Add a separate proxy** just for Care-Tracker (simpler but duplicates infra). (assuming its just more processing power, no big deal. this would be  prefered. )
- **Architecture decision (2026-03-16):** The ideal pattern is a single shared reverse
  proxy (Caddy or nginx) in its own Docker Compose project with an external Docker
  network that other project containers join. This avoids duplicating proxy infra per
  project but requires planning across WorkoutTracker + Care-Tracker together.
- **Depends on:** Understanding the existing nginx setup first. SEC-08 should follow once HTTPS is live.
- **Files:** `docker-compose.yml`, new proxy config, possibly the WorkoutTracker project.

### SEC-02: Add authentication to all API endpoints
- **Risk:** 14+ API endpoints have zero auth. Anyone can read/modify pet care data, and once meds are added, that's health information exposed to the internet.
- **Scope:** `app/backend/main.py` — add `Depends(get_current_user)` to every unprotected route.
- **Endpoints to protect:**
  - `GET /api/pets`, `POST /api/pets`, `GET /api/pets/{id}`
  - `POST /api/pets/{id}/timer`, `DELETE /api/pets/{id}/timer`
  - `GET /api/care-items`, `POST /api/care-items`
  - `GET /api/status`
  - `POST /api/tasks/{id}/complete`, `POST /api/tasks/{id}/undo`
  - `GET /api/history`, `GET /api/history/grid`
  - `GET /api/users/search`, `GET /api/users/by-name/{name}`
  - `POST /api/users/check-in` (also see SEC-07)
- **Leave unauthenticated:** `GET /api/info` (non-sensitive), `/login`, `/signup`, `/logout`.
- **Test:** Run `pytest` after changes. Update test fixtures to include auth cookies.
- **Files:** `app/backend/main.py`, `tests/conftest.py`, `tests/test_api_endpoints.py`.

### SEC-03: Remove traceback from API error responses
- **Risk:** Full Python tracebacks leak file paths, library versions, and internal logic. Since this machine hosts the app AND is on the home network, this aids lateral movement.
- **Scope:** One-line change in `app/backend/main.py`.
- **Change:** In the exception middleware (~line 87-89), remove `"traceback": traceback.format_exc()` from the JSON response. Keep the `print()` for server-side logging.
- **Files:** `app/backend/main.py`.

### SEC-04: Disable FastAPI auto-generated docs
- **Risk:** `/docs` and `/redoc` give unauthenticated users a complete interactive map of every endpoint, parameter, and schema.
- **Scope:** One-line change in `app/backend/main.py`.
- **Change:** `app = FastAPI(..., docs_url=None, redoc_url=None)`.
- **Files:** `app/backend/main.py`.

---

## P1 — High (do this week)

These become important with the meds expansion — health data raises the stakes.

### SEC-05: Restrict or disable public signup
- **Status:** SUPERSEDED — public signup stays open by design.
- **Original risk:** Anyone on the internet can create an account and access all data.
- **Decision (2026-03-16):** Pet care data (dogs) is intentionally public to any
  signed-in user. Future med/health data will be scoped per-user via a permissions
  or ownership column in the database, so open signup is not the threat vector —
  data visibility is. SEC-02 (auth on endpoints) already prevents unauthenticated
  access. A permissions/RBAC model will be added when meds tracking is built.
- **No code changes needed for this item.**

### SEC-06: Secure the `check-in` endpoint / SMS abuse
- **Risk:** `POST /api/users/check-in` is unauthenticated and can trigger Twilio SMS to arbitrary phone numbers, costing real money. Also creates users freely.
- **Scope:** `app/backend/main.py`.
- **Approach:** Auth-protect it (covered by SEC-02), or remove it entirely if it's truly legacy. Add E.164 phone number validation regardless.
- **Files:** `app/backend/main.py`, `app/backend/schemas.py`.

### SEC-07: Add rate limiting on login and SMS endpoints
- **Risk:** No rate limiting anywhere. With med data, brute-forcing a login becomes more motivated. SMS spam costs money.
- **Scope:** Add `slowapi` middleware.
- **Approach:**
  1. `pip install slowapi`.
  2. Rate limits: `/login` and `/signup` (5/min), `/api/users/check-in` (3/min).
  3. Return 429 with a clear message.
- **Files:** `app/backend/main.py`, `requirements.txt`.

### SEC-08: Add `secure` flag to session cookies
- **Status:** DEFERRED — depends on SEC-01 (HTTPS must be working first).
- **Risk:** Without `secure=True`, the JWT cookie is sent over HTTP and can be intercepted.
- **Scope:** Two `set_cookie()` calls in `app/backend/main.py` (login and signup).
- **Change:** Add `secure=True` to both. Cannot enable until HTTPS is live or the
  cookie won't be sent over plain HTTP, locking everyone out.
- **Files:** `app/backend/main.py`.

### SEC-09: Add security headers middleware
- **Risk:** With health data, clickjacking and XSS protections become worthwhile.
- **Scope:** Add a middleware in `app/backend/main.py`.
- **Headers to add:**
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains` (after HTTPS)
- **Files:** `app/backend/main.py`.

---

## P2 — Medium (do when expanding to meds)

### SEC-10: Upgrade Jinja2 to ≥3.1.6
- **Risk:** CVE-2025-27516 — sandbox bypass. Low practical risk (app doesn't use sandbox), but trivial to fix.
- **Change:** `jinja2==3.1.4` → `jinja2>=3.1.6` in `requirements.txt`.
- **Files:** `requirements.txt`.

### SEC-11: Strengthen password policy
- **Risk:** 6-character minimum is fine for family pet tracking, weak for health data.
- **Change:** Increase `MIN_PASSWORD_LENGTH` to 8 in `app/backend/auth.py`. Update client-side `minlength` in `login.html` and `account.html`.
- **Files:** `app/backend/auth.py`, `app/frontend/templates/login.html`, `app/frontend/templates/account.html`.

### SEC-12: Sanitize log output
- **Risk:** Phone numbers logged to stdout. Once med data exists, any leaked PII compounds the problem.
- **Change:** Mask phone numbers in logs (e.g., `+1***...7890`).
- **Files:** `app/backend/sms_utils.py`, `app/backend/main.py`.

### SEC-13: Remove source code volume mount for production
- **Risk:** `./app:/app/app` mount gives the container write access to host source code.
- **Approach:** Move the mount to a `docker-compose.override.yml` for dev only.
- **Files:** `docker-compose.yml`, new `docker-compose.override.yml`.

---

## P3 — Backlog (nice-to-have)

### SEC-14: Add uniqueness check for name updates
- **Risk:** `PUT /api/users/{id}` allows name changes that could collide with existing users.
- **Change:** Check `crud.get_user_by_name()` before updating; reject if taken.
- **Files:** `app/backend/main.py` or `app/backend/crud.py`.

### SEC-15: Replace `python-jose` with `PyJWT`
- **Risk:** `python-jose` has unpatched CVEs, but they require specific attack scenarios (public key access, crafted JWE tokens) not applicable to this HS256 setup. Low practical risk.
- **Approach:** Swap to `PyJWT[crypto]` — very similar API. Do when convenient.
- **Files:** `app/backend/auth.py`, `requirements.txt`.

### SEC-16: Migrate from `passlib` to `bcrypt` or `argon2-cffi`
- **Risk:** `passlib` unmaintained since 2020. No current CVEs. Fix when it breaks.
- **Files:** `app/backend/auth.py`, `requirements.txt`.

### SEC-17: Set `AUTH_SECRET_KEY` persistently
- **Risk:** Without the env var, the JWT secret randomizes on every restart, invalidating sessions.
- **Change:** Add `AUTH_SECRET_KEY=<generated value>` to `.env`.
- **Files:** `.env`.

### SEC-18: Upgrade all pinned dependencies
- **Risk:** Several deps pinned to 2024 versions.
- **Approach:** `pip install --upgrade` for each, then run tests.
- **Files:** `requirements.txt`.
