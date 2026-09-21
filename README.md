# Demo Buy

A single-category (phones) e-commerce site built with Django. Session-based cart, email + Google login, search/filter, and WhatsApp checkout.

## Features

- Custom user model (email + username + password), email-based password reset, Google OAuth login (django-allauth)
- Product catalog (name, price, stock quantity, image, description) with an admin panel for managing inventory
- Home page grid with "Add to Cart" (no login required)
- Search by name + price filters (under ₦5,000 / over ₦5,000 / ₦5,000–₦10,000 / custom range)
- Session cart with header icon + floating cart button, quantity update/remove, subtotal/total
- Checkout only for logged-in users: deducts stock atomically, validates against available inventory, clears the cart, then redirects to a pre-filled WhatsApp message
- Dark/light mode toggle persisted in `localStorage`
- CSRF protection, `@login_required` on checkout, custom 404 page

## 1. Setup

```bash
python3 -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and fill in a real `DJANGO_SECRET_KEY` (any long random string) plus whichever
email/Google settings you plan to use (see below — safe defaults are provided for local dev).

## 2. Database

```bash
python manage.py migrate
python manage.py createsuperuser
```

SQLite is used by default (`db.sqlite3`). To use PostgreSQL instead, set `DATABASE_URL` in
`.env`, e.g. `DATABASE_URL=postgres://user:password@host:5432/dbname`.

## 3. Run

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`. Add products at `http://127.0.0.1:8000/admin/`.

## 4. Email (password reset)

Set `EMAIL_BACKEND_TYPE` in `.env` to one of:

- `console` (default) — emails print to the terminal, nothing is actually sent. Good for local dev.
- `smtp` — Gmail SMTP. Set `EMAIL_HOST_USER` to your Gmail address and `EMAIL_HOST_PASSWORD` to a
  [Gmail App Password](https://myaccount.google.com/apppasswords) (not your normal password — you need
  2‑Step Verification enabled first).
- `sendgrid` — set `SENDGRID_API_KEY` to a free-tier SendGrid API key.

## 5. Google OAuth login

