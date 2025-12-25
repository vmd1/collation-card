# Architecture Overview

## Service Architecture

This project consists of three independent Flask services:

### 1. Dashboard Service (Port 8000)
**Protected by Traefik + Authentik**

Responsibilities:
- Review pending message submissions
- Approve/reject messages
- Generate invite tokens/links
- Upload and manage card cover image

Key Components:
- `MessageService` - Handle message approval workflow
- `InviteLinkService` - Token generation and management
- `CoverService` - Card cover image management

### 2. Submission Service (Port 8001)
**Public - No Authentication Required**

Responsibilities:
- Validate invite tokens
- Accept message submissions with rich text editor
- Handle image uploads with validation
- Rate limiting and abuse prevention

Key Components:
- `SubmissionService` - Process and validate submissions
- `ContentSanitizer` - Sanitize HTML content
- `ImageProcessor` - Validate and process uploaded images
- Flask-Limiter - Rate limiting per IP

### 3. Card Service (Port 8002)
**Protected by Traefik + Authentik**

Responsibilities:
- Display card cover image
- Show approved messages with animations
- Provide JSON API for messages
- Serve media files

Key Components:
- `CardService` - Fetch approved messages
- Center-out animation rendering
- Modal interactions for message details

## Data Flow

```
1. Admin generates invite token (Dashboard)
   ↓
2. User visits /submit/<token> (Submission)
   ↓
3. User submits message (pending status)
   ↓
4. Admin reviews on Dashboard
   ↓
5. Admin approves message
   ↓
6. Message appears on Card page
```

## Database Schema

### Messages Table
- Stores all submissions
- Status: pending/approved/rejected
- Includes sanitized HTML content
- References image paths in media storage

### InviteLinks Table
- Token-based access control
- Configurable expiration and usage limits
- Tracks usage count

### CardCovers Table
- Manages front cover image
- Only one active cover at a time

## Security Architecture

### Authentication Layers
- **Traefik + Authentik**: External authentication for Dashboard and Card services
- **Application Level**: NO authentication headers are read or trusted by Flask apps
- **Token Validation**: Submission service validates invite tokens from database

### Content Security
- HTML sanitization with bleach
- Image validation with python-magic
- File size limits enforced
- Secure filename generation (UUID)

### Rate Limiting
- Per-IP rate limits on submission endpoint
- Configurable thresholds
- Redis backend for production (memory for dev)

## Object-Oriented Design

### Service Layer Pattern
Each service implements business logic in dedicated service classes:
- `MessageService` - Message operations
- `InviteLinkService` - Token operations
- `SubmissionService` - Submission processing
- `CardService` - Card display operations
- `CoverService` - Cover management

### Shared Utilities
- `ImageProcessor` - Image handling and validation
- `TokenGenerator` - Secure token generation
- `ContentSanitizer` - HTML sanitization

### Separation of Concerns
- **Models** (`shared/models.py`): Database schema with SQLAlchemy
- **Services** (each service's `services.py`): Business logic
- **Views** (each service's `app.py`): HTTP request handling
- **Templates**: Presentation layer

## Frontend Architecture

### Dashboard
- Server-rendered with Jinja2
- TailwindCSS for styling
- Simple form submissions

### Submission Page
- Quill.js rich text editor
- Client-side form validation
- Image upload preview
- Responsive design

### Card Page
- 3D card flip animation (CSS)
- Center-out message rendering
- Pastel color generation from names
- Avatar hover effects
- Modal for message details
- Fetch API for dynamic message loading

## Deployment Architecture

```
[Traefik Reverse Proxy]
         |
         ├──[Authentik]──→ [Dashboard Service:8000]
         |                        ↓
         ├──────────────→ [Submit Service:8001]
         |                        ↓
         └──[Authentik]──→ [Card Service:8002]
                                 ↓
                    [Shared SQLite DB + Media Volume]
```

### Key Points
- Three independent containers
- Shared volumes for database and media
- Traefik handles routing and TLS
- Authentik protects Dashboard and Card
- Submit service remains public
