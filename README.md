# Virtual Card - Collation Card Project

A beautiful virtual card web application built with Flask, featuring three independent microservices for managing, submitting, and displaying greeting card messages.

## 🎯 Overview

This project implements a virtual card system where:
- **Admins** can review and approve messages, generate invite links, and manage the card cover
- **Users** submit messages via tokenized links with rich text and optional photos
- **Viewers** see an animated card with approved messages displayed beautifully

### Key Features

✨ **Three Independent Services**
- Dashboard (Admin) - Port 8000
- Submission (Public) - Port 8001
- Card Display (Protected) - Port 8002

🎨 **Beautiful UI**
- Animated card flip effect
- Center-out message rendering animation
- Deterministic pastel colors for each user
- Avatar with initials and hover effects
- Modal for full message view

🔒 **Security First**
- Designed for Traefik + Authentik authentication
- Content sanitization (XSS prevention)
- Image validation and processing
- Rate limiting and token-based access
- No reliance on forwarded auth headers

🏗️ **Production Ready**
- Docker containers for all services
- Shared database and media volumes
- Object-oriented architecture
- Comprehensive error handling

## 📋 Important Deployment Detail

The app is designed to run behind an external Traefik reverse proxy and Authentik instance. These services are managed separately and are NOT part of this repository's deployment. The Dashboard (management) and Card pages are protected by Authentik via Traefik, while the Submission service remains public. 

**Critical**: The Flask services MUST NOT read, parse, or act on authentication identity headers set by Traefik/authentik - Traefik/authentik handle authentication and access control. Application code should ignore forwarded auth identity headers and should not base authorization decisions on them.

## 🚀 Quick Start

### Development (Local)

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd collation-card
   cp .env.example .env
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run services** (choose one method):

   **Option A: Docker Compose** (recommended)
   ```bash
   docker-compose up --build
   ```

   **Option B: Development script**
   ```bash
   ./run_dev.sh
   ```

   **Option C: Manual**
   ```bash
   # Terminal 1 - Dashboard
   cd services/dashboard && python app.py
   
   # Terminal 2 - Submit
   cd services/submit && python app.py
   
   # Terminal 3 - Card
   cd services/card && python app.py
   ```

4. **Access the services**:
   - Dashboard: http://localhost:8000
   - Submit: http://localhost:8001/submit/<token>
   - Card: http://localhost:8002

### First Use

1. Access the dashboard at http://localhost:8000
2. Navigate to "Invite Links" and create a new link
3. Copy the token and visit http://localhost:8001/submit/<token>
4. Submit a test message
5. Go back to dashboard, approve the message
6. View the card at http://localhost:8002

## 📁 Project Structure

```
collation-card/
├── services/
│   ├── dashboard/          # Admin service (port 8000)
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── services.py     # Business logic
│   │   ├── templates/
│   │   └── Dockerfile
│   ├── submit/             # Submission service (port 8001)
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── services.py
│   │   ├── templates/
│   │   └── Dockerfile
│   └── card/               # Card display service (port 8002)
│       ├── app.py
│       ├── config.py
│       ├── services.py
│       ├── templates/
│       └── Dockerfile
├── shared/
│   ├── models.py           # SQLAlchemy models
│   └── utils/              # Shared utilities
│       ├── image_utils.py
│       ├── token_utils.py
│       └── sanitizer.py
├── docker-compose.yml
├── requirements.txt
├── ARCHITECTURE.md         # Detailed architecture
├── DEPLOYMENT.md           # Deployment guide
└── README.md               # This file
```

## 🛠️ Technology Stack

- **Backend**: Flask 3.0, SQLAlchemy
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Frontend**: TailwindCSS, Quill.js, Vanilla JS
- **Security**: Bleach (sanitization), python-magic (validation)
- **Rate Limiting**: Flask-Limiter + Redis
- **Deployment**: Docker, Traefik, Authentik

## 📖 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed system architecture, data flow, and design patterns
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide with Traefik + Authentik
- **Project Specification** - See below for complete specification

## 🔧 Configuration

Key environment variables (`.env`):

```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:////data/virtual_card.db
MEDIA_PATH=/media
REDIS_URL=memory://  # Use redis://redis:6379/0 for production
```

