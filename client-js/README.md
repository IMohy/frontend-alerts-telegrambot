# jahiz-tracker

Lightweight error tracking client that sends real-time notifications to **Telegram**. Catch errors in your JavaScript/TypeScript applications and get instant, richly formatted alerts on your phone.

Zero dependencies. Works with React, Vue, Next.js, Node.js, or any JavaScript environment.

## Features

- **Automatic error capture** -- unhandled errors and promise rejections are caught globally
- **React integration** -- Error Boundary component and `useJahizTracker` hook
- **Rich context** -- stack traces, browser info, user data, custom metadata, and tags
- **Error deduplication** -- fingerprint-based grouping prevents notification storms
- **Filtering** -- `beforeSend` callback lets you drop or modify reports before they're sent
- **Tiny footprint** -- ~10 KB bundled, zero runtime dependencies
- **Full TypeScript support** -- ships ESM + CJS + type declarations

## Installation

```bash
npm install jahiz-tracker
```

## Quick Start

### 1. Initialize (once, at app startup)

```ts
import { createJahizTracker } from "jahiz-tracker";

createJahizTracker({
  webhookUrl: "https://your-jahiz-server.com",
  webhookSecret: "your-webhook-secret",
  appName: "My App",
  appVersion: "1.2.0",
  environment: "production",
});
```

That's it. All unhandled errors and unhandled promise rejections are now automatically reported to your Telegram.

### 2. Manually report errors

```ts
import { getJahizTracker } from "jahiz-tracker";

const tracker = getJahizTracker();

try {
  await riskyOperation();
} catch (err) {
  tracker.captureError(err, {
    severity: "critical",
    component: "PaymentService",
    errorCode: "PAY_001",
    metadata: { orderId: "ord_123", amount: 49.99 },
  });
}
```

### 3. Send custom messages

```ts
tracker.captureMessage("Deployment completed successfully", {
  severity: "info",
  tags: { version: "1.2.0" },
});
```

---

## React Integration

### Error Boundary

Wrap your pages or components to catch React render crashes:

```tsx
import { JahizErrorBoundary } from "jahiz-tracker/react";

function App() {
  return (
    <JahizErrorBoundary component="App">
      <Router />
    </JahizErrorBoundary>
  );
}
```

With a custom fallback:

```tsx
<JahizErrorBoundary
  component="Dashboard"
  fallback={(error, reset) => (
    <div>
      <h2>Something went wrong</h2>
      <p>{error.message}</p>
      <button onClick={reset}>Try Again</button>
    </div>
  )}
  onError={(error) => console.log("Caught:", error)}
>
  <Dashboard />
</JahizErrorBoundary>
```

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `children` | `ReactNode` | Components to wrap |
| `component` | `string` | Component name for context (e.g. `"Dashboard"`) |
| `fallback` | `ReactNode \| (error, reset) => ReactNode` | Custom error UI. Receives the error and a reset function |
| `reportOptions` | `ReportOptions` | Extra options applied to every captured error |
| `onError` | `(error, errorInfo) => void` | Callback when an error is caught |

### useJahizTracker Hook

Report errors from within functional components:

```tsx
import { useJahizTracker } from "jahiz-tracker/react";

function CheckoutForm() {
  const { captureError, captureMessage, setUser } = useJahizTracker("CheckoutForm");

  const handleSubmit = async () => {
    try {
      await submitOrder();
    } catch (err) {
      captureError(err as Error, {
        severity: "critical",
        errorCode: "CHECKOUT_FAIL",
        metadata: { cartItems: 3, total: 149.99 },
        tags: { flow: "checkout" },
      });
      toast.error("Checkout failed. We've been notified.");
    }
  };

  return <button onClick={handleSubmit}>Place Order</button>;
}
```

#### Returns

| Method | Signature | Description |
|--------|-----------|-------------|
| `captureError` | `(error: Error \| string, options?) => Promise` | Report an error |
| `captureMessage` | `(message: string, options?) => Promise` | Report a custom message |
| `setUser` | `(user: Partial<UserInfo>) => void` | Set user context |
| `clearUser` | `() => void` | Clear user context |

---

## Configuration

### `createJahizTracker(config)`

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `webhookUrl` | `string` | **required** | Your Jahiz webhook server URL |
| `webhookSecret` | `string` | **required** | Secret for authenticating with the webhook |
| `appName` | `string` | `undefined` | Application name (shown in Telegram messages) |
| `appVersion` | `string` | `undefined` | Application version |
| `environment` | `string` | `undefined` | e.g. `"production"`, `"staging"`, `"development"` |
| `serviceName` | `string` | `undefined` | Microservice name (if applicable) |
| `captureGlobal` | `boolean` | `true` | Auto-capture `window.onerror` and `unhandledrejection` |
| `collectDeviceInfo` | `boolean` | `true` | Auto-collect browser/OS info |
| `defaultTags` | `Record<string, string>` | `undefined` | Tags applied to every report |
| `beforeSend` | `(payload) => payload \| false` | `undefined` | Filter or modify payloads before sending |

