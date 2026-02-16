/**
 * Jahiz Error Tracker - Core Client
 *
 * Lightweight client for sending error reports to the Jahiz webhook.
 * Framework-agnostic. Works in any JS/TS environment (browser, Node, Deno).
 */

// ─── Defaults (injected at build time by tsup from .env) ────────────

declare const process: { env: Record<string, string | undefined> };

const DEFAULT_WEBHOOK_URL = process.env.CLIENT_WEBHOOK_URL ?? "";
const DEFAULT_WEBHOOK_SECRET = process.env.CLIENT_WEBHOOK_SECRET ?? "";

// ─── Types ───────────────────────────────────────────────────────────

export type Severity = 'critical' | 'error' | 'warning' | 'info';

export interface JahizConfig {
  /** Webhook server URL. Defaults to the hosted Jahiz instance. */
  webhookUrl?: string;
  /** Webhook authentication secret. Defaults to the hosted Jahiz secret. */
  webhookSecret?: string;
  appName?: string;
  appVersion?: string;
  environment?: string;
  serviceName?: string;
  /** Automatically capture unhandled errors and promise rejections. Default: true */
  captureGlobal?: boolean;
  /** Collect browser/device info automatically. Default: true */
  collectDeviceInfo?: boolean;
  /** Custom tags applied to every error report */
  defaultTags?: Record<string, string>;
  /** Callback before sending — return false to skip */
  beforeSend?: (payload: ErrorPayload) => ErrorPayload | false;
}

export interface UserInfo {
  userId?: string;
  username?: string;
  email?: string;
  sessionId?: string;
  ipAddress?: string;
}

export interface ErrorContext {
  requestUrl?: string;
  requestMethod?: string;
  responseStatus?: number;
  queryParams?: Record<string, string>;
}

export interface DeviceInfo {
  hostname?: string;
  os?: string;
  osVersion?: string;
  architecture?: string;
  ipAddress?: string;
}

export interface ErrorPayload {
  error_message: string;
  severity: Severity;
  error_type?: string;
  error_code?: string;
  stacktrace?: string;
  file_name?: string;
  line_number?: number;
  function_name?: string;
  app_name?: string;
  app_version?: string;
  environment?: string;
  service_name?: string;
  component?: string;
  context?: Partial<ErrorContext>;
  user?: Partial<UserInfo>;
  device?: Partial<DeviceInfo>;
  tags?: Record<string, string>;
  metadata?: Record<string, unknown>;
  fingerprint?: string;
  timestamp?: string;
}

export interface WebhookResponse {
  success: boolean;
  message: string;
  error_id?: string;
  timestamp: string;
}

export interface ReportOptions {
  severity?: Severity;
  component?: string;
  errorCode?: string;
  context?: Partial<ErrorContext>;
  user?: Partial<UserInfo>;
  tags?: Record<string, string>;
  metadata?: Record<string, unknown>;
}

// ─── Client ──────────────────────────────────────────────────────────

class JahizTracker {
  private config: Required<Pick<JahizConfig, 'webhookUrl' | 'webhookSecret'>> & JahizConfig;
  private user: Partial<UserInfo> = {};
  private initialized = false;

  constructor(config: JahizConfig = {}) {
    this.config = {
      webhookUrl: DEFAULT_WEBHOOK_URL,
      webhookSecret: DEFAULT_WEBHOOK_SECRET,
      captureGlobal: true,
      collectDeviceInfo: true,
      ...config,
    };
  }

