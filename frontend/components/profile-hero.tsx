"use client";

import type { RefObject } from "react";
import { ProfileGallery } from "@/components/profile-gallery";
import { ProfileSummary } from "@/components/profile-summary";
import type { Photo, Profile } from "@/lib/types";

type ProfileHeroProps = {
  profile: Profile;
  photos: Photo[];
  heroClassName: string;
  summaryClassName?: string;
  introTriggerRef: RefObject<HTMLButtonElement | null>;
  onPhotoOpen: (index: number) => void;
  onOpenIntro: () => void;
  onOpenBlock: () => void;
  onOpenReport: () => void;
};

export function ProfileHero({
  profile,
  photos,
  heroClassName,
  summaryClassName,
  introTriggerRef,
  onPhotoOpen,
  onOpenIntro,
  onOpenBlock,
  onOpenReport,
}: ProfileHeroProps) {
  return (
    <div className={heroClassName} data-testid="profile-detail-hero">
      <ProfileGallery
        photos={photos}
        displayName={profile.display_name}
        onPhotoOpen={onPhotoOpen}
      />
      <ProfileSummary
        profile={profile}
        introTriggerRef={introTriggerRef}
        onOpenIntro={onOpenIntro}
        onOpenBlock={onOpenBlock}
        onOpenReport={onOpenReport}
        className={summaryClassName}
      />
    </div>
  );
}
