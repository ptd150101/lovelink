"use client";

import { useEffect, useRef, useState } from "react";
import { Alert, Button, Field, Input } from "./ui";
import { Dialog } from "./dialog";

const OUTPUT_WIDTH = 1200;
const OUTPUT_HEIGHT = 1500;

export function ImageCropper({
  file,
  onCancel,
  onConfirm,
}: {
  file: File;
  onCancel: () => void;
  onConfirm: (file: File) => Promise<void>;
}) {
  const [url, setUrl] = useState("");
  const [zoom, setZoom] = useState(1);
  const [positionX, setPositionX] = useState(50);
  const [positionY, setPositionY] = useState(50);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const imageRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const objectUrl = URL.createObjectURL(file);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

  async function crop() {
    const image = imageRef.current;
    if (!image || !image.naturalWidth || !image.naturalHeight) return;
    setBusy(true);
    setError("");
    try {
      const canvas = document.createElement("canvas");
      canvas.width = OUTPUT_WIDTH;
      canvas.height = OUTPUT_HEIGHT;
      const context = canvas.getContext("2d");
      if (!context) throw new Error("Trình duyệt không hỗ trợ xử lý ảnh.");

      const coverScale = Math.max(
        OUTPUT_WIDTH / image.naturalWidth,
        OUTPUT_HEIGHT / image.naturalHeight,
      );
      const scale = coverScale * zoom;
      const sourceWidth = OUTPUT_WIDTH / scale;
      const sourceHeight = OUTPUT_HEIGHT / scale;
      const maxSourceX = Math.max(0, image.naturalWidth - sourceWidth);
      const maxSourceY = Math.max(0, image.naturalHeight - sourceHeight);
      const sourceX = (positionX / 100) * maxSourceX;
      const sourceY = (positionY / 100) * maxSourceY;

      context.drawImage(
        image,
        sourceX,
        sourceY,
        sourceWidth,
        sourceHeight,
        0,
        0,
        OUTPUT_WIDTH,
        OUTPUT_HEIGHT,
      );
      const blob = await new Promise<Blob | null>((resolve) =>
        canvas.toBlob(resolve, "image/webp", 0.9),
      );
      if (!blob) throw new Error("Không thể tạo ảnh đã cắt.");
      const baseName = file.name.replace(/\.[^.]+$/, "") || "profile";
      await onConfirm(
        new File([blob], `${baseName}-4x5.webp`, {
          type: "image/webp",
          lastModified: Date.now(),
        }),
      );
    } catch (caught: any) {
      setError(caught.message || "Không thể cắt ảnh.");
      setBusy(false);
    }
  }

  return (
    <Dialog
      title="Cắt ảnh theo tỷ lệ 4:5"
      onClose={onCancel}
      overlayClassName="modal-backdrop crop-modal"
      contentClassName="modal-card crop-card"
    >
        <p className="muted">
          Điều chỉnh vị trí và độ phóng để khuôn mặt nằm rõ trong khung.
        </p>
        <div className="crop-frame">
          {url && (
            <img
              ref={imageRef}
              src={url}
              alt="Xem trước ảnh cắt"
              style={{
                objectPosition: `${positionX}% ${positionY}%`,
                transform: `scale(${zoom})`,
              }}
            />
          )}
        </div>
        <div className="crop-controls">
          <Field label="Phóng to">
            <Input
              type="range"
              min="1"
              max="3"
              step="0.05"
              value={zoom}
              onChange={(event) => setZoom(Number(event.target.value))}
            />
          </Field>
          <Field label="Dịch ngang">
            <Input
              type="range"
              min="0"
              max="100"
              value={positionX}
              onChange={(event) => setPositionX(Number(event.target.value))}
            />
          </Field>
          <Field label="Dịch dọc">
            <Input
              type="range"
              min="0"
              max="100"
              value={positionY}
              onChange={(event) => setPositionY(Number(event.target.value))}
            />
          </Field>
        </div>
        {error && <Alert className="error-inline">{error}</Alert>}
        <div className="form-actions">
          <Button variant="secondary" disabled={busy} onClick={onCancel}>
            Hủy
          </Button>
          <Button disabled={busy} onClick={() => void crop()}>
            {busy ? "Đang xử lý…" : "Dùng ảnh này"}
          </Button>
        </div>
    </Dialog>
  );
}
