"use client";

import type { RefObject } from "react";
import {
  BadgeCheck,
  Flag,
  HeartHandshake,
  MapPin,
  Ruler,
  ShieldCheck,
  UserX,
} from "lucide-react";
import { Badge, Button } from "@/components/ui";
import type { Profile } from "@/lib/types";

type ProfileSummaryProps = {
  profile: Profile;
  introTriggerRef: RefObject<HTMLButtonElement | null>;
  onOpenIntro: () => void;
  onOpenBlock: () => void;
  onOpenReport: () => void;
  className?: string;
};

export function ProfileSummary({
  profile,
  introTriggerRef,
  onOpenIntro,
  onOpenBlock,
  onOpenReport,
  className,
}: ProfileSummaryProps) {
  const occupation =
    profile.occupation_text ||
    profile.occupation_category?.name ||
    "Chưa cập nhật";
  const height = profile.height_cm ? `${profile.height_cm} cm` : "Chưa cập nhật";

  return (
    <div className={`profile-summary${className ? ` ${className}` : ""}`}>
      <span className="eyebrow">Hồ sơ thành viên</span>
      <h1>
        {profile.display_name}, {profile.age}{" "}
        {profile.verification_level === "identity_verified" && (
          <ShieldCheck
            className="verified-icon"
            aria-label="Danh tính đã xác minh"
          />
        )}
        {profile.is_phone_verified && (
          <BadgeCheck
            className="phone-verified-icon"
            aria-label="Số điện thoại đã xác minh"
          />
        )}
      </h1>
      <p>
        <MapPin size={18} aria-hidden="true" />
        {profile.current_province?.name || "Chưa cập nhật"}
      </p>
      <p>
        <Ruler size={18} aria-hidden="true" />
        {height} · {occupation}
      </p>
      <div className="chips">
        {profile.interests.map((interest) => (
          <Badge key={interest.id || interest.name}>{interest.name}</Badge>
        ))}
      </div>
      {profile.verification_level === "identity_verified" && (
        <div className="verified-notice">
          <ShieldCheck aria-hidden="true" />
          <div>
            <b>Danh tính đã xác minh</b>
            <small>
              Đã được reviewer đối chiếu tại thời điểm kiểm duyệt. Đây không
              phải bảo đảm về hành vi.
            </small>
          </div>
        </div>
      )}
      {profile.is_phone_verified && (
        <div className="phone-verified-notice">
          <BadgeCheck aria-hidden="true" />
          <div>
            <b>Số điện thoại đã xác minh</b>
            <small>Số điện thoại được giữ riêng tư và không hiển thị.</small>
          </div>
        </div>
      )}
      <div className="profile-actions">
        <Button
          ref={introTriggerRef}
          disabled={
            !!profile.connection_status && profile.connection_status !== "none"
          }
          onClick={onOpenIntro}
        >
          <HeartHandshake size={18} aria-hidden="true" />
          {profile.connection_status && profile.connection_status !== "none"
            ? "Đã có trạng thái kết nối"
            : "Gửi lời làm quen"}
        </Button>
        <Button variant="secondary" onClick={onOpenBlock}>
          <UserX size={18} aria-hidden="true" /> Chặn
        </Button>
        <Button variant="ghost" onClick={onOpenReport}>
          <Flag size={18} aria-hidden="true" /> Báo cáo
        </Button>
      </div>
    </div>
  );
}
