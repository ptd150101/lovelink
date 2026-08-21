"use client";

import { useState } from "react";
import { ImageOff, UserRound } from "lucide-react";
import type { Photo } from "@/lib/types";
import styles from "./profile-gallery.module.css";

type ProfileGalleryProps = {
  photos: Photo[];
  displayName: string;
  onPhotoOpen: (index: number) => void;
};

export function ProfileGallery({
  photos,
  displayName,
  onPhotoOpen,
}: ProfileGalleryProps) {
  const [failedPhotoIds, setFailedPhotoIds] = useState<Set<string>>(
    () => new Set(),
  );

  function markFailed(photoId: string) {
    setFailedPhotoIds((current) => {
      const next = new Set(current);
      next.add(photoId);
      return next;
    });
  }

  if (photos.length === 0) {
    return (
      <div className={styles.gallery} aria-label="Ảnh hồ sơ">
        <div
          className={`${styles.mainPhotoButton} ${styles.emptyPhoto}`}
          data-testid="profile-photo-placeholder"
        >
          <UserRound aria-hidden="true" />
          <span>Chưa có ảnh</span>
        </div>
      </div>
    );
  }

  const mainPhoto = photos[0];
  const hasOverflow = photos.length > 5;
  const thumbnailPhotos = hasOverflow ? photos.slice(1, 4) : photos.slice(1, 5);
  const overflowPhoto = hasOverflow ? photos[4] : null;
  const overflowCount = hasOverflow ? photos.length - 4 : 0;

  return (
    <div className={styles.gallery} aria-label={`Ảnh của ${displayName}`}>
      <button
        type="button"
        className={styles.mainPhotoButton}
        onClick={() => onPhotoOpen(0)}
        aria-label={`Xem ảnh 1 của ${displayName}`}
        data-testid="profile-main-photo"
      >
        {failedPhotoIds.has(mainPhoto.id) ? (
          <span className={styles.imageFallback}>
            <ImageOff aria-hidden="true" />
            <span>Không thể tải ảnh</span>
          </span>
        ) : (
          <img
            className={styles.mainPhoto}
            src={mainPhoto.public_url}
            alt={`Ảnh 1 của ${displayName}`}
            width={1000}
            height={1000}
            loading="eager"
            fetchPriority="high"
            decoding="async"
            sizes="(max-width: 700px) calc(100vw - 56px), 420px"
            onError={() => markFailed(mainPhoto.id)}
          />
        )}
        <span className={styles.viewHint}>Xem ảnh</span>
      </button>

      {photos.length > 1 && (
        <div className={styles.thumbnails} aria-label="Ảnh khác">
          {thumbnailPhotos.map((photo, offset) => {
            const photoIndex = offset + 1;
            return (
              <button
                key={photo.id}
                type="button"
                className={styles.thumbnailButton}
                onClick={() => onPhotoOpen(photoIndex)}
                aria-label={`Xem ảnh ${photoIndex + 1} của ${displayName}`}
                data-testid="profile-thumbnail"
              >
                {failedPhotoIds.has(photo.id) ? (
                  <span className={styles.thumbnailFallback}>
                    <ImageOff aria-hidden="true" />
                  </span>
                ) : (
                  <img
                    src={photo.thumbnail_url || photo.public_url}
                    alt=""
                    width={320}
                    height={320}
                    loading="lazy"
                    decoding="async"
                    sizes="100px"
                    onError={() => markFailed(photo.id)}
                  />
                )}
              </button>
            );
          })}

          {overflowPhoto && (
            <button
              type="button"
              className={styles.thumbnailButton}
              onClick={() => onPhotoOpen(4)}
              aria-label={`Xem thêm ${overflowCount} ảnh của ${displayName}`}
              data-testid="profile-thumbnail"
            >
              {failedPhotoIds.has(overflowPhoto.id) ? (
                <span className={styles.thumbnailFallback}>
                  <ImageOff aria-hidden="true" />
                </span>
              ) : (
                <img
                  src={overflowPhoto.thumbnail_url || overflowPhoto.public_url}
                  alt=""
                  width={320}
                  height={320}
                  loading="lazy"
                  decoding="async"
                  sizes="100px"
                  onError={() => markFailed(overflowPhoto.id)}
                />
              )}
              <span
                className={styles.moreOverlay}
                data-testid="profile-more-photos"
              >
                +{overflowCount}
              </span>
            </button>
          )}
        </div>
      )}
    </div>
  );
}
