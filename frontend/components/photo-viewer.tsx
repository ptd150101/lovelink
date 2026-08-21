"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type TouchEvent,
} from "react";
import { ChevronLeft, ChevronRight, ImageOff, X } from "lucide-react";
import type { Photo } from "@/lib/types";
import styles from "./photo-viewer.module.css";

type PhotoViewerProps = {
  photos: Photo[];
  displayName: string;
  activeIndex: number;
  open: boolean;
  onActiveIndexChange: (index: number) => void;
  onClose: () => void;
};

const FOCUSABLE_SELECTOR =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function PhotoViewer({
  photos,
  displayName,
  activeIndex,
  open,
  onActiveIndexChange,
  onClose,
}: PhotoViewerProps) {
  const [failedPhotoIds, setFailedPhotoIds] = useState<Set<string>>(
    () => new Set(),
  );
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const touchStartX = useRef<number | null>(null);
  const activeIndexRef = useRef(activeIndex);

  const photoCount = photos.length;

  useEffect(() => {
    activeIndexRef.current = activeIndex;
  }, [activeIndex]);

  const goPrevious = useCallback(() => {
    if (photoCount < 2) return;
    onActiveIndexChange(
      (activeIndexRef.current - 1 + photoCount) % photoCount,
    );
  }, [onActiveIndexChange, photoCount]);

  const goNext = useCallback(() => {
    if (photoCount < 2) return;
    onActiveIndexChange((activeIndexRef.current + 1) % photoCount);
  }, [onActiveIndexChange, photoCount]);

  const goTo = useCallback(
    (index: number) => {
      if (!photoCount) return;
      onActiveIndexChange(Math.min(Math.max(index, 0), photoCount - 1));
    },
    [onActiveIndexChange, photoCount],
  );

  useEffect(() => {
    if (!open || !photoCount) return;

    returnFocusRef.current =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    const previousBodyOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const focusTimer = window.setTimeout(() => closeButtonRef.current?.focus(), 0);

    function handleKeyDown(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        goPrevious();
        return;
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        goNext();
        return;
      }
      if (event.key !== "Tab") return;

      const focusable = Array.from(
        dialogRef.current?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR) ?? [],
      ).filter((element) => !element.hasAttribute("disabled"));
      if (!focusable.length) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      window.clearTimeout(focusTimer);
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousBodyOverflow;
      returnFocusRef.current?.focus();
    };
  }, [goNext, goPrevious, onClose, open, photoCount]);

  useEffect(() => {
    if (!open || photoCount < 2) return;
    const previousIndex = (activeIndex - 1 + photoCount) % photoCount;
    const nextIndex = (activeIndex + 1) % photoCount;
    const previousImage = new Image();
    const nextImage = new Image();
    previousImage.src = photos[previousIndex].public_url;
    nextImage.src = photos[nextIndex].public_url;
  }, [activeIndex, open, photoCount, photos]);

  if (!open || photoCount === 0) return null;

  const activePhoto = photos[activeIndex];

  function markFailed(photoId: string) {
    setFailedPhotoIds((current) => {
      const next = new Set(current);
      next.add(photoId);
      return next;
    });
  }

  function handleTouchStart(event: TouchEvent<HTMLDivElement>) {
    touchStartX.current = event.changedTouches[0]?.clientX ?? null;
  }

  function handleTouchEnd(event: TouchEvent<HTMLDivElement>) {
    const start = touchStartX.current;
    touchStartX.current = null;
    if (start === null) return;
    const end = event.changedTouches[0]?.clientX ?? start;
    const delta = end - start;
    if (Math.abs(delta) < 50) return;
    if (delta > 0) goPrevious();
    else goNext();
  }

  function stopKeyboardPropagation(event: ReactKeyboardEvent) {
    if (event.key === "Enter" || event.key === " ") event.stopPropagation();
  }

  return (
    <div
      ref={dialogRef}
      className={styles.viewer}
      role="dialog"
      aria-modal="true"
      aria-label={`Xem ảnh của ${displayName}`}
      data-testid="photo-viewer"
    >
      <div className={styles.topBar}>
        <div className={styles.counter} aria-live="polite">
          {activeIndex + 1} / {photoCount}
        </div>
        <button
          ref={closeButtonRef}
          type="button"
          className={styles.iconButton}
          onClick={onClose}
          aria-label="Đóng trình xem ảnh"
        >
          <X aria-hidden="true" />
        </button>
      </div>

      <div className={styles.stage}>
        <button
          type="button"
          className={`${styles.navButton} ${styles.previousButton}`}
          onClick={goPrevious}
          disabled={photoCount < 2}
          aria-label="Ảnh trước"
        >
          <ChevronLeft aria-hidden="true" />
        </button>

        <div
          className={styles.mediaFrame}
          onClick={(event) => {
            if (event.target === event.currentTarget) onClose();
          }}
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
          {failedPhotoIds.has(activePhoto.id) ? (
            <div className={styles.imageError} role="status">
              <ImageOff aria-hidden="true" />
              <span>Không thể tải ảnh này.</span>
            </div>
          ) : (
            <img
              className={styles.fullImage}
              src={activePhoto.public_url}
              alt={`Ảnh ${activeIndex + 1} của ${displayName}`}
              decoding="async"
              data-testid="photo-viewer-image"
              onError={() => markFailed(activePhoto.id)}
            />
          )}
        </div>

        <button
          type="button"
          className={`${styles.navButton} ${styles.nextButton}`}
          onClick={goNext}
          disabled={photoCount < 2}
          aria-label="Ảnh tiếp theo"
        >
          <ChevronRight aria-hidden="true" />
        </button>
      </div>

      {photoCount > 1 && (
        <div className={styles.thumbnailRail} aria-label="Danh sách ảnh">
          {photos.map((photo, index) => (
            <button
              key={photo.id}
              type="button"
              className={`${styles.viewerThumbnail} ${
                index === activeIndex ? styles.activeThumbnail : ""
              }`}
              onClick={() => goTo(index)}
              onKeyDown={stopKeyboardPropagation}
              aria-label={`Xem ảnh ${index + 1}`}
              aria-current={index === activeIndex ? "true" : undefined}
            >
              {failedPhotoIds.has(photo.id) ? (
                <span className={styles.thumbnailError}>
                  <ImageOff aria-hidden="true" />
                </span>
              ) : (
                <img
                  src={photo.thumbnail_url || photo.public_url}
                  alt=""
                  width={112}
                  height={112}
                  loading="lazy"
                  decoding="async"
                  onError={() => markFailed(photo.id)}
                />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
