# Jahiz Error Tracker

A professional webhook service that receives error notifications from your applications and instantly delivers them to Telegram with rich formatting and full context.

## Features

- **Rich Telegram Messages** - Beautifully formatted error notifications with severity indicators, stacktraces, device info, user context, and more
- **Webhook Security** - HMAC-based secret verification on every request
- **Rate Limiting** - Sliding window rate limiter to prevent Telegram API spam
- **Full Error Context** - Captures error type, stacktrace, file/line, request info, user info, server metrics (CPU/RAM/Disk), tags, and custom metadata
- **Error Deduplication** - Fingerprint-based grouping to avoid notification storms
- **Client SDK** - Drop-in Python client that auto-collects device info and formats exceptions
- **Auto API Docs** - Interactive Swagger UI at `/docs`
- **Health Check** - `/health` endpoint with Telegram connectivity status
- **Async** - Built on FastAPI + httpx for non-blocking I/O

## Quick Start

### 1. Create a Telegram Bot

1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **bot token**

### 2. Get Your Chat ID

1. Start a chat with your bot (or add it to a group)
2. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Find the `"chat":{"id": ...}` value

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=-1001234567890
WEBHOOK_SECRET=your-secret-here
```

Generate a secure webhook secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Install & Run

```bash
pip install -r requirements.txt
python main.py
```

The server starts at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Service info |
| `GET`  | `/health` | Health check + Telegram status |
| `POST` | `/webhook/error` | Receive error notification |
| `POST` | `/webhook/test` | Send a test notification |

## Usage

### Using the Python Client SDK

```python
from client.jahiz_client import JahizClient

client = JahizClient(
    webhook_url="https://your-server.com/webhook/error",
    webhook_secret="your-secret-here",
    app_name="MyApp",
    app_version="2.1.0",
    environment="production",
    service_name="payment-service",
)

# Automatically report exceptions with full stacktrace
try:
    process_payment(order)
except Exception as e:
    client.report_exception(
        e,
        severity="critical",
        component="PaymentProcessor",
        user_id="usr_12345",
        tags={"region": "eu-west-1"},
        metadata={"order_id": "ord_67890", "amount": 149.99},
    )

# Report a custom error
client.report_error(
    message="Database connection pool exhausted",
    severity="critical",
    error_code="DB_POOL_001",
    component="DatabaseManager",
    tags={"db": "primary", "region": "us-east-1"},
    metadata={"pool_size": 50, "active_connections": 50},
)
```

### Using cURL

```bash
curl -X POST http://localhost:8000/webhook/error \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret-here" \
  -d '{
    "error_message": "NullPointerException in checkout flow",
    "severity": "critical",
    "error_type": "NullPointerException",
    "error_code": "CHK_001",
    "stacktrace": "Traceback (most recent call last):\n  File \"checkout.py\", line 42\n    process(order)\nNullPointerException: order.user is None",
    "file_name": "checkout.py",
    "line_number": 42,
    "function_name": "process_checkout",
    "app_name": "E-Commerce API",
    "app_version": "3.2.1",
    "environment": "production",
    "service_name": "checkout-service",
    "component": "CheckoutController",
    "context": {
      "request_url": "https://api.example.com/checkout",
      "request_method": "POST",
      "response_status": 500
    },
    "user": {
      "user_id": "usr_12345",
      "username": "john_doe",
      "email": "john@example.com",
      "session_id": "sess_abc123"
    },
    "device": {
      "hostname": "prod-web-03",
      "os": "Linux",
      "os_version": "Ubuntu 22.04",
      "cpu_usage": 78.5,
      "memory_usage": 91.2,
      "disk_usage": 65.0
    },
    "tags": {
      "team": "backend",
      "priority": "p0"
    },
    "metadata": {
      "order_id": "ord_67890",
      "cart_total": 299.99,
      "items_count": 5
    }
  }'
```

### Test Notification

```bash
curl -X POST http://localhost:8000/webhook/test \
  -H "X-Webhook-Secret: your-secret-here"
```

## Error Payload Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error_message` | string | Yes | The error message |
| `severity` | enum | No | `critical`, `error`, `warning`, `info` (default: `error`) |
| `error_type` | string | No | Exception class name |
| `error_code` | string | No | Application-specific error code |
| `stacktrace` | string | No | Full stack trace |
| `file_name` | string | No | File where error occurred |
| `line_number` | int | No | Line number |
| `function_name` | string | No | Function/method name |
| `app_name` | string | No | Application name |
| `app_version` | string | No | Application version |
| `environment` | string | No | e.g. production, staging |
| `service_name` | string | No | Microservice name |
| `component` | string | No | Component/module name |
| `context` | object | No | Request context (URL, method, status, headers, body) |
| `user` | object | No | User info (ID, username, email, session, IP) |
| `device` | object | No | Server info (hostname, OS, CPU%, MEM%, DISK%) |
| `tags` | object | No | Key-value tags |
| `metadata` | object | No | Any additional data |
| `fingerprint` | string | No | Unique hash for deduplication |
| `timestamp` | datetime | No | ISO 8601 (auto-generated if omitted) |

## Project Structure

```
jahiztrackingbot/
├── main.py                     # FastAPI application entry point
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
├── .gitignore
├── README.md
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings from environment
│   │   ├── rate_limiter.py     # Sliding window rate limiter
│   │   └── security.py         # Webhook secret verification
│   ├── models/
│   │   ├── __init__.py
│   │   └── error_payload.py    # Pydantic validation models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py           # Health check endpoints
│   │   └── webhook.py          # Webhook endpoints
│   └── services/
│       ├── __init__.py
│       └── telegram_service.py # Telegram message formatting & sending
└── client/
    ├── __init__.py
    └── jahiz_client.py         # Python client SDK
```

## Deployment

### Docker (optional)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Systemd

```ini
[Unit]
Description=Jahiz Error Tracker
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/jahiztrackingbot
ExecStart=/opt/jahiztrackingbot/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## License

MIT
