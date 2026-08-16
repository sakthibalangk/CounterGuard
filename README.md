# CounterGuard

**Smart Fake Product Detection & Verification System using Barcode**

A web-based platform that lets consumers verify whether a product is genuine
or counterfeit by scanning its barcode, and gives administrators full control
over the product catalog, barcode assignment, user management, and
counterfeit reports.

> **Build status:** All 10 modules complete ✅ — Foundation, Authentication, Product Management, Barcode Scanning & Verification, Scan History, Counterfeit Reporting, Admin User Management, Analytics Dashboard, Profile Management & Settings, and Security Hardening.
> Scan history, reporting, and the rest of the admin dashboard are
> being built next, one module at a time.

---

## Tech Stack

| Layer      | Technology |
|------------|------------|
| Frontend   | HTML5, CSS3, JavaScript, Bootstrap 5, Font Awesome, Chart.js |
| Backend    | Python (Flask), MVC architecture, Flask Blueprints |
| Database   | MySQL |
| Barcode    | OpenCV, pyzbar, python-barcode |
| Images     | Pillow |
| Security   | Werkzeug password hashing, parameterized SQL queries |

## Project Structure

```
CounterGuard/
├── app.py                # Application factory + entry point
├── config.py             # Environment-driven configuration
├── database.sql          # MySQL schema (run once to create the DB)
├── requirements.txt
├── .env.example           # Copy to .env and fill in real values
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   ├── images/
│   ├── uploads/           # Product images uploaded by admins
│   └── barcodes/          # Generated barcode images
├── templates/
│   ├── base.html          # Shared layout (navbar, flash messages, footer)
│   ├── index.html
│   └── error.html
├── models/                # Data-access classes (one per table) — Module 2+
├── routes/                # Flask Blueprints — Module 2+
└── utils/
    └── db.py              # Per-request MySQL connection helper
```

## Setup (Module 1)

1. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

   > `pyzbar` also needs the system library `libzbar0` (Linux) or `zbar`
   > (via Homebrew on macOS) installed — this comes in the barcode-scanning
   > module, not required to run Module 1.

2. **Create the database**
   ```bash
   mysql -u root -p < database.sql
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # then edit .env with your real MySQL password, secret key, etc.
   ```

4. **Create your first admin account**
   ```bash
   python scripts/seed_admin.py
   ```
   This reads `DEFAULT_ADMIN_*` from your `.env` and creates one admin
   account so you have a way into `/admin/login` without writing SQL
   by hand. Safe to re-run — it won't create a duplicate.

5. **Run the app**
   ```bash
   python app.py
   ```
   Visit `http://127.0.0.1:5000/` — you'll see the landing page with
   separate **Customer** and **Admin** entry points. Register a
   customer account, or log in to `/admin/login` with the admin
   credentials from step 4.

6. **Try scanning a barcode**
   As a customer, click **Scan a Barcode** from your dashboard. The
   Camera tab needs a secure context to access your webcam — it works
   fine at `http://127.0.0.1:5000` or `http://localhost:5000`, but
   browsers block camera access over a plain `http://<lan-ip>:5000`
   URL. If you're testing from another device on your network (or the
   camera otherwise won't start), use the **Upload Photo** or
   **Enter Manually** tabs instead — both use the same OpenCV/zxing-cpp
   decoding and database lookup underneath.

## Deployment

CounterGuard ships with a `Dockerfile` so it can run identically on
any container host.

**Recommended free-tier path (no credit card on either service):**

