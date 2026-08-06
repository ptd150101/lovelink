"use client";

import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useState, Suspense } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import { AuthFormShell } from "@/components/auth-form-shell";
import { Alert, Button, Field, Input } from "@/components/ui";

function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { refresh } = useAuth();
  const router = useRouter();
  const query = useSearchParams();

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password, remember }),
      });
      await refresh();
      router.push(query.get("next") || "/discover");
    } catch (caught: any) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthFormShell
      title="Chào mừng trở lại"
      subtitle="Đăng nhập để tiếp tục kết nối."
      footer={
        <>
          Chưa có tài khoản? <Link href="/auth/register">Đăng ký ngay</Link>
        </>
      }
    >
      <form onSubmit={submit} className="form-stack">
        <Field label="Email">
          <Input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            autoComplete="email"
          />
        </Field>
        <Field label="Mật khẩu">
          <Input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            autoComplete="current-password"
          />
        </Field>
        <div className="row-between">
          <label className="check">
            <input
              type="checkbox"
              checked={remember}
              onChange={(event) => setRemember(event.target.checked)}
            />{" "}
            Ghi nhớ
          </label>
          <Link href="/auth/forgot-password">Quên mật khẩu?</Link>
        </div>
        {error && <Alert>{error}</Alert>}
        <Button disabled={busy}>
          {busy ? "Đang đăng nhập…" : "Đăng nhập"}
        </Button>
      </form>
    </AuthFormShell>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<AuthFormShell title="Đăng nhập" subtitle="Chào mừng quay lại."><p>Vui lòng đợi…</p></AuthFormShell>}>
      <LoginForm />
    </Suspense>
  );
}
