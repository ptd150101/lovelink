"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, uploadToSignedUrl } from "@/lib/api";
import type { Photo, Profile } from "@/lib/types";
import { Alert, Button, Card, Status } from "./ui";
import { PhotoManager } from "./photo-manager";
import {
  BasicProfileFields,
  DetailProfileFields,
  PrivacyProfileFields,
  ProfileReview,
  ProfileTextAndInterests,
  type ReferenceData,
} from "./profile-step-fields";

const steps = ["basic", "details", "photos", "privacy", "review"] as const;
type Step = (typeof steps)[number];

const titles: Record<Step, string> = {
  basic: "Thông tin cơ bản",
  details: "Thông tin cá nhân",
  photos: "Ảnh và giới thiệu",
  privacy: "Quyền riêng tư",
  review: "Kiểm tra hồ sơ",
};

export function ProfileEditor({
  step = "basic",
  edit = false,
}: {
  step?: Step;
  edit?: boolean;
}) {
  const [profile, setProfile] = useState<any>(null);
  const [referenceData, setReferenceData] = useState<ReferenceData | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const router = useRouter();

  useEffect(() => {
    Promise.all([
      api<Profile>("/me/profile"),
      api<ReferenceData>("/reference-data"),
    ])
      .then(([loaded, reference]) => {
        setProfile({
          ...loaded,
          current_province: loaded.current_province?.code || "",
          hometown_province: loaded.hometown_province?.code || "",
          occupation_category: loaded.occupation_category?.id || "",
          interest_ids: loaded.interests
            .map((interest) => interest.id)
            .filter(Boolean),
        });
        setReferenceData(reference);
      })
      .catch((caught) => setError(caught.message));
  }, []);

  if (!profile || !referenceData) {
    return (
      <div className="page">
        <p>{error || "Đang tải hồ sơ…"}</p>
      </div>
    );
  }

  const setField = (key: string, value: any) =>
    setProfile((current: any) => ({ ...current, [key]: value }));

  function writablePayload() {
    const payload = { ...profile };
    for (const key of [
      "public_id",
      "age",
      "photos",
      "interests",
      "visibility_status",
      "completion_percent",
      "verification_level",
      "verified_at",
      "published_at",
      "presence",
    ]) {
      delete payload[key];
    }
    return payload;
  }

  async function persist() {
    return api<Profile>("/me/profile", {
      method: "PATCH",
      body: JSON.stringify(writablePayload()),
    });
  }

  async function save(next?: string) {
    setBusy(true);
    setError("");
    try {
      await persist();
      setSaved(true);
      router.push(next || "/me/profile");
    } catch (caught: any) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  async function publish() {
    setBusy(true);
    setError("");
    try {
      await persist();
      await api("/me/profile/publish", { method: "POST" });
      router.push("/discover");
    } catch (caught: any) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  async function upload(file: File) {
    setError("");
    try {
      const signed = await api<any>("/me/photos/presign", {
        method: "POST",
        body: JSON.stringify({ content_type: file.type, size: file.size }),
      });
      await uploadToSignedUrl(signed.upload_url, file, signed.headers);
      const photo = await api<Photo>("/me/photos/complete", {
        method: "POST",
        body: JSON.stringify({ object_key: signed.object_key }),
      });
      setProfile((current: any) => ({
        ...current,
        photos: [...current.photos, photo],
      }));
    } catch (caught: any) {
      setError(caught.message);
    }
  }

  async function remove(photo: Photo) {
    setError("");
    if (photo.is_primary && profile.photos.length > 1) {
      setError("Hãy chọn ảnh đại diện khác trước khi xóa ảnh này.");
      return;
    }
    try {
      await api(`/me/photos/${photo.id}`, { method: "DELETE" });
      setProfile((current: any) => ({
        ...current,
        photos: current.photos.filter((item: Photo) => item.id !== photo.id),
      }));
    } catch (caught: any) {
      setError(caught.message);
    }
  }

  async function primary(photoId: string) {
    setError("");
    try {
      await api(`/me/photos/${photoId}/primary`, { method: "POST" });
      setProfile((current: any) => ({
        ...current,
        photos: current.photos.map((photo: Photo) => ({
          ...photo,
          is_primary: photo.id === photoId,
        })),
      }));
    } catch (caught: any) {
      setError(caught.message);
    }
  }

  async function reorder(nextPhotos: Photo[]) {
    const previous = profile.photos as Photo[];
    const normalized = nextPhotos.map((photo, index) => ({
      ...photo,
      position: index,
    }));
    setProfile((current: any) => ({ ...current, photos: normalized }));
    try {
      const saved = await api<Photo[]>("/me/photos/reorder", {
        method: "PATCH",
        body: JSON.stringify({ photo_ids: normalized.map((photo) => photo.id) }),
      });
      setProfile((current: any) => ({ ...current, photos: saved }));
    } catch (caught: any) {
      setProfile((current: any) => ({ ...current, photos: previous }));
      setError(caught.message);
    }
  }

  const index = steps.indexOf(step);
  const next =
    index < steps.length - 1
      ? `/onboarding/${steps[index + 1]}`
      : "/discover";
  const shared = { profile, referenceData, setField };
  const photoSection = (
    <>
      <Card>
        <h2>Ảnh hồ sơ</h2>
        <p className="muted">
          Kéo thả để sắp xếp, dùng mũi tên trên màn hình cảm ứng và chọn rõ ảnh
          đại diện. Tối đa 6 ảnh JPG, PNG hoặc WebP.
        </p>
        <PhotoManager
          photos={profile.photos}
          onUpload={upload}
          onRemove={remove}
          onPrimary={primary}
          onReorder={reorder}
        />
      </Card>
      <ProfileTextAndInterests {...shared} />
    </>
  );

  return (
    <div className="page narrow">
      <div className="page-heading">
        <div>
          <span className="eyebrow">
            {edit ? "Chỉnh sửa hồ sơ" : `Bước ${index + 1}/5`}
          </span>
          <h1>{edit ? "Toàn bộ hồ sơ" : titles[step]}</h1>
        </div>
        <span>{profile.completion_percent || 0}% hoàn thiện</span>
      </div>

      {!edit && (
        <div className="stepper">
          {steps.map((item, itemIndex) => (
            <div key={item} className={itemIndex <= index ? "done" : ""}>
              {itemIndex + 1}
            </div>
          ))}
        </div>
      )}

      {edit ? (
        <div className="form-stack">
          <BasicProfileFields {...shared} />
          <DetailProfileFields {...shared} />
          {photoSection}
          <PrivacyProfileFields {...shared} />
        </div>
      ) : (
        <>
          {step === "basic" && <BasicProfileFields {...shared} />}
          {step === "details" && <DetailProfileFields {...shared} />}
          {step === "photos" && photoSection}
          {step === "privacy" && <PrivacyProfileFields {...shared} />}
          {step === "review" && <ProfileReview profile={profile} />}
        </>
      )}

      {error && <Alert>{error}</Alert>}
      {saved && <Status className="success-text">Đã lưu thay đổi. Bạn có thể tiếp tục chỉnh sửa bất cứ lúc nào.</Status>}
      <div className="form-actions">
        {index > 0 && !edit && (
          <Button
            variant="secondary"
            onClick={() => router.push(`/onboarding/${steps[index - 1]}`)}
          >
            Quay lại
          </Button>
        )}
        <Button
          disabled={busy}
          onClick={() =>
            step === "review" && !edit
              ? void publish()
              : void save(edit ? undefined : next)
          }
        >
          {busy
            ? "Đang lưu…"
            : step === "review" && !edit
              ? "Công khai hồ sơ"
              : edit
                ? "Lưu toàn bộ thay đổi"
                : "Lưu và tiếp tục"}
        </Button>
      </div>
    </div>
  );
}
