"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  BadgeCheck,
  Flag,
  HeartHandshake,
  MapPin,
  Ruler,
  ShieldCheck,
  UserX,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Profile } from "@/lib/types";
import { connectionStatusLabel, label, safeErrorMessage } from "@/lib/utils";
import {
  Badge,
  Button,
  Card,
  Field,
  Select,
  Textarea,
  Toast,
} from "@/components/ui";
import { Dialog } from "@/components/dialog";

export default function ProfileDetail() {
  const { publicId } = useParams<{ publicId: string }>();
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [intro, setIntro] = useState("");
  const [showIntro, setShowIntro] = useState(false);
  const [showBlock, setShowBlock] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [report, setReport] = useState({
    reason_code: "fake",
    description: "",
  });
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<"status" | "error">("status");
  const introTriggerRef = useRef<HTMLButtonElement>(null);
  const introRef = useRef<HTMLTextAreaElement>(null);
  const reportRef = useRef<HTMLSelectElement>(null);

  useEffect(() => {
    api<Profile>(`/profiles/${publicId}`)
      .then(setProfile)
      .catch(() => { setMessageTone("error"); setMessage(safeErrorMessage()); });
  }, [publicId]);

  async function connect() {
    try {
      await api("/connections/requests", {
        method: "POST",
        body: JSON.stringify({
          receiver_public_id: publicId,
          intro_message: intro,
        }),
      });
      setShowIntro(false);
      setMessageTone("status");
      setMessage("Đã gửi lời làm quen.");
      setProfile((current) =>
        current ? { ...current, connection_status: "pending_sent" } : current,
      );
    } catch (caught: any) {
      setMessageTone("error");
      setMessage(safeErrorMessage());
    }
  }

  async function block() {
    await api(`/users/${publicId}/block`, { method: "POST" });
    router.push("/discover");
  }

  async function submitReport() {
    try {
      await api("/reports", {
        method: "POST",
        body: JSON.stringify({
          reported_user_public_id: publicId,
          target_type: "profile",
          target_id: publicId,
          ...report,
        }),
      });
      setShowReport(false);
      setMessageTone("status");
      setMessage("Đã gửi báo cáo tới đội ngũ kiểm duyệt.");
    } catch (caught: any) {
      setMessageTone("error");
      setMessage(safeErrorMessage());
    }
  }

  if (!profile)
    return (
      <div className="page narrow">
        <p>{message || "Đang tải hồ sơ…"}</p>
      </div>
    );

  const primary =
    profile.photos.find((photo) => photo.is_primary) || profile.photos[0];

  return (
    <div className="page profile-detail-page">
      <div className="profile-hero-card">
        <div className="profile-gallery">
          {primary ? (
            <img
              className="profile-main-photo"
              src={primary.public_url}
              alt={profile.display_name}
              width={1200}
              height={1500}
              loading="eager"
              decoding="async"
              sizes="(max-width: 980px) 100vw, 480px"
            />
          ) : (
            <div className="profile-main-photo placeholder">
              {profile.display_name[0]}
            </div>
          )}
          <div className="profile-thumbs">
            {profile.photos.slice(1).map((photo) => (
              <img
                key={photo.id}
                src={photo.thumbnail_url || photo.public_url}
                alt="Ảnh hồ sơ"
                width={480}
                height={600}
                loading="lazy"
                decoding="async"
                sizes="80px"
              />
            ))}
          </div>
        </div>
        <div className="profile-summary">
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
            <MapPin size={18} />
            {profile.current_province?.name || "Chưa cập nhật"}
          </p>
          <p>
            <Ruler size={18} />
            {profile.height_cm
              ? `${profile.height_cm} cm`
              : "Chưa cập nhật"}{" "}
            ·{" "}
            {profile.occupation_text || profile.occupation_category?.name}
          </p>
          <div className="chips">
            {profile.interests.map((interest) => (
              <Badge key={interest.id || interest.name}>{interest.name}</Badge>
            ))}
          </div>
          {profile.verification_level === "identity_verified" && (
            <div className="verified-notice">
              <ShieldCheck />
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
              <BadgeCheck />
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
                !!profile.connection_status &&
                profile.connection_status !== "none"
              }
              onClick={() => setShowIntro(true)}
            >
              <HeartHandshake size={18} />
              {profile.connection_status &&
              profile.connection_status !== "none"
                ? "Đã có trạng thái kết nối"
                : "Gửi lời làm quen"}
            </Button>
            <Button variant="secondary" onClick={() => setShowBlock(true)}>
              <UserX size={18} /> Chặn
            </Button>
            <Button variant="ghost" onClick={() => setShowReport(true)}>
              <Flag size={18} /> Báo cáo
            </Button>
          </div>
        </div>
      </div>
      <div className="profile-content-grid">
        <Card>
          <h2>Giới thiệu</h2>
          <p className="prose">{profile.bio}</p>
        </Card>
        <Card>
          <h2>Mong muốn ở đối phương</h2>
          <p className="prose">
            {profile.looking_for || "Chưa chia sẻ."}
          </p>
        </Card>
        <Card>
          <h2>Thông tin cơ bản</h2>
          <dl className="detail-list">
            <div>
              <dt>Quê quán</dt>
              <dd>{profile.hometown_province?.name || "Riêng tư"}</dd>
            </div>
            <div>
              <dt>Học vấn</dt>
              <dd>{label(profile.education_level)}</dd>
            </div>
            <div>
              <dt>Thu nhập</dt>
              <dd>{label(profile.income_band)}</dd>
            </div>
            <div>
              <dt>Mục tiêu</dt>
              <dd>{label(profile.relationship_goal)}</dd>
            </div>
            <div>
              <dt>Tình trạng</dt>
              <dd>{label(profile.relationship_status)}</dd>
            </div>
          </dl>
        </Card>
        <Card>
          <h2>Lối sống</h2>
          <dl className="detail-list">
            <div>
              <dt>Hút thuốc</dt>
              <dd>{label(profile.smoking_status)}</dd>
            </div>
            <div>
              <dt>Uống rượu</dt>
              <dd>{label(profile.drinking_status)}</dd>
            </div>
            <div>
              <dt>Con cái</dt>
              <dd>{label(profile.children_status)}</dd>
            </div>
            <div>
              <dt>Kế hoạch sinh con</dt>
              <dd>{label(profile.children_plan)}</dd>
            </div>
            <div>
              <dt>Tôn giáo</dt>
              <dd>{profile.religion || "Chưa chia sẻ"}</dd>
            </div>
          </dl>
        </Card>
      </div>
      {showIntro && (
        <Dialog
          title={`Gửi lời làm quen tới ${profile.display_name}`}
          onClose={() => setShowIntro(false)}
          initialFocusRef={introRef}
          returnFocusRef={introTriggerRef}
        >
          <Field label="Lời nhắn" hint={`${intro.length}/300 ký tự`}>
            <Textarea
              ref={introRef}
              maxLength={300}
              rows={5}
              value={intro}
              onChange={(event) => setIntro(event.target.value)}
              placeholder="Giới thiệu ngắn gọn và lịch sự…"
            />
          </Field>
          <div className="form-actions">
            <Button variant="secondary" onClick={() => setShowIntro(false)}>
              Hủy
            </Button>
            <Button disabled={!intro.trim()} onClick={() => void connect()}>
              Gửi
            </Button>
          </div>
        </Dialog>
      )}
      {showBlock && (
        <Dialog title="Chặn người này?" onClose={() => setShowBlock(false)}>
          <p>
            Hai bạn sẽ không còn nhìn thấy hoặc liên hệ với nhau.
          </p>
          <div className="form-actions">
            <Button variant="secondary" onClick={() => setShowBlock(false)}>
              Hủy
            </Button>
            <Button variant="danger" onClick={() => void block()}>
              Chặn
            </Button>
          </div>
        </Dialog>
      )}
      {showReport && (
        <Dialog
          title="Báo cáo hồ sơ"
          onClose={() => setShowReport(false)}
          initialFocusRef={reportRef}
        >
          <Field label="Lý do">
            <Select
              ref={reportRef}
              value={report.reason_code}
              onChange={(event) =>
                setReport({ ...report, reason_code: event.target.value })
              }
            >
              <option value="fake">Hồ sơ giả mạo</option>
              <option value="scam">Lừa đảo</option>
              <option value="harassment">Quấy rối</option>
              <option value="sexual">Nội dung không phù hợp</option>
              <option value="threat">Đe dọa</option>
              <option value="spam">Spam</option>
              <option value="underage">Có dấu hiệu chưa đủ tuổi</option>
              <option value="other">Khác</option>
            </Select>
          </Field>
          <Field label="Mô tả">
            <Textarea
              rows={4}
              maxLength={2000}
              value={report.description}
              onChange={(event) =>
                setReport({ ...report, description: event.target.value })
              }
            />
          </Field>
          <div className="form-actions">
            <Button variant="secondary" onClick={() => setShowReport(false)}>
              Hủy
            </Button>
            <Button variant="danger" onClick={() => void submitReport()}>
              Gửi báo cáo
            </Button>
          </div>
        </Dialog>
      )}
      {message && (
        <Toast
          tone={messageTone}
          onDismiss={() => setMessage("")}
        >
          {message}
        </Toast>
      )}
    </div>
  );
}
