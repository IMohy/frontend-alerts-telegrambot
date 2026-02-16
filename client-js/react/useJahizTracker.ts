import { useCallback, useRef } from "react";
import {
  getJahizTracker,
  type ReportOptions,
  type UserInfo,
  type WebhookResponse,
} from "../jahiz-tracker";

/**
 * React hook for reporting errors from components.
 *
 * Usage:
 *   const { captureError, captureMessage } = useJahizTracker("PaymentForm");
 *
 *   const handleSubmit = async () => {
 *     try {
 *       await processPayment();
 *     } catch (err) {
 *       captureError(err, { severity: "critical", metadata: { orderId } });
 *       showErrorToast("Payment failed");
 *     }
 *   };
 */
export function useJahizTracker(component?: string) {
  const trackerRef = useRef(getJahizTracker());

  const captureError = useCallback(
    async (
      error: Error | string,
      options: ReportOptions = {}
    ): Promise<WebhookResponse | null> => {
      return trackerRef.current.captureError(error, {
        component,
        ...options,
      });
    },
    [component]
  );

  const captureMessage = useCallback(
    async (
      message: string,
      options: ReportOptions = {}
    ): Promise<WebhookResponse | null> => {
      return trackerRef.current.captureMessage(message, {
        component,
        ...options,
      });
    },
    [component]
  );

  const setUser = useCallback(
    (user: Partial<UserInfo>) => {
      trackerRef.current.setUser(user);
    },
    []
  );

  const clearUser = useCallback(() => {
    trackerRef.current.clearUser();
  }, []);

  return { captureError, captureMessage, setUser, clearUser };
}

export default useJahizTracker;
