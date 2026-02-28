# CareerTrojan Email Microservice

Node.js email service providing unified email handling via:

- **Klaviyo** — Marketing campaigns, user engagement flows
- **SendGrid** — Transactional email, backup provider
- **Zendesk** — Support ticket creation and management

## Features

### Token-Based Email Responses
- One-click feedback links in emails (👍/👎)
- Secure unsubscribe handling
- Survey response collection

### Mentor-User Communication
- Mentor introduction emails
- Session reminders to both parties
- Feedback request post-session
- Document sharing notifications
- Issue escalation to support

### Webhook Handlers
- SendGrid event tracking (delivery, opens, clicks, bounces)
- Klaviyo flow events
- Zendesk ticket updates

## API Endpoints

| Route | Description |
|-------|-------------|
| `GET /health` | Health check with provider status |
| `POST /api/email/klaviyo/profile` | Create/update Klaviyo profile |
| `POST /api/email/klaviyo/event` | Track custom event |
| `POST /api/email/sendgrid/send` | Send transactional email |
| `POST /api/email/sendgrid/template` | Send template email |
| `POST /api/email/zendesk/tickets` | Create support ticket |
| `POST /api/email/token/create` | Generate response tokens |
| `GET /api/email/token/respond/:token` | Handle token response |
| `POST /api/email/mentor/intro` | Send mentor introduction |
| `POST /api/email/mentor/session-reminder` | Send session reminder |
| `POST /api/email/mentor/feedback-request` | Request session feedback |
| `POST /api/webhooks/sendgrid` | SendGrid webhook receiver |
| `POST /api/webhooks/klaviyo` | Klaviyo webhook receiver |
| `POST /api/webhooks/zendesk` | Zendesk webhook receiver |

## Configuration

Copy `.env.example` to `.env` and set:

```env
KLAVIYO_API_KEY=your-klaviyo-private-key
SENDGRID_API_KEY=your-sendgrid-api-key
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_EMAIL=admin@company.com
ZENDESK_API_TOKEN=your-zendesk-token
EMAIL_TOKEN_SECRET=strong-random-secret
```

## Development

```bash
# Install dependencies
npm install

# Run with hot reload
npm run dev

# Run tests
npm test
```

## Docker

```bash
# Build
docker build -t careertrojan-email-service .

# Run
docker run -p 3050:3050 --env-file .env careertrojan-email-service
```

## Port

- Development: `3050`
- Docker Compose: `8650` (mapped to internal 3050)
