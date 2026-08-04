"use client";

import { useEffect, useState } from "react";
import { BadgeCheck, Phone } from "lucide-react";
import { SettingsNav } from "@/components/settings-nav";
import { useAuth } from "@/components/auth-provider";
import { api } from "@/lib/api";
import { Button, Card, Field, Input } from "@/components/ui";
import { formatDate } from "@/lib/utils";

export default function Security() {
  const { user, refresh } = useAuth();
  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
  });
  const [sessions, setSessions] = useState<any[]>([]);
  const [passwordMessage, setPasswordMessage] = useState("");
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [phoneMessage, setPhoneMessage] = useState("");
  const [phoneBusy, setPhoneBusy] = useState(false);

  async function loadSessions() {
    setSessions(await api("/auth/sessions"));
  }

  useEffect(() => {
    void loadSessions();
  }, []);

  useEffect(() => {
    if (user?.phone) setPhone(user.phone);
  }, [user?.phone]);

  async function changePassword(event: React.FormEvent) {
    event.preventDefault();
    try {
      await api("/auth/password/change", {
        method: "POST",
        body: JSON.stringify(passwordData),
      });
      setPasswordMessage("Đã đổi mật khẩu.");
      setPasswordData({ current_password: "", new_password: "" });
    } catch (caught: any) {
      setPasswordMessage(caught.message);
    }
  }

  async function sendOtp() {
    setPhoneBusy(true);
    setPhoneMessage("");
    try {
      const response = await api<any>("/auth/phone/send", {
        method: "POST",
        body: JSON.stringify({ phone }),
      });
      setOtpSent(true);
      setCode("");
      setPhoneMessage(
        `${response.detail} Mã có hiệu lực trong ${Math.ceil(
          response.expires_in / 60,
        )} phút.`,
      );
    } catch (caught: any) {
      setPhoneMessage(caught.message);
    } finally {
      setPhoneBusy(false);
    }
  }

  async function verifyOtp(event: React.FormEvent) {
    event.preventDefault();
    setPhoneBusy(true);
    setPhoneMessage("");
    try {
      await api("/auth/phone/verify", {
        method: "POST",
        body: JSON.stringify({ phone, code }),
      });
      await refresh();
      setOtpSent(false);
      setCode("");
      setPhoneMessage("Xác minh số điện thoại thành công.");
    } catch (caught: any) {
      setPhoneMessage(caught.message);
    } finally {
      setPhoneBusy(false);
    }
  }

  return (
    <div className="page narrow">
      <h1>Cài đặt</h1>
      <SettingsNav />

      <Card>
        <div className="row-between">
          <div>
            <h2>Xác minh số điện thoại</h2>
            <p className="muted">
              Số điện thoại không được công khai. LoveLink chỉ hiển thị trạng
              thái đã xác minh.
            </p>
          </div>
          {user?.is_phone_verified && (
            <span className="badge badge-success phone-status-badge">
              <BadgeCheck size={16} /> Đã xác minh
            </span>
          )}
        </div>
        <form onSubmit={verifyOtp} className="form-stack">
          <Field label="Số điện thoại">
            <Input
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              placeholder="+84901234567"
              value={phone}
              onChange={(event) => {
                setPhone(event.target.value);
                if (event.target.value !== user?.phone) setOtpSent(false);
              }}
            />
          </Field>
          <div className="form-actions">
            <Button
              type="button"
              variant="secondary"
              disabled={phoneBusy || !phone.trim()}
              onClick={() => void sendOtp()}
            >
              <Phone size={17} />
              {user?.is_phone_verified && phone === user.phone
                ? "Gửi lại OTP"
                : "Gửi mã OTP"}
            </Button>
          </div>
          {otpSent && (
            <div className="otp-row">
              <Field label="Mã OTP 6 chữ số">
                <Input
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={6}
                  pattern="[0-9]{6}"
                  value={code}
                  onChange={(event) =>
                    setCode(event.target.value.replace(/\D/g, "").slice(0, 6))
                  }
                />
              </Field>
              <Button disabled={phoneBusy || code.length !== 6}>
                Xác minh
              </Button>
            </div>
          )}
          {phoneMessage && <p>{phoneMessage}</p>}
        </form>
      </Card>

      <Card>
        <h2>Đổi mật khẩu</h2>
        <form onSubmit={changePassword} className="form-stack">
          <Field label="Mật khẩu hiện tại">
            <Input
              type="password"
              value={passwordData.current_password}
              onChange={(event) =>
                setPasswordData({
                  ...passwordData,
                  current_password: event.target.value,
                })
              }
            />
          </Field>
          <Field label="Mật khẩu mới">
            <Input
              type="password"
              minLength={10}
              value={passwordData.new_password}
              onChange={(event) =>
                setPasswordData({
                  ...passwordData,
                  new_password: event.target.value,
                })
              }
            />
          </Field>
          <Button>Đổi mật khẩu</Button>
          {passwordMessage && <p>{passwordMessage}</p>}
        </form>
      </Card>

      <Card>
        <h2>Phiên đăng nhập</h2>
        <div className="session-list">
          {sessions.map((session) => (
            <div key={session.id}>
              <div>
                <b>{session.current ? "Thiết bị hiện tại" : "Thiết bị khác"}</b>
                <p>{session.user_agent || "Không rõ thiết bị"}</p>
                <small>
                  {session.ip_address} · {formatDate(session.last_seen_at)}
                </small>
              </div>
              {!session.current && (
                <Button
                  variant="secondary"
                  onClick={async () => {
                    await api(`/auth/sessions/${session.id}`, {
                      method: "DELETE",
                    });
                    await loadSessions();
                  }}
                >
                  Đăng xuất
                </Button>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
