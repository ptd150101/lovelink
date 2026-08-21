"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Dialog } from "@/components/dialog";
import { PhotoViewer } from "@/components/photo-viewer";
import {
  AboutCard,
  BasicInfoCard,
  LifestyleCard,
  PartnerPreferenceCard,
} from "@/components/profile-detail-cards";
import { ProfileHero } from "@/components/profile-hero";
import { Button, Field, Select, Textarea, Toast } from "@/components/ui";
import { api } from "@/lib/api";
import { orderProfilePhotos } from "@/lib/profile";
import type { Profile } from "@/lib/types";
import { safeErrorMessage } from "@/lib/utils";
import styles from "./profile-detail.module.css";

export default function ProfileDetail() {
  const { publicId } = useParams<{ publicId: string }>();
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [intro, setIntro] = useState("");
  const [showIntro, setShowIntro] = useState(false);
  const [showBlock, setShowBlock] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [viewerIndex, setViewerIndex] = useState<number | null>(null);
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
      .catch(() => {
        setMessageTone("error");
        setMessage(safeErrorMessage());
      });
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
    } catch {
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
    } catch {
      setMessageTone("error");
      setMessage(safeErrorMessage());
    }
  }

  if (!profile) {
    return (
      <div className="page narrow">
        <p>{message || "Đang tải hồ sơ…"}</p>
      </div>
    );
  }

  const orderedPhotos = orderProfilePhotos(profile.photos);

  return (
    <div className="page profile-detail-page">
      <ProfileHero
        profile={profile}
        photos={orderedPhotos}
        heroClassName={styles.heroCard}
        summaryClassName={styles.summary}
        introTriggerRef={introTriggerRef}
        onPhotoOpen={setViewerIndex}
        onOpenIntro={() => setShowIntro(true)}
        onOpenBlock={() => setShowBlock(true)}
        onOpenReport={() => setShowReport(true)}
      />

      <div className={styles.contentGrid}>
        <AboutCard profile={profile} />
        <PartnerPreferenceCard profile={profile} />
        <BasicInfoCard
          profile={profile}
          detailListClassName={styles.detailList}
        />
        <LifestyleCard
          profile={profile}
          detailListClassName={styles.detailList}
        />
      </div>

      <PhotoViewer
        photos={orderedPhotos}
        displayName={profile.display_name}
        activeIndex={viewerIndex ?? 0}
        open={viewerIndex !== null}
        onActiveIndexChange={setViewerIndex}
        onClose={() => setViewerIndex(null)}
      />

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
          <p>Hai bạn sẽ không còn nhìn thấy hoặc liên hệ với nhau.</p>
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
        <Toast tone={messageTone} onDismiss={() => setMessage("")}>
          {message}
        </Toast>
      )}
    </div>
  );
}
