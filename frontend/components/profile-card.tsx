import Link from "next/link";
import { BadgeCheck, MapPin, Ruler, ShieldCheck } from "lucide-react";
import type { Profile } from "@/lib/types";
import { avatar } from "@/lib/utils";
import { Badge } from "./ui";

export function ProfileCard({ profile }: { profile: Profile }) {
  const photo = avatar(profile);
  return (
    <article className="profile-card">
      <Link href={`/profiles/${profile.public_id}`} className="photo-wrap">
        {photo ? (
          <img
            src={photo}
            alt={profile.display_name}
            width={480}
            height={600}
            loading="lazy"
            decoding="async"
            sizes="(max-width: 700px) 50vw, (max-width: 980px) 33vw, 280px"
          />
        ) : (
          <div className="photo-placeholder">
            {profile.display_name?.[0] || "?"}
          </div>
        )}
        <div className="photo-gradient" />
      </Link>
      <div className="profile-card-body">
        <h3>
          <Link href={`/profiles/${profile.public_id}`}>
            {profile.display_name}, {profile.age}
          </Link>
          {profile.verification_level === "identity_verified" && (
            <ShieldCheck
              className="verified-icon"
              size={18}
              aria-label="Danh tính đã xác minh"
            />
          )}
          {profile.is_phone_verified && (
            <BadgeCheck
              className="phone-verified-icon"
              size={17}
              aria-label="Số điện thoại đã xác minh"
            />
          )}
        </h3>
        <p>
          <MapPin size={15} />
          {profile.current_province?.name || "Chưa cập nhật"}
        </p>
        <p>
          <Ruler size={15} />
          {profile.height_cm ? `${profile.height_cm} cm` : "Chưa cập nhật"} ·{" "}
          {profile.occupation_text ||
            profile.occupation_category?.name ||
            "Chưa cập nhật"}
        </p>
        <div className="chips">
          {profile.interests.slice(0, 3).map((interest) => (
            <Badge key={interest.id || interest.name}>{interest.name}</Badge>
          ))}
        </div>
        <Link
          className="btn btn-primary full"
          href={`/profiles/${profile.public_id}`}
        >
          Xem hồ sơ
        </Link>
      </div>
    </article>
  );
}