1. **Database — [Aiven for MySQL](https://aiven.io/free-mysql-database)**
   (always-free tier, 1GB storage/RAM, no expiry). Create a service,
   download its CA certificate, and note the host/port/user/password
   it gives you.
2. **App — [Render](https://render.com)**, as a Docker-based Web
   Service connected to your GitHub repo. Render's free tier gives
   750 instance-hours/month; the service sleeps after 15 minutes of
   inactivity and takes 30-60s to wake on the next request — fine for
   a portfolio/demo project, not for something that needs to be always
   instantly responsive.
3. Set the environment variables from `.env.example` in Render's
   dashboard (never commit a real `.env`), pointing `DB_HOST` etc. at
   your Aiven service and `DB_SSL_CA` at the CA cert.
4. Run `database.sql` against the Aiven database once, and
   `scripts/seed_admin.py` once, before or right after your first
   deploy.

**Known limitation:** uploaded product photos and generated barcode
images are written to local disk (`static/uploads/`,
`static/barcodes/`). Most free container hosts — including Render's
free tier — have an *ephemeral* filesystem: anything written there is
wiped on every redeploy or restart. That's acceptable for a
demo/portfolio deployment, but re-adding products after a redeploy is
expected. Moving image storage to something like S3/Cloudinary would
be the next step for a persistent production deployment — out of
scope for this project's current modules.

## Security & Hardening

- **Passwords** are hashed with Werkzeug's `generate_password_hash` — never stored in plaintext.
- **CSRF protection** via Flask-WTF on every form in the app.
- **Parameterized SQL** throughout — no string-formatted queries, anywhere.
- **Rate limiting** (Flask-Limiter) on login, registration, password-change, and report-submission
  endpoints, to blunt naive brute-force and spam attempts. Uses in-memory storage, which is
  appropriate for this project's single-instance scope — see the comment in
  `utils/rate_limit.py` for how to point it at Redis for a multi-worker deployment.
- **Security headers** (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`) set on
  every response via an `after_request` hook in `app.py`.
- **Session hardening**: HttpOnly + SameSite=Lax cookies always; Secure cookies (HTTPS-only) in
  production via `ProductionConfig`.
- **Role isolation**: customer and admin sessions use entirely separate session keys and
  decorators (`login_required` vs `admin_required`) — see `utils/decorators.py`.
- **Upload validation**: file type and actual image content (via Pillow's `.verify()`, not just
  the file extension) checked before anything is saved to disk.
- **Production logging**: a rotating log file (`logs/counterguard.log`) is written whenever the
  app runs outside debug mode, so a deployed instance's errors are recoverable after the fact.

## Known Limitations & Future Work

Worth being upfront about, both for anyone evaluating this project and for future development:

- **Barcode-only trust model.** A product shows "Genuine" purely because its barcode exists in
  the database — this verifies the barcode was registered, not that the physical item in the
  customer's hand is authentic. A shared barcode scanned from two different fake units would
  still show "Genuine." Real anti-counterfeiting systems mitigate this with unique **per-unit**
  serial numbers rather than one shared barcode per product line — a natural next step beyond
  this project's scope.
- **Any admin account can register any product as genuine.** There's currently no separate
  "manufacturer" role or approval workflow — an admin account is fully trusted by definition.
  A production version of this system would likely add a `manufacturer` role scoped to their
  own company's products, with a `super_admin` approval step before a new product goes live,
  plus visible provenance ("registered by X on Y date") so customers can see who vouched for a
  product, not just whether one exists.
- **Rate limiting is single-instance.** As noted above, the in-memory storage backend means
  limits reset if the process restarts and aren't shared across multiple gunicorn workers or
  horizontally-scaled instances. Fine for this project's scale; would need Redis-backed storage
  to scale further.
- **No email verification or password reset flow.** Registration and password changes are
  immediate with no email confirmation step — a real deployment would want both.

## Roadmap

- [x] Module 1 — Project scaffold, config, database schema, app factory
- [x] Module 2 — Authentication (customer register/login, admin login, session management, CSRF protection, role-isolated portals)
- [x] Module 3 — Product management (admin CRUD, image upload with Pillow, auto barcode generation with python-barcode)
- [x] Module 4 — Barcode scanning & verification (webcam capture, photo upload, and manual entry, decoded with OpenCV + zxing-cpp)
- [x] Module 5 — Scan history (paginated, filterable by result, scoped to the logged-in customer)
- [x] Module 6 — Counterfeit reporting (customer submission with optional evidence photo, admin review queue with status workflow and notes)
- [x] Module 7 — Admin user management (searchable customer list, activity detail view, activate/deactivate)
- [x] Module 8 — Analytics dashboard (Chart.js: scan trends, genuine/not-found breakdown, top products, report status)
- [x] Module 9 — Profile management & settings (customer profile edit + password change, admin settings + password change)
- [x] Module 10 — Polish, validation hardening, deployment notes (rate limiting, security headers, production logging)
