"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { AuthFormShell } from "@/components/auth-form-shell";
import { Alert, Button, Field, Input, Status } from "@/components/ui";

export default function Register() {
  const [data, setData] = useState({
    email: "",
    password: "",
    password_confirm: "",
    birth_date: "",
    accept_terms: false,
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const set = (key: string, value: any) =>
    setData((current) => ({ ...current, [key]: value }));

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setFieldErrors({});
    try {
      await api("/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
      });
      setMessage("Tài khoản đã được tạo. Hãy kiểm tra email để xác minh.");
    } catch (caught: any) {
      const errors = caught.data as Record<string, string[] | string> | undefined;
      if (errors) {
        setFieldErrors(
          Object.fromEntries(
            Object.entries(errors).map(([key, value]) => [
              key,
              Array.isArray(value) ? value[0] : String(value),
            ]),
          ),
        );
      }
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthFormShell
      title="Tạo tài khoản LoveLink"
      subtitle="Bạn phải từ 18 tuổi và đồng ý điều khoản sử dụng."
      footer={
        <>
          Đã có tài khoản? <Link href="/auth/login">Đăng nhập</Link>
        </>
      }
    >
      <form onSubmit={submit} className="form-stack">
        <Field label="Email" error={fieldErrors.email}>
          <Input
            type="email"
            value={data.email}
            onChange={(event) => set("email", event.target.value)}
            required
          />
        </Field>
        <Field
          label="Ngày sinh"
          hint="Ngày sinh đầy đủ không được công khai."
          error={fieldErrors.birth_date}
        >
          <Input
            type="date"
            value={data.birth_date}
            onChange={(event) => set("birth_date", event.target.value)}
            required
          />
        </Field>
        <Field
          label="Mật khẩu"
          hint="Tối thiểu 10 ký tự."
          error={fieldErrors.password}
        >
          <Input
            type="password"
            value={data.password}
            onChange={(event) => set("password", event.target.value)}
            required
          />
        </Field>
        <Field
          label="Nhập lại mật khẩu"
          error={fieldErrors.password_confirm}
        >
          <Input
            type="password"
            value={data.password_confirm}
            onChange={(event) => set("password_confirm", event.target.value)}
            required
          />
        </Field>
        <label className="check">
          <input
            type="checkbox"
            checked={data.accept_terms}
            onChange={(event) => set("accept_terms", event.target.checked)}
          />{" "}
          Tôi đồng ý với <Link href="/terms">điều khoản</Link> và{" "}
          <Link href="/privacy">chính sách quyền riêng tư</Link>.
        </label>
        {error && <Alert>{error}</Alert>}
        {message && <Status className="alert success-box">{message}</Status>}
        <Button disabled={busy}>{busy ? "Đang tạo…" : "Tạo tài khoản"}</Button>
      </form>
    </AuthFormShell>
  );
}
