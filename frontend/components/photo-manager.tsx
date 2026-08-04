"use client";

import { useState } from "react";
import {
  GripVertical,
  ImagePlus,
  MoveLeft,
  MoveRight,
  Star,
  Trash2,
} from "lucide-react";
import type { Photo } from "@/lib/types";
import { ImageCropper } from "./image-cropper";

export function PhotoManager({
  photos,
  onUpload,
  onRemove,
  onPrimary,
  onReorder,
}: {
  photos: Photo[];
  onUpload: (file: File) => Promise<void>;
  onRemove: (photo: Photo) => Promise<void>;
  onPrimary: (id: string) => Promise<void>;
  onReorder: (photos: Photo[]) => Promise<void>;
}) {
  const [dragged, setDragged] = useState<string | null>(null);
  const [pendingCrop, setPendingCrop] = useState<File | null>(null);

  function move(id: string, offset: number) {
    const next = [...photos];
    const from = next.findIndex((photo) => photo.id === id);
    const to = from + offset;
    if (from < 0 || to < 0 || to >= next.length) return;
    const [photo] = next.splice(from, 1);
    next.splice(to, 0, photo);
    void onReorder(next);
  }

  function drop(targetId: string) {
    if (!dragged || dragged === targetId) return;
    const next = [...photos];
    const from = next.findIndex((photo) => photo.id === dragged);
    const to = next.findIndex((photo) => photo.id === targetId);
    if (from < 0 || to < 0) return;
    const [photo] = next.splice(from, 1);
    next.splice(to, 0, photo);
    setDragged(null);
    void onReorder(next);
  }

  return (
    <>
      <div className="photo-manager">
        {photos.map((photo, index) => (
          <div
            key={photo.id}
            className={photo.is_primary ? "photo-item primary" : "photo-item"}
            draggable
            onDragStart={() => setDragged(photo.id)}
            onDragEnd={() => setDragged(null)}
            onDragOver={(event) => event.preventDefault()}
            onDrop={() => drop(photo.id)}
          >
            <img src={photo.public_url} alt={`Ảnh hồ sơ ${index + 1}`} />
            <div className="photo-item-label">
              <GripVertical size={15} />
              {photo.is_primary ? "Ảnh đại diện" : `Ảnh ${index + 1}`}
            </div>
            <div className="photo-item-actions">
              <button
                type="button"
                title="Chuyển sang trái"
                disabled={index === 0}
                onClick={() => move(photo.id, -1)}
              >
                <MoveLeft size={16} />
              </button>
              <button
                type="button"
                title="Chuyển sang phải"
                disabled={index === photos.length - 1}
                onClick={() => move(photo.id, 1)}
              >
                <MoveRight size={16} />
              </button>
              {!photo.is_primary && (
                <button
                  type="button"
                  title="Đặt làm ảnh đại diện"
                  onClick={() => void onPrimary(photo.id)}
                >
                  <Star size={16} />
                </button>
              )}
              <button
                type="button"
                title="Xóa ảnh"
                onClick={() => void onRemove(photo)}
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
        {photos.length < 6 && (
          <label className="upload-box">
            <input
              hidden
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) setPendingCrop(file);
                event.currentTarget.value = "";
              }}
            />
            <ImagePlus />
            <span>Tải và cắt ảnh</span>
          </label>
        )}
      </div>
      {pendingCrop && (
        <ImageCropper
          file={pendingCrop}
          onCancel={() => setPendingCrop(null)}
          onConfirm={async (file) => {
            await onUpload(file);
            setPendingCrop(null);
          }}
        />
      )}
    </>
  );
}
