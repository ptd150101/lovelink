"use client";

import { createContext, useContext, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { CallSession } from "@/lib/types";
import { useAuth } from "./auth-provider";

type Handler = (payload: any) => void;
type ContextValue = {
  on: (event: string, handler: Handler) => () => void;
  incomingCall: CallSession | null;
  clearIncoming: () => void;
};

const RealtimeContext = createContext<ContextValue | null>(null);
const TERMINAL_CALL_EVENTS = new Set([
  "call.cancelled",
  "call.declined",
  "call.ended",
]);

function validCall(value: unknown): value is CallSession {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<CallSession>;
  return Boolean(
    candidate.id &&
      candidate.status &&
      candidate.caller?.public_id &&
      candidate.caller?.display_name &&
      candidate.callee?.public_id,
  );
}

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const handlers = useRef(new Map<string, Set<Handler>>());
  const [incomingCall, setIncomingCall] = useState<CallSession | null>(null);

  useEffect(() => {
    if (!user) {
      setIncomingCall(null);
      return;
    }

    let stopped = false;
    let socket: WebSocket | undefined;
    let heartbeatTimer: ReturnType<typeof setInterval> | undefined;
    let recoveryTimer: ReturnType<typeof setInterval> | undefined;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;

    async function recoverIncomingCall() {
      try {
        const response = await api<unknown>("/calls/incoming");
        if (!stopped) setIncomingCall(validCall(response) ? response : null);
      } catch {
        // A transient recovery failure must not break the realtime connection.
      }
    }

    function dispatch(type: string, payload: any) {
      if (type === "call.incoming" && validCall(payload)) {
        setIncomingCall(payload);
      }
      if (TERMINAL_CALL_EVENTS.has(type)) {
        setIncomingCall((current) =>
          current && (!payload?.id || current.id === payload.id) ? null : current,
        );
      }
      if (type === "account.suspended") {
        setIncomingCall(null);
        socket?.close(4403, "account_suspended");
      }
      handlers.current.get(type)?.forEach((handler) => handler(payload));
    }

    function connect() {
      socket = new WebSocket(
        process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/app",
      );
      socket.onopen = () => {
        recoverIncomingCall();
        heartbeatTimer = setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: "presence.ping" }));
          }
        }, 25_000);
      };
      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          dispatch(message.type, message.payload);
        } catch {
          // Ignore malformed events rather than terminating the connection.
        }
      };
      socket.onclose = () => {
        if (heartbeatTimer) clearInterval(heartbeatTimer);
        if (!stopped) reconnectTimer = setTimeout(connect, 1_500);
      };
    }

    recoverIncomingCall();
    recoveryTimer = setInterval(recoverIncomingCall, 10_000);
    connect();

    return () => {
      stopped = true;
      if (heartbeatTimer) clearInterval(heartbeatTimer);
      if (recoveryTimer) clearInterval(recoveryTimer);
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [user]);

  return (
    <RealtimeContext.Provider
      value={{
        on: (event, handler) => {
          if (!handlers.current.has(event)) {
            handlers.current.set(event, new Set());
          }
          handlers.current.get(event)!.add(handler);
          return () => handlers.current.get(event)?.delete(handler);
        },
        incomingCall,
        clearIncoming: () => setIncomingCall(null),
      }}
    >
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime() {
  const value = useContext(RealtimeContext);
  if (!value) throw new Error("RealtimeProvider missing");
  return value;
}
