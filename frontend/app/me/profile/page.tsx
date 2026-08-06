"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { EyeOff, PenLine, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import type { Profile } from "@/lib/types";
import { avatar, label } from "@/lib/utils";
import { Badge, Button, Card, Toast } from "@/components/ui";

export default function MyProfile() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setProfile(await api<Profile>("/me/profile"));
    } catch (caught) {
      if ((caught as { status?: number }).status === 401) {
        router.push("/auth/login?next=/me/profile");
      }
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  async function toggleVisibility() {
    setError("");
    try {
      if (profile?.visibility_status === "hidden_by_user") {
        await api("/me/profile/hide", { method: "DELETE" });
      } else {
        await api("/me/profile/hide", { method: "POST" });
      }
      await load();
    } catch (caught) {
      const data = (caught as { data?: Record<string, unknown> }).data;
      const first = data && Object.values(data)[0];
      setError(
        Array.isArray(first)
          ? String(first[0])
          : (caught as Error).message,
      );
    }
  }

  if (!profile) return <div className="page">Đang tải…</div>;
  const photo = avatar(profile);

  return (
    <div className="page narrow">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Hồ sơ của tôi</span>
          <h1>Quản lý hiển thị</h1>
        </div>
        <Link className="btn btn-primary" href="/me/profile/edit">
          <PenLine size={17} /> Chỉnh sửa
        </Link>
      </div>
      <Card className="my-profile-card">
        <div className="my-avatar">
          {photo ? (
            <img
              src={photo}
              alt=""
              width={100}
              height={100}
              loading="lazy"
              decoding="async"
            />
          ) : (
            profile.display_name?.[0]
          )}
        </div>
        <div>
          <h2>
            {profile.display_name}, {profile.age}{" "}
            {profile.verification_level === "identity_verified" && (
              <ShieldCheck className="verified-icon" />
            )}
          </h2>
          <p>
            {profile.occupation_text} · {profile.current_province?.name}
          </p>
          <div className="chips">
            {profile.interests.map((interest) => (
              <Badge key={interest.id || interest.name}>{interest.name}</Badge>
            ))}
          </div>
        </div>
        <div className="completion">
          <strong>{profile.completion_percent}%</strong>
          <span>hoàn thiện</span>
        </div>
      </Card>
      <Card>
        <div className="row-between">
          <div>
            <h2>Hiển thị trên Khám phá</h2>
            <p className="muted">
              Ẩn hồ sơ sẽ ngăn lời làm quen mới nhưng vẫn giữ các cuộc trò chuyện
              cũ.
            </p>
          </div>
          <Button
            variant={
              profile.visibility_status === "published" ? "secondary" : "primary"
            }
            onClick={() => void toggleVisibility()}
          >
            <EyeOff size={17} />
            {profile.visibility_status === "published" ? "Ẩn hồ sơ" : "Hiện hồ sơ"}
          </Button>
        </div>
      </Card>
      {error && (
        <Toast tone="error" onDismiss={() => setError("")}>
          {error}
        </Toast>
      )}
      <div className="settings-grid">
        <Link href="/verification">
          <Card>
            <h3>Xác minh danh tính</h3>
            <p>{label(profile.verification_level)}</p>
          </Card>
        </Link>
        <Link href="/settings/privacy">
          <Card>
            <h3>Quyền riêng tư</h3>
            <p>Chọn ai có thể xem thông tin.</p>
          </Card>
        </Link>
        <Link href="/settings/security">
          <Card>
            <h3>Bảo mật</h3>
            <p>Mật khẩu và phiên đăng nhập.</p>
          </Card>
        </Link>
        <Link href="/settings/blocked-users">
          <Card>
            <h3>Người đã chặn</h3>
            <p>Quản lý danh sách chặn.</p>
          </Card>
        </Link>
      </div>
    </div>
  );
}
