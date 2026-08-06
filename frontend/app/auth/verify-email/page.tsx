"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { api } from "@/lib/api";
import { AuthFormShell } from "@/components/auth-form-shell";
import { Button, Field, Input } from "@/components/ui";

function VerifyEmailForm() {
  const token = useSearchParams().get("token") || "";
  const [message, setMessage] = useState(
    token ? "Đang xác minh…" : "Nhập email để nhận lại liên kết xác minh.",
  );
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!token) return;
    api<{ detail: string }>("/auth/email/verify", {
      method: "POST",
      body: JSON.stringify({ token }),
    })
      .then((response) => setMessage(response.detail))
      .catch((error) => setMessage(error.message));
  }, [token]);

  async function resend(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const response = await api<{ detail: string }>("/auth/email/resend", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setMessage(response.detail);
    } catch (error: any) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthFormShell title="Xác minh email" subtitle={message}>
      <form className="form-stack" onSubmit={resend}>
        <Field label="Gửi lại email xác minh">
          <Input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="ban@example.com"
          />
        </Field>
        <Button disabled={busy} variant="secondary">
          {busy ? "Đang gửi…" : "Gửi lại liên kết"}
        </Button>
        <Link className="btn btn-primary full" href="/auth/login">
          Đi đến đăng nhập
        </Link>
      </form>
    </AuthFormShell>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<AuthFormShell title="Xác minh email" subtitle="Đang tải…"><p>Vui lòng đợi…</p></AuthFormShell>}>
      <VerifyEmailForm />
    </Suspense>
  );
}