  /** Initialize the tracker. Call once at app startup. */
  init(): void {
    if (this.initialized) return;
    this.initialized = true;

    if (this.config.captureGlobal && typeof window !== 'undefined') {
      window.addEventListener('error', (event) => {
        this.captureError(event.error ?? event.message, {
          metadata: {
            source: 'window.onerror',
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
          },
        });
      });

      window.addEventListener('unhandledrejection', (event) => {
        const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason));
        this.captureError(error, {
          metadata: { source: 'unhandledrejection' },
        });
      });
    }
  }

  /** Set the current user context. Attached to all subsequent reports. */
  setUser(user: Partial<UserInfo>): void {
    this.user = user;
  }

  /** Clear user context (e.g. on logout). */
  clearUser(): void {
    this.user = {};
  }

  /** Capture an Error object or string message. */
  async captureError(error: Error | string, options: ReportOptions = {}): Promise<WebhookResponse | null> {
    const isError = error instanceof Error;
    const message = isError ? error.message : String(error);
    const stack = isError ? error.stack : undefined;

    const parsed = stack ? this.parseStack(stack) : {};

    const payload = this.buildPayload({
      error_message: message,
      severity: options.severity ?? 'error',
      error_type: isError ? error.name : undefined,
      error_code: options.errorCode,
      stacktrace: stack,
      file_name: parsed.fileName,
      line_number: parsed.lineNumber,
      function_name: parsed.functionName,
      component: options.component,
      context: options.context,
      user: { ...this.user, ...options.user },
      tags: { ...this.config.defaultTags, ...options.tags },
      metadata: options.metadata,
      fingerprint: this.generateFingerprint(isError ? error.name : 'Error', message, parsed.fileName),
    });

    return this.send(payload);
  }

  /** Report a custom error message (not from a thrown Error). */
  async captureMessage(message: string, options: ReportOptions = {}): Promise<WebhookResponse | null> {
    const payload = this.buildPayload({
      error_message: message,
      severity: options.severity ?? 'info',
      error_code: options.errorCode,
      component: options.component,
      context: options.context,
      user: { ...this.user, ...options.user },
      tags: { ...this.config.defaultTags, ...options.tags },
      metadata: options.metadata,
    });

    return this.send(payload);
  }

  /** Wrap an async function so errors are automatically captured. */
  wrap<T extends (...args: unknown[]) => unknown>(fn: T, options: ReportOptions = {}): T {
    const tracker = this;
    return function (this: unknown, ...args: unknown[]) {
      try {
        const result = fn.apply(this, args);
        if (result instanceof Promise) {
          return result.catch((err: Error) => {
            tracker.captureError(err, options);
            throw err;
          });
        }
        return result;
      } catch (err) {
        tracker.captureError(err as Error, options);
        throw err;
      }
    } as T;
  }

  // ─── Internal ────────────────────────────────────────────────────

  private buildPayload(partial: Partial<ErrorPayload>): ErrorPayload {
    const payload: ErrorPayload = {
      error_message: partial.error_message ?? 'Unknown error',
      severity: partial.severity ?? 'error',
      ...partial,
      app_name: partial.app_name ?? this.config.appName,
      app_version: partial.app_version ?? this.config.appVersion,
      environment: partial.environment ?? this.config.environment,
      service_name: partial.service_name ?? this.config.serviceName,
      timestamp: new Date().toISOString(),
    };

    if (this.config.collectDeviceInfo && typeof window !== 'undefined') {
      payload.device = this.collectBrowserInfo();
    }

    return payload;
  }

  private async send(payload: ErrorPayload): Promise<WebhookResponse | null> {
    if (this.config.beforeSend) {
      const result = this.config.beforeSend(payload);
      if (result === false) return null;
      payload = result;
    }

    try {
      const url = this.config.webhookUrl.replace(/\/$/, '');
      const response = await fetch(`${url}/webhook/error`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Webhook-Secret': this.config.webhookSecret,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        console.error(`[JahizTracker] Webhook returned ${response.status}:`, await response.text());
        return null;
      }

      return (await response.json()) as WebhookResponse;
    } catch (err) {
      console.error('[JahizTracker] Failed to send error report:', err);
      return null;
    }
  }

  private parseStack(stack: string): { fileName?: string; lineNumber?: number; functionName?: string } {
    // Match Chrome/Edge: "    at functionName (file:line:col)"
    // Match Firefox:     "functionName@file:line:col"
    const lines = stack.split('\n').filter((l) => l.trim());
    const frameLine = lines[1] ?? lines[0] ?? '';

    const chromeMatch = frameLine.match(/at\s+(.+?)\s+\((.+?):(\d+):\d+\)/);
    if (chromeMatch) {
      return {
        functionName: chromeMatch[1],
        fileName: chromeMatch[2],
        lineNumber: parseInt(chromeMatch[3], 10),
      };
    }

    const firefoxMatch = frameLine.match(/(.+?)@(.+?):(\d+):\d+/);
    if (firefoxMatch) {
      return {
        functionName: firefoxMatch[1],
        fileName: firefoxMatch[2],
        lineNumber: parseInt(firefoxMatch[3], 10),
      };
    }

    return {};
  }

  private collectBrowserInfo(): Partial<DeviceInfo> {
    const nav = typeof navigator !== 'undefined' ? navigator : null;
    if (!nav) return {};

    return {
      os: this.getOS(),
      osVersion: nav.userAgent,
      architecture:
        (nav as Navigator & { userAgentData?: { platform?: string } }).userAgentData?.platform ?? nav.platform,
    };
  }

  private getOS(): string {
    const ua = navigator.userAgent;
    if (ua.includes('Win')) return 'Windows';
    if (ua.includes('Mac')) return 'macOS';
    if (ua.includes('Linux')) return 'Linux';
    if (ua.includes('Android')) return 'Android';
    if (/iPhone|iPad|iPod/.test(ua)) return 'iOS';
    return 'Unknown';
  }

  private generateFingerprint(type: string, message: string, fileName?: string): string {
    const raw = `${type}:${message}:${fileName ?? ''}`;
    let hash = 0;
    for (let i = 0; i < raw.length; i++) {
      const char = raw.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash |= 0;
    }
    return Math.abs(hash).toString(16);
  }
}

// ─── Singleton ───────────────────────────────────────────────────────
// Stored on globalThis to guarantee a single instance even when bundlers
// (e.g. tsup, Vite, Webpack) duplicate this module across entry points.

const GLOBAL_KEY = '__jahiz_tracker__' as const;

/** Create and return the singleton tracker instance. */
export function createJahizTracker(config: JahizConfig = {}): JahizTracker {
  const tracker = new JahizTracker(config);
  tracker.init();
  (globalThis as Record<string, unknown>)[GLOBAL_KEY] = tracker;
  return tracker;
}

/** Get the existing tracker instance. Throws if not initialized. */
export function getJahizTracker(): JahizTracker {
  const tracker = (globalThis as Record<string, unknown>)[GLOBAL_KEY] as JahizTracker | undefined;
  if (!tracker) {
    throw new Error('[JahizTracker] Not initialized. Call createJahizTracker() first.');
  }
  return tracker;
}

export { JahizTracker };
export default JahizTracker;
