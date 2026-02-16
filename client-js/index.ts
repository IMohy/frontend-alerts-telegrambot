export {
  createJahizTracker,
  getJahizTracker,
  JahizTracker,
} from "./jahiz-tracker";

export type {
  JahizConfig,
  Severity,
  ErrorPayload,
  WebhookResponse,
  ReportOptions,
  UserInfo,
  ErrorContext,
  DeviceInfo,
} from "./jahiz-tracker";

export { JahizErrorBoundary, useJahizTracker } from "./react";
