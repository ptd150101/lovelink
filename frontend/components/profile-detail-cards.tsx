import { Card } from "@/components/ui";
import { ProfileInfoRow } from "@/components/profile-info-row";
import { profileLabel, religionLabel } from "@/lib/profile";
import type { Profile } from "@/lib/types";

type DetailCardProps = {
  profile: Profile;
  detailListClassName: string;
};

export function AboutCard({ profile }: Pick<DetailCardProps, "profile">) {
  return (
    <Card>
      <h2>Giới thiệu</h2>
      <p className="prose">{profile.bio || "Chưa cập nhật."}</p>
    </Card>
  );
}

export function PartnerPreferenceCard({
  profile,
}: Pick<DetailCardProps, "profile">) {
  return (
    <Card>
      <h2>Mong muốn ở đối phương</h2>
      <p className="prose">{profile.looking_for || "Chưa cập nhật."}</p>
    </Card>
  );
}

export function BasicInfoCard({ profile, detailListClassName }: DetailCardProps) {
  return (
    <Card>
      <h2>Thông tin cơ bản</h2>
      <dl className={detailListClassName}>
        <ProfileInfoRow
          label="Quê quán"
          value={profile.hometown_province?.name || "Chưa cập nhật"}
        />
        <ProfileInfoRow
          label="Học vấn"
          value={profileLabel("education", profile.education_level)}
        />
        <ProfileInfoRow
          label="Thu nhập"
          value={profileLabel("income", profile.income_band)}
        />
        <ProfileInfoRow
          label="Mục tiêu"
          value={profileLabel("relationshipGoal", profile.relationship_goal)}
        />
        <ProfileInfoRow
          label="Tình trạng"
          value={profileLabel(
            "relationshipStatus",
            profile.relationship_status,
          )}
        />
      </dl>
    </Card>
  );
}

export function LifestyleCard({ profile, detailListClassName }: DetailCardProps) {
  return (
    <Card>
      <h2>Lối sống</h2>
      <dl className={detailListClassName}>
        <ProfileInfoRow
          label="Hút thuốc"
          value={profileLabel("habit", profile.smoking_status)}
        />
        <ProfileInfoRow
          label="Uống rượu"
          value={profileLabel("habit", profile.drinking_status)}
        />
        <ProfileInfoRow
          label="Con cái"
          value={profileLabel("children", profile.children_status)}
        />
        <ProfileInfoRow
          label="Kế hoạch sinh con"
          value={profileLabel("childrenPlan", profile.children_plan)}
        />
        <ProfileInfoRow
          label="Tôn giáo"
          value={religionLabel(profile.religion)}
        />
      </dl>
    </Card>
  );
}