## 🧪 Testing

Run service tests:
```bash
python test_services.py
```

## 🐳 Docker Deployment

Build and run:
```bash
docker-compose build
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

Stop services:
```bash
docker-compose down
```

## 🔐 Security Notes

- Content is sanitized to prevent XSS attacks
- Images are validated and processed securely
- Rate limiting prevents abuse
- Token-based access control for submissions
- Authentication handled by external Traefik + Authentik
- Application code does NOT rely on forwarded auth headers

## 📝 License

[Your license here]

---

# Project Specification & Structure

Last updated: 2025-12-06

This document describes a complete project design for a "Virtual Card" web app built with Python + HTML using Flask. The system is split into three separate services (each hosted on its own port / container) and packaged for Docker.

---

Table of contents
- Overview
- High-level architecture
- File-tree / repo layout
- Services (3) - responsibilities, routes & endpoints
  - Dashboard (admin) service
  - Submission (public) service
  - Card (protected) service
- Traefik + authentik integration (deployment notes)
- Data model (sqlite) & migrations
- Workflow: messages lifecycle & links
- Security & abuse protections
- Rate limiting & quotas
- UI / front-end details (visual editor, rendering, animations)
- File upload & media handling
- Docker & deployment (docker-compose)
- Development, testing & CI notes
- Example config / env vars
- Implementation notes / code snippets
- Next steps & checklist

---

Overview

The app provides a virtual card page that shows user-submitted messages. Messages are created by visitors via generated submission links, then reviewed on an admin dashboard and approved to appear on the card page.

Three services (hosted separately, each on its own port so they can be containerized independently):
1. Dashboard (admin) - approve/reject messages, generate submission links, see abuse reports, manage card front image. Protected by authentik via Traefik.
2. Submission (public) - visual editor + photo upload + name. Open to the public (no authentik required).
3. Card page - shows a single front-cover image. When the cover pressed, it opens to reveal the dynamic messages page with animation and interactions. Protected by authentik via Traefik.

All messages are stored in SQLite. Only approved messages are shown on the Card service.

High-level architecture

- Each service is a Flask application. You can run them from a single repository with separate entrypoints or as distinct apps in the same monorepo.
- An external Traefik instance runs in front as the reverse proxy. It routes requests to containers and handles TLS.
- An external Authentik instance provides authentication for the Dashboard and Card routes via Traefik (forward-auth or OIDC). The submission service remains open (no authentik).
- Shared storage (Docker volume) holds the sqlite DB and uploaded media so the services access the same data.

Important operational note (auth headers)
- Traefik/authentik protect the routes. The Flask applications MUST NOT read or rely on forwarded authentication/identity headers (for example X-Forwarded-User, X-Auth-User, etc.). Do not implement authorization logic that depends on these headers.
- Treat Traefik/authentik as the enforcement layer only; the applications should assume that requests reaching them have already been permitted by Traefik. The app-level authorization decisions should be independent of headers injected by the proxy.
- It is fine to use proxy-aware middleware like ProxyFix so Flask correctly generates URLs and understands scheme/host, but do not use any forwarded identity headers for auth decisions or for user identity display.

File-tree (example)

```
virtual-card/
├─ services/
│  ├─ dashboard/                # Admin Flask app (port 8000)
│  │  ├─ app.py
│  │  ├─ config.py
│  │  ├─ models.py
│  │  ├─ views.py
│  │  ├─ templates/
│  │  ├─ static/
│  │  │  ├─ css/
│  │  │  └─ js/
│  │  └─ Dockerfile
│  ├─ submit/                   # Submission Flask app (port 8001)
│  │  ├─ app.py
│  │  ├─ config.py
│  │  ├─ models.py
│  │  ├─ views.py
│  │  ├─ templates/
│  │  ├─ static/
│  │  └─ Dockerfile
│  └─ card/                     # Card display Flask app (port 8002)
│     ├─ app.py
│     ├─ config.py
│     ├─ models.py
│     ├─ views.py
│     ├─ templates/
│     ├─ static/
│     └─ Dockerfile
├─ shared/
│  ├─ db/                       # Shared sqlite or volume mount target
│  ├─ media/                    # Uploaded images (volume)
│  └─ utils/                    # shared utils: image processing, token util
├─ docker-compose.yml
├─ Dockerfile.base
├─ requirements.txt
└─ VIRTUAL-CARD-PROJECT.md      # (this file)
```

Services - responsibilities & routes

1) Dashboard service (admin) - port 8000 (protected by Traefik+authentik)
- Purpose:
  - Admin interface that lists pending submissions, allows approving/rejecting messages, generates submission links, and manages the card cover.
- Protection:
  - Traefik + authentik enforce authentication at the proxy. The app MUST NOT read any identity headers from the proxy. Implement no server-side logic that parses such headers for authorization or identity.
  - If you require additional in-app authorization features (e.g., roles, permissions), implement them with an application-managed admin user store or via an explicit OIDC integration inside the app (not by trusting proxy headers). If you later choose to implement OIDC within the app, that should be a deliberate app-level integration.
- Core routes:
  - GET / - dashboard overview (pending count, recent submissions)
  - GET /messages/pending - list pending messages (paginated)
  - POST /messages/<message_id>/approve - approve message
  - POST /messages/<message_id>/reject - reject message
  - POST /cover - upload/replace front cover image
  - GET/POST /invite-links - manage tokenized submission links

2) Submission service (public) - port 8001 (open)
- Purpose:
  - Hosts submission forms reachable by tokenized invite links. Accepts text messages (rich text editor), optional photo upload, and name.
- Core routes:
  - GET /submit/<token> - visual editor form (token validation)
  - POST /submit/<token> - submit message (multipart/form-data for image)
  - GET /health - health check
- Features:
  - Visual editor: Quill or TinyMCE with server-side sanitization (bleach).
  - File upload: size limit (recommend 5 MiB), accept jpg/png/webp, validate MIME with python-magic, resize with Pillow, store in shared media.
  - Rate limiting: Flask-Limiter (Redis backend recommended).
  - Captcha: optional reCAPTCHA flow after thresholds.
- Behavior:
  - Submissions are stored with status='pending'; Dashboard approves them before they appear on the Card.

3) Card service (protected) - port 8002 (protected by Traefik+authentik)
- Purpose:
  - Shows the card front cover; when clicked, opens to reveal a dynamically rendered page with all approved messages.
- Protection:
  - Traefik + authentik protect the route. The app MUST NOT read any identity headers from the proxy.
- Core routes:
  - GET / - card cover page
  - GET /api/messages - returns approved messages as JSON
  - GET /media/<path> - serve media (thumbs/full)

Traefik + authentik integration (deployment notes)

**Note: Traefik and Authentik are external services and are not included in this repository's docker-compose.**

Design goals
- External Traefik enforces TLS and authentication. Dashboard and Card routers are configured with authentik middleware (forward-auth or OIDC).
- Submission router is public (no authentik).
- Flask apps do not parse or rely on auth identity headers coming from Traefik.

Traefik label examples (for reference only)
When configuring your external Traefik, you might use labels similar to these on your containers:

- Dashboard (protected):
  - labels include router rule and the authentik forward-auth middleware
- Card (protected):
  - same as dashboard
- Submission (open):
  - expose without authentik middleware

Example snippet (reference):

```yaml
services:
  dashboard:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`dashboard.example.com`)"
      - "traefik.http.routers.dashboard.entrypoints=websecure"
      - "traefik.http.routers.dashboard.middlewares=authentik-forward-auth@docker"
      - "traefik.http.services.dashboard.loadbalancer.server.port=8000"

  card:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.card.rule=Host(`card.example.com`)"
      - "traefik.http.routers.card.entrypoints=websecure"
      - "traefik.http.routers.card.middlewares=authentik-forward-auth@docker"
      - "traefik.http.services.card.loadbalancer.server.port=8002"

  submit:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.submit.rule=Host(`submit.example.com`)"
      - "traefik.http.routers.submit.entrypoints=websecure"
      - "traefik.http.services.submit.loadbalancer.server.port=8001"
