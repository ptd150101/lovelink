"use client";

import { useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { SettingsNav } from "@/components/settings-nav";
import { api } from "@/lib/api";
import { Alert, Button, Card, Field, Input, Status } from "@/components/ui";
import { Dialog } from "@/components/dialog";

export default function Account() {
  const { user } = useAuth();
  const [password, setPassword] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<"status" | "error">("status");
  const [showDeletion, setShowDeletion] = useState(false);

  async function changeEmail(event: React.FormEvent) {
    event.preventDefault();
    try {
      const response = await api<{ detail: string }>("/auth/email/change", {
        method: "POST",
        body: JSON.stringify({ new_email: newEmail, password }),
      });
      setMessageTone("status");
      setMessage(response.detail);
      location.href = "/auth/login";
    } catch (caught: any) {
      setMessageTone("error");
      setMessage(caught.message);
    }
  }

  async function remove() {
    try {
      const response = await api<{ detail: string }>(
        "/auth/deletion-request",
        {
          method: "POST",
          body: JSON.stringify({ password }),
        },
      );
      setMessageTone("status");
      setMessage(response.detail);
      location.href = "/";
    } catch (caught: any) {
      setShowDeletion(false);
      setMessageTone("error");
      setMessage(caught.message);
    }
  }

  return (
    <div className="page narrow">
      <h1>Cài đặt</h1>
      <SettingsNav />
      <Card>
        <h2>Thông tin tài khoản</h2>
        <dl className="detail-list">
          <div>
            <dt>Email</dt>
            <dd>{user?.email}</dd>
          </div>
          <div>
            <dt>Trạng thái</dt>
            <dd>{user?.status}</dd>
          </div>
          <div>
            <dt>Xác minh email</dt>
            <dd>{user?.is_email_verified ? "Đã xác minh" : "Chưa xác minh"}</dd>
          </div>
        </dl>
      </Card>
      <Card>
        <h2>Đổi email</h2>
        <form className="form-stack" onSubmit={changeEmail}>
          <Field label="Email mới">
            <Input
              type="email"
              required
              value={newEmail}
              onChange={(event) => setNewEmail(event.target.value)}
            />
          </Field>
          <Field label="Mật khẩu hiện tại">
            <Input
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </Field>
          <Button>Đổi email và gửi xác minh</Button>
        </form>
      </Card>
      <Card className="danger-zone">
        <h2>Xóa tài khoản</h2>
        <p>Hồ sơ được ẩn ngay. Đăng nhập lại trong thời gian chờ sẽ hủy việc xóa.</p>
        <Field label="Nhập mật khẩu để xác nhận">
          <Input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </Field>
        <Button variant="danger" onClick={() => setShowDeletion(true)}>
          Yêu cầu xóa tài khoản
        </Button>
        {message &&
          (messageTone === "error" ? (
            <Alert>{message}</Alert>
          ) : (
            <Status className="success-text">{message}</Status>
          ))}
      </Card>
      {showDeletion && (
        <Dialog
          title="Yêu cầu xóa tài khoản?"
          onClose={() => setShowDeletion(false)}
        >
          <p>
            Hồ sơ sẽ bị ẩn ngay và tài khoản được xóa sau thời gian chờ.
          </p>
          <div className="form-actions">
            <Button variant="secondary" onClick={() => setShowDeletion(false)}>
              Hủy
            </Button>
            <Button variant="danger" onClick={() => void remove()}>
              Tiếp tục
            </Button>
          </div>
        </Dialog>
      )}
    </div>
  );
}
