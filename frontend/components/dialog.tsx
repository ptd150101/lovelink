"use client";

import { ReactNode, RefObject, useEffect, useId, useRef } from "react";
import { cn } from "@/lib/utils";

const FOCUSABLE = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled]):not([type='hidden'])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

let scrollLocks = 0;
let previousOverflow = "";

function lockScroll() {
  if (scrollLocks === 0) {
    previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
  }
  scrollLocks += 1;
}

function unlockScroll() {
  scrollLocks = Math.max(0, scrollLocks - 1);
  if (scrollLocks === 0) document.body.style.overflow = previousOverflow;
}

function focusableElements(container: HTMLElement) {
  return Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
    (element) => element.getClientRects().length > 0,
  );
}

export function Dialog({
  title,
  children,
  onClose,
  leading,
  initialFocusRef,
  returnFocusRef,
  overlayClassName = "modal-backdrop",
  contentClassName = "modal-card",
}: {
  title: ReactNode;
  children: ReactNode;
  onClose: () => void;
  leading?: ReactNode;
  initialFocusRef?: RefObject<HTMLElement | null>;
  returnFocusRef?: RefObject<HTMLElement | null>;
  overlayClassName?: string;
  contentClassName?: string;
}) {
  const titleId = useId();
  const contentRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    triggerRef.current =
      returnFocusRef?.current ||
      (document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null);
    lockScroll();

    const frame = requestAnimationFrame(() => {
      const content = contentRef.current;
      if (!content) return;
      const target =
        initialFocusRef?.current || focusableElements(content)[0] || content;
      target.focus({ preventScroll: true });
    });

    return () => {
      cancelAnimationFrame(frame);
      unlockScroll();
      const trigger = triggerRef.current;
      if (trigger?.isConnected) {
        requestAnimationFrame(() => {
          if (trigger.isConnected) trigger.focus({ preventScroll: true });
        });
      }
    };
  }, [initialFocusRef, returnFocusRef]);

  function handleKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      onClose();
      return;
    }
    if (event.key !== "Tab" || !contentRef.current) return;

    const focusable = focusableElements(contentRef.current);
    if (!focusable.length) {
      event.preventDefault();
      contentRef.current.focus();
      return;
    }

    const first = focusable[0];
    const last = focusable.at(-1)!;
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return (
    <div className={overlayClassName}>
      <div
        ref={contentRef}
        className={cn("dialog-surface", contentClassName)}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onKeyDown={handleKeyDown}
      >
        {leading}
        <h2 id={titleId}>{title}</h2>
        {children}
      </div>
    </div>
  );
}