1. Go to the [Google Cloud Console](https://console.cloud.google.com/apis/credentials) → create an
   OAuth 2.0 Client ID (Web application).
2. Add authorized redirect URI: `http://127.0.0.1:8000/accounts/google/login/callback/`
   (and your production domain equivalent later).
3. Copy the Client ID and Client Secret into `.env` as `GOOGLE_OAUTH_CLIENT_ID` and
   `GOOGLE_OAUTH_CLIENT_SECRET`.
4. In the Django admin, under **Sites**, edit the default site (`example.com`) to match your domain
   (`127.0.0.1:8000` for local dev). django-allauth reads the redirect URI from this Site record.
5. Restart the server. The "Sign in with Google" button on the login/signup pages will now work.

## 6. WhatsApp checkout number

Set `WHATSAPP_NUMBER` in `.env` (international format, digits only, e.g. `2348072552365`).
This is the number that receives the pre-filled `wa.me` order message when a customer checks out.

## 7. Project layout

```
demobuy/
├── manage.py
├── demobuy/          # project settings, root urls
├── accounts/         # custom user model, login/signup/password-reset views & templates
├── products/         # Product model, session cart, home/search/cart/checkout views
├── templates/         # base.html, 404.html
├── static/            # css/js (dark mode toggle, layout)
├── media/              # uploaded product images (created on first upload)
├── requirements.txt
└── .env.example
```

## 8. Walkthrough of main features

- **Browsing** — `/` lists all products as cards (image, name, price, stock). Query params `q`,
  `price` (`under_5000` / `over_5000` / `5000_10000`), and `min_price`/`max_price` filter the grid;
  they combine (chained queryset filtering).
- **Cart** — adding a product (`POST /cart/add/<id>/`) stores `{product_id: quantity}` in the
  session, no login needed. `/cart/` shows the full cart with per-item quantity update/remove forms
  and a running total.
- **Checkout** — `POST /checkout/` (login required) re-validates stock for every cart line inside a
  DB transaction with row locking, decrements `Product.quantity`, clears the session cart, then
  redirects to `https://wa.me/<number>?text=...` with the order summary. If any item is out of
  stock, nothing is deducted and the user is sent back to the cart with an error message.
- **Auth** — `/accounts/signup/` and `/accounts/login/` support username or email; Google OAuth is
  available via django-allauth on both pages. `/accounts/password-reset/` runs Django's built-in
  reset flow through the configured email backend.
- **Admin** — `/admin/` lets staff add, edit, and delete phones and manage users.

## 9. Deploying for free

The project ships ready for two free-tier options: **Render** (recommended — full free web
service + Postgres, no card required) and **PythonAnywhere** (simplest, Django-specific, no card
required). `whitenoise` is already wired in so static files (CSS/JS/admin assets) are served
correctly with `DEBUG=False`, without needing a separate static host or CDN.

### Option A — Render

1. Push this project to a GitHub repo.
2. In the Render dashboard: **New → Blueprint**, point it at the repo. Render reads `render.yaml`
   in this project and creates a free web service + free Postgres database automatically.
3. Render generates `DJANGO_SECRET_KEY` for you and wires `DATABASE_URL` to the new database. You
   still need to set, in the service's **Environment** tab:
   - `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET` (see step 5 below)
   - `EMAIL_BACKEND_TYPE=smtp` (or `sendgrid`) plus the matching credentials, once you're ready to
     send real emails — it defaults to `console` (no real email is sent) so the app deploys clean
     first.
4. First deploy runs `collectstatic` and `migrate` automatically (see `render.yaml` /
   `Procfile`). Create an admin user from the Render **Shell** tab: `python manage.py createsuperuser`.
5. Update the Google Cloud Console OAuth client's authorized redirect URI to
   `https://<your-service>.onrender.com/accounts/google/login/callback/`, and set the Django
   **Sites** record (`/admin/sites/site/`) domain to `<your-service>.onrender.com`.

Notes: the free web service spins down after 15 minutes idle (~1 min cold start on the next
request), and the free Postgres database is deleted 90 days after creation (not 90 days of
inactivity) — recreate it and update `DATABASE_URL` before then, or upgrade to a paid instance.

### Option B — PythonAnywhere

1. Create a free account, then open a **Bash console** and clone/upload this project.
2. `mkvirtualenv --python=python3.10 demobuy-env && pip install -r requirements.txt`
3. **Web** tab → **Add a new web app** → Manual configuration → your Python version → point the
   virtualenv path at `demobuy-env`.
4. Edit the generated WSGI file to import this project's WSGI application:
   ```python
   import os, sys
   sys.path.insert(0, "/home/yourusername/demobuy")
   os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demobuy.settings")
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
5. In the **Files** tab, create `.env` (copy from `.env.example`) with `DJANGO_DEBUG=False` and
   `DJANGO_ALLOWED_HOSTS=yourusername.pythonanywhere.com`. SQLite works fine here since the disk is
   persistent (unlike Render's free tier).
6. **Static files** section on the Web tab: map URL `/static/` to
   `/home/yourusername/demobuy/staticfiles`, and `/media/` to `/home/yourusername/demobuy/media`.
   Run `python manage.py collectstatic` from the console first.
7. Run `python manage.py migrate` and `python manage.py createsuperuser` from the console, then hit
   **Reload** on the Web tab.
8. PythonAnywhere's free tier only allows outbound requests to a small allowlist of external
   sites — Google's OAuth domains are on it, but double-check if the "Sign in with Google" button
   fails; SMTP email sending is also restricted on the free tier, so `EMAIL_BACKEND_TYPE=console`
   (or a webhook-based provider like SendGrid's HTTPS API instead of SMTP) is the safer bet there.

## 10. Production settings checklist

- `DJANGO_DEBUG=False`, a real random `DJANGO_SECRET_KEY`, and `DJANGO_ALLOWED_HOSTS` set to your
  real domain(s).
- `DJANGO_CSRF_TRUSTED_ORIGINS` set to `https://your-domain` (comma-separated for multiple).
- `DATABASE_URL` pointed at your platform's managed Postgres — SQLite works but won't survive
  Render's ephemeral filesystem between deploys (PythonAnywhere's disk is persistent, so SQLite is
  fine there).
- A real `EMAIL_BACKEND_TYPE` (`smtp` or `sendgrid`) so password-reset emails actually send —
  `console` only prints to the server log.
- `ACCOUNT_EMAIL_VERIFICATION = "mandatory"` in `demobuy/settings.py` once real email is wired up.
- Updated Google OAuth redirect URI + Django **Sites** domain for your live URL (see step 5/8
  above).
- `python manage.py collectstatic --noinput` — already automated in `render.yaml`/`Procfile`, but
  needs a manual run on PythonAnywhere.
- Product images: free-tier disks (Render especially) are ephemeral, so uploaded images can vanish
  on redeploy/restart. Fine for a demo; for anything real, swap `MEDIA` storage for Cloudinary's
  free tier or S3.