```

Notes
- Configure the authentik Outpost or OIDC provider on your external Traefik/Authentik setup. The application should not rely on forwarded auth headers for identity or authorization.
- You may still use ProxyFix to ensure Flask URL generation and request.url reflect original scheme/host. ProxyFix is acceptable for proxying behavior (proto/host), but do not use it to read identity headers.

Data model (sqlite)

A shared sqlite database (or other RDBMS in production) stores messages, invite tokens, and admin data (if used).

Core tables:

- messages
  - id: INTEGER PRIMARY KEY AUTOINCREMENT
  - uuid: TEXT UNIQUE
  - name: TEXT
  - initials: TEXT
  - content: TEXT (sanitized HTML)
  - image_path: TEXT NULLABLE
  - thumb_path: TEXT NULLABLE
  - status: TEXT ('pending','approved','rejected') DEFAULT 'pending'
  - created_at: DATETIME
  - approved_at: DATETIME NULLABLE
  - ip_address: TEXT
  - color_hint: TEXT
  - order_index: INTEGER NULLABLE

- invite_links
  - token: TEXT PRIMARY KEY
  - created_at, expires_at, max_uses, uses_count, is_active, note

- admin_users (optional if the app manages its own admin users)
  - id, username, password_hash, role

- abuse_reports / rate_logs (optional)

Workflow: submit -> approve -> visible

1. Admin generates an invite link (Dashboard).
2. Visitor uses /submit/<token> to create a message (Submission service). Submission service enforces rate-limits and sanitizes content and images.
3. Message is stored with status='pending'.
4. Admin reviews pending messages on Dashboard and approves them.
5. Card service reads approved messages and renders them.

Security & abuse protections

- Rate limiting:
  - Use Flask-Limiter with Redis backend for the Submission service. Example: 5 submissions per IP per hour; 1 per minute.
- Captcha:
  - Optional reCAPTCHA/anti-bot for suspicious flows.
- Content sanitization:
  - Use bleach or similar to sanitize HTML from the visual editor and allow a safe subset of tags and attributes.
- File upload safety:
  - Validate MIME type with python-magic, enforce size limits, use secure filenames (uuid).
  - Generate thumbnails via Pillow; optionally convert to webp.
- Tokenized links:
  - Support TTL and max_uses.
- Logging:
  - Log suspicious attempts and blocked submissions for admin review.

Rate limiting & quotas

- Key policy:
  - per-IP using get_remote_address
  - per-token usage tracked in DB
- Example:
  - submission POST: "5 per hour; 1 per minute"
  - login: "5 per hour per account"

UI / front-end details (modern UI)

Framework
- TailwindCSS (CDN or prebuilt), minimal JS using Alpine.js, or vanilla JS.

Design language
- Clean, card-based UI with pastel outlines, rounded corners, and subtle shadows.

Submission page
- WYSIWYG editor (Quill/TinyMCE)
- Fields: Name, Message, Optional Photo
- Validation: client-side + server-side (sanitize)

Card page interactions
- Cover flip/open animation on click.
- Messages as tiles with faint pastel border (color computed deterministically).
- Avatar with initials in corner; hover expands to show name; click opens modal.
- Dynamic "center-out" animation when rendering messages:
  - Algorithm:
    1. Fetch ordered list of messages.
    2. Compute mid index and sequence [mid, mid+1, mid-1, ...].
    3. Apply incremental transition delays (e.g., 80ms steps).
    4. Animate from translateY/opacity to visible.

Example center-out order function (JS)

```javascript
function centerOutOrder(n) {
  const mid = Math.floor((n - 1) / 2);
  const order = [];
  let delta = 0;
  while (order.length < n) {
    const right = mid + delta;
    const left = mid - delta;
    if (right < n) order.push(right);
    if (left !== right && left >= 0) order.push(left);
    delta++;
  }
  return order;
}
```

Message tile styles (outline + avatar)
- Generate pastel color via deterministic hash of uuid/name -> hue -> HSL with high lightness for faint outlines.
- Avatar: initials text in a colored circle; scale/expand on hover via CSS transitions.

Client API (Card service)
- GET /api/messages -> returns approved messages JSON:
  - fields: uuid, name, initials, content_html (sanitized), thumb_url, image_url, color_hint, created_at

File upload & media handling

- Store images under shared media volume (/media) in date-based directories.
- Filenames: uuid4 + extension.
- Generate thumb (200px max) and constrained full image (max width 1600px).
- Validate MIME and file size, optionally run ClamAV for scanning.
- Serve media using Flask static route in dev or via a static file server (nginx) in production.

Docker & deployment (docker-compose)

- Base Python image with dependencies. Each service contains a small Dockerfile using the base.
- Use docker-compose to wire the three services. Traefik and Authentik are assumed to be running externally.
- Use named volumes for data and media.

Development & testing

- Local dev uses SQLite. For production prefer PostgreSQL.
- Unit tests: message creation, sanitization, token validation, rate-limiter behaviors.
- E2E tests: Playwright or Selenium for submit -> approve -> view.
- Linting: black, isort, flake8.

Example environment variables

- SECRET_KEY
- DATABASE_URL (sqlite:////data/virtual_card.db or postgres)
- ADMIN_INITIAL_USERNAME / ADMIN_INITIAL_PASSWORD (if creating local admin users)
- RATE_LIMIT_RULES
- MAX_IMAGE_SIZE
- MEDIA_PATH
- RECAPTCHA_SITE_KEY / RECAPTCHA_SECRET (optional)

Implementation notes & code snippets

- Using ProxyFix is acceptable for correct URL generation behind Traefik:

```python
from werkzeug.middleware.proxy_fix import ProxyFix

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
```

- Do NOT read or rely on identity headers injected by Traefik/authentik. The app should ignore headers such as X-Forwarded-User, X-Auth-User, etc.

**Coding Conventions (OOP)**

- **Follow object-oriented design:** Implement application logic using classes to encapsulate behavior and state. Prefer class-based Flask patterns (e.g., factory functions returning configured `Flask` instances and class-based service components) rather than putting procedural logic into single large modules.
- **Models as classes:** Define data models and domain logic using ORM models or typed `dataclass`/Pydantic models where appropriate. Keep validation, serialization, and business rules with the model or a dedicated service layer.
- **Service / repository layers:** Use service classes (e.g., `MessageService`, `InviteService`, `MediaService`) to handle business logic and a repository/DAO layer to isolate persistence (SQLite) operations. This separation improves testability and makes swapping databases easier.
- **Separation of concerns:** Keep views/controllers thin - they should parse requests, call service methods, and return responses. Avoid embedding business rules or I/O directly in view functions.
- **Dependency injection:** Pass dependencies (db session, storage path, limiter, config) into service constructors or use a lightweight DI/factory pattern to keep components decoupled and easier to unit test.
- **Typed interfaces & docstrings:** Use type annotations for public methods and dataclasses/DTOs for structured data. Add concise docstrings to classes and methods to document intent.
- **Testing:** Write unit tests for class methods (services, repositories, models) and use integration tests for route behavior. Mock external dependencies (file storage, rate-limiter) in unit tests.


- Flask-Limiter example:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

- Deterministic pastel color JS:

```javascript
function pastelFromString(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) { h = (h << 5) - h + s.charCodeAt(i); h |= 0; }
  const hue = Math.abs(h) % 360;
  return `hsl(${hue} 60% 90%)`;
}
```

Operational considerations

- Backups for DB and media.
- Monitor health endpoints; use Prometheus metrics and Sentry for errors.
- Logs -> stdout for container aggregation.
- For scale, move from SQLite to PostgreSQL.

Accessibility & UX

- Ensure color contrast for text.
- Keyboard accessible modal and controls.
- Alt text for images, aria attributes.

Acceptance checklist

- [ ] Services are ready to be proxied by external Traefik.
- [ ] Dashboard and Card are ready to be protected by external Authentik.
- [ ] Submission service public and reachable without authentik.
- [ ] Flask apps do NOT read or act on auth identity headers from Traefik/authentik.
- [ ] Invite link creation, token validation, rate limiting, and content sanitization implemented.
- [ ] Card UI renders with center-first animation, avatars, hover expand, modal, and pastel outlines.
- [ ] Media handling and thumbnails implemented.
- [ ] Tests for critical flows in place.

Quick start (dev)

1. Create .env with SECRET_KEY and other values.
2. docker-compose build
3. docker-compose up
4. Access the services via the ports exposed (8000, 8001, 8002) or configure your external proxy to point to them.