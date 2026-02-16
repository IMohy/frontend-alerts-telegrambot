# Changelog

All notable changes to this project will be documented in this file.

## [1.0.3] - 2026-02-16

### Fixed
- **Critical: Singleton instance not shared across entry points** -- `getJahizTracker()` in the React sub-package (`jahiz-tracker/react`) returned `null` because tsup duplicated the module-level `instance` variable into a separate bundle. The singleton is now stored on `globalThis`, guaranteeing a single shared instance regardless of how bundlers (Vite, Webpack, tsup) split or duplicate the code.

### Changed
- Updated repository and homepage URLs in package.json to point to correct GitHub repo

## [1.0.1] - 2026-02-16

### Added
- Full npm README documentation with API reference, examples, and integration guide

### Fixed
- Minor TypeScript import warning in `useJahizTracker` hook

## [1.0.0] - 2026-02-16

### Added
- **Webhook Server** (Python / FastAPI)
  - `POST /webhook/error` - Receive error notifications with full payload validation
  - `POST /webhook/test` - Send test notification to verify Telegram integration
  - `GET /health` - Health check with live Telegram bot connectivity status
  - HMAC-based webhook secret authentication (`X-Webhook-Secret` header)
  - Sliding window rate limiter (30 errors/minute default) to prevent Telegram spam
  - Rich HTML-formatted Telegram messages with severity indicators, stacktraces, server metrics, user context, tags, and metadata
  - Pydantic v2 models with 20+ validated fields
  - Automatic error ID generation for tracking
  - Fingerprint-based error deduplication
  - Swagger/OpenAPI docs at `/docs`
  - Docker + docker-compose + Nixpacks deployment support

- **Python Client SDK** (`client/`)
  - `report_exception()` - Auto-extracts stacktrace, file, line, function from caught exceptions
  - `report_error()` - Send custom error reports with full context
  - Auto-collects device info (hostname, OS, CPU/RAM/disk usage, IP)
  - Sync and async HTTP support

- **JavaScript/TypeScript Client SDK** (`client-js/`, npm: `jahiz-tracker`)
  - `createJahizTracker()` - Initialize with webhook URL, secret, and app context
  - `captureError()` - Report Error objects or string messages
  - `captureMessage()` - Report custom info/warning messages
  - `wrap()` - Wrap functions for automatic error capture
  - `setUser()` / `clearUser()` - Attach user context to all reports
  - `beforeSend` callback for filtering/modifying reports before sending
  - Auto-captures `window.onerror` and `unhandledrejection` events
  - Auto-collects browser/OS info
  - Fingerprint-based deduplication
  - Zero runtime dependencies, ~10 KB bundled

- **React Integration** (`jahiz-tracker/react`)
  - `<JahizErrorBoundary>` - Error Boundary with auto-reporting, custom fallback UI, and reset support
  - `useJahizTracker()` - Hook for reporting errors from functional components
  - Ships ESM + CJS + full TypeScript declarations