---

## User Context

Attach user information to all subsequent error reports:

```ts
import { getJahizTracker } from "jahiz-tracker";

// After login
getJahizTracker().setUser({
  userId: "usr_abc123",
  username: "john_doe",
  email: "john@example.com",
  sessionId: "sess_xyz",
});

// After logout
getJahizTracker().clearUser();
```

---

## Filtering & Modifying Reports

Use `beforeSend` to drop or transform reports before they're sent:

```ts
createJahizTracker({
  webhookUrl: "https://your-server.com",
  webhookSecret: "secret",
  beforeSend: (payload) => {
    // Don't report errors in development
    if (payload.environment === "development") return false;

    // Redact sensitive data
    if (payload.metadata?.password) {
      payload.metadata.password = "[REDACTED]";
    }

    // Skip noisy errors
    if (payload.error_message.includes("ResizeObserver")) return false;

    return payload;
  },
});
```

---

## Wrapping Functions

Automatically capture errors from any function:

```ts
const tracker = getJahizTracker();

const safeFetch = tracker.wrap(
  async (url: string) => {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
  { component: "APIClient", severity: "error" }
);

// Errors thrown inside are automatically reported
const data = await safeFetch("/api/users");
```

---

## Full Example (React + Vite)

**`src/main.tsx`**

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { createJahizTracker } from "jahiz-tracker";

createJahizTracker({
  webhookUrl: import.meta.env.VITE_JAHIZ_URL,
  webhookSecret: import.meta.env.VITE_JAHIZ_SECRET,
  appName: "My React App",
  appVersion: "1.0.0",
  environment: import.meta.env.MODE,
  defaultTags: { team: "frontend" },
  beforeSend: (payload) => {
    if (import.meta.env.DEV) return false; // skip in dev
    return payload;
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

**`src/App.tsx`**

```tsx
import { JahizErrorBoundary } from "jahiz-tracker/react";
import Dashboard from "./pages/Dashboard";

export default function App() {
  return (
    <JahizErrorBoundary
      component="App"
      fallback={(error, reset) => (
        <div style={{ padding: "2rem", textAlign: "center" }}>
          <h1>Oops!</h1>
          <p>{error.message}</p>
          <button onClick={reset}>Reload</button>
        </div>
      )}
    >
      <Dashboard />
    </JahizErrorBoundary>
  );
}
```

**`src/pages/Dashboard.tsx`**

```tsx
import { useJahizTracker } from "jahiz-tracker/react";
import { useEffect } from "react";

export default function Dashboard() {
  const { captureError, captureMessage, setUser } = useJahizTracker("Dashboard");

  useEffect(() => {
    setUser({ userId: "usr_123", username: "mohy" });
  }, []);

  const loadData = async () => {
    try {
      const res = await fetch("/api/dashboard");
      if (!res.ok) throw new Error(`API error: ${res.status}`);
    } catch (err) {
      captureError(err as Error, {
        severity: "error",
        context: { requestUrl: "/api/dashboard", requestMethod: "GET" },
      });
    }
  };

  return <button onClick={loadData}>Load Data</button>;
}
```

**`.env`**

```
VITE_JAHIZ_URL=https://your-jahiz-server.com
VITE_JAHIZ_SECRET=your-webhook-secret
```

---

## Report Options

Every `captureError` and `captureMessage` call accepts these options:

| Option | Type | Description |
|--------|------|-------------|
| `severity` | `"critical" \| "error" \| "warning" \| "info"` | Error severity level |
| `component` | `string` | Component or module name |
| `errorCode` | `string` | Application-specific error code |
| `context` | `ErrorContext` | Request URL, method, status, query params |
| `user` | `UserInfo` | User ID, username, email, session, IP |
| `tags` | `Record<string, string>` | Key-value tags for categorization |
| `metadata` | `Record<string, unknown>` | Any additional data |

---

## What Gets Sent to Telegram

Each error report is formatted as a rich Telegram message with:

- Severity indicator (colored circles)
- Unique error ID
- Error message, type, and code
- File name, line number, function name
- Full stack trace
- Application info (name, version, environment, service)
- Request context (URL, method, status)
- User info (ID, username, email, session)
- Browser/OS info
- Tags and custom metadata
- Timestamp and deduplication fingerprint

---

## TypeScript

Full type definitions are included. Key types you can import:

```ts
import type {
  JahizConfig,
  Severity,
  ErrorPayload,
  WebhookResponse,
  ReportOptions,
  UserInfo,
  ErrorContext,
  DeviceInfo,
} from "jahiz-tracker";
```

---

## Backend Setup

This package is the **client SDK**. You also need the **Jahiz webhook server** running to receive reports and forward them to Telegram.

See the [server repository](https://github.com/your-username/jahiztrackingbot) for setup instructions.

---

## License

MIT
