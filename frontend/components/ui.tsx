import {
  ButtonHTMLAttributes,
  cloneElement,
  forwardRef,
  InputHTMLAttributes,
  isValidElement,
  ReactElement,
  ReactNode,
  TextareaHTMLAttributes,
  useId,
} from "react";
import { cn } from "@/lib/utils";

export const Button = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "primary" | "secondary" | "danger" | "ghost";
  }
>(function Button({ className, variant = "primary", ...props }, ref) {
  return (
    <button
      ref={ref}
      className={cn("btn", `btn-${variant}`, className)}
      {...props}
    />
  );
});

export const Input = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement>
>(function Input({ className, ...props }, ref) {
  return <input ref={ref} className={cn("input", className)} {...props} />;
});

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(function Textarea({ className, ...props }, ref) {
  return (
    <textarea ref={ref} className={cn("input textarea", className)} {...props} />
  );
});

export const Select = forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(function Select({ className, children, ...props }, ref) {
  return (
    <select ref={ref} className={cn("input", className)} {...props}>
      {children}
    </select>
  );
});

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <section className={cn("card", className)}>{children}</section>;
}

type FieldControlProps = {
  id?: string;
  "aria-describedby"?: string;
  "aria-invalid"?: boolean | "true" | "false";
};

export function Field({
  label,
  children,
  error,
  hint,
}: {
  label: string;
  children: ReactElement<FieldControlProps>;
  error?: string;
  hint?: string;
}) {
  const generatedId = useId();
  const controlId = children.props.id || `${generatedId}-control`;
  const hintId = hint ? `${generatedId}-hint` : undefined;
  const errorId = error ? `${generatedId}-error` : undefined;
  const describedBy = [
    children.props["aria-describedby"],
    hintId,
    errorId,
  ]
    .filter(Boolean)
    .join(" ") || undefined;
  const control = isValidElement(children)
    ? cloneElement(children, {
        id: controlId,
        "aria-describedby": describedBy,
        "aria-invalid": error ? true : children.props["aria-invalid"],
      })
    : children;

  return (
    <label className="field" htmlFor={controlId}>
      <span>{label}</span>
      {control}
      {hint && <small id={hintId}>{hint}</small>}
      {error && (
        <small id={errorId} className="error">
          {error}
        </small>
      )}
    </label>
  );
}

export function Alert({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={className || "alert error-box"}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      {children}
    </div>
  );
}

export function Status({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={className}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      {children}
    </div>
  );
}

export function Toast({
  children,
  tone = "status",
  onDismiss,
}: {
  children: ReactNode;
  tone?: "status" | "error";
  onDismiss?: () => void;
}) {
  return (
    <div
      className="toast"
      role={tone === "error" ? "alert" : "status"}
      aria-live={tone === "error" ? "assertive" : "polite"}
      aria-atomic="true"
    >
      <span>{children}</span>
      {onDismiss && (
        <button
          type="button"
          className="toast-dismiss"
          onClick={onDismiss}
          aria-label="Đóng thông báo"
        >
          Đóng
        </button>
      )}
    </div>
  );
}

export function Badge({
  children,
  tone = "default",
}: {
  children: ReactNode;
  tone?: "default" | "verified" | "success" | "warning";
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function Empty({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <h3>{title}</h3>
      <p>{body}</p>
      {action}
    </div>
  );
}

export function Spinner() {
  return <span className="spinner" aria-label="Đang tải" />;
}
