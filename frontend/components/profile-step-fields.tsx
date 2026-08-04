"use client";

import { Card, Field, Input, Select, Textarea } from "./ui";

export type ReferenceData = {
  provinces: { code: string; name: string }[];
  occupations: { id: string; name: string }[];
  interests: { id: string; name: string }[];
  choices: Record<string, [string, string][]>;
};

type Props = {
  profile: any;
  referenceData: ReferenceData;
  setField: (key: string, value: any) => void;
};

function options(values: [string, string][]) {
  return values.map(([value, label]) => (
    <option key={value} value={value}>
      {label}
    </option>
  ));
}

export function BasicProfileFields({ profile, referenceData, setField }: Props) {
  return (
    <Card className="form-grid">
      <Field label="Tên hiển thị">
        <Input
          maxLength={80}
          value={profile.display_name || ""}
          onChange={(event) => setField("display_name", event.target.value)}
        />
      </Field>
      <Field label="Ngày sinh">
        <Input
          type="date"
          value={profile.birth_date || ""}
          onChange={(event) => setField("birth_date", event.target.value)}
        />
      </Field>
      <Field label="Giới tính">
        <Select
          value={profile.gender || ""}
          onChange={(event) => setField("gender", event.target.value)}
        >
          <option value="">Chọn</option>
          {options(referenceData.choices.genders)}
        </Select>
      </Field>
      <Field label="Muốn tìm">
        <div className="checkbox-grid">
          {referenceData.choices.genders.map(([value, label]) => (
            <label className="check" key={value}>
              <input
                type="checkbox"
                checked={(profile.interested_genders || []).includes(value)}
                onChange={(event) => {
                  const current = profile.interested_genders || [];
                  setField(
                    "interested_genders",
                    event.target.checked
                      ? [...current, value]
                      : current.filter((item: string) => item !== value),
                  );
                }}
              />
              {label}
            </label>
          ))}
        </div>
      </Field>
      <Field label="Tỉnh/thành hiện tại">
        <Select
          value={profile.current_province || ""}
          onChange={(event) => setField("current_province", event.target.value)}
        >
          <option value="">Chọn</option>
          {referenceData.provinces.map((province) => (
            <option key={province.code} value={province.code}>
              {province.name}
            </option>
          ))}
        </Select>
      </Field>
      <Field label="Tình trạng quan hệ">
        <Select
          value={profile.relationship_status || ""}
          onChange={(event) =>
            setField("relationship_status", event.target.value)
          }
        >
          <option value="">Chọn</option>
          {options(referenceData.choices.relationship_status)}
        </Select>
      </Field>
      <Field label="Mục tiêu quan hệ">
        <Select
          value={profile.relationship_goal || ""}
          onChange={(event) =>
            setField("relationship_goal", event.target.value)
          }
        >
          <option value="">Chọn</option>
          {options(referenceData.choices.goals)}
        </Select>
      </Field>
    </Card>
  );
}

export function DetailProfileFields({ profile, referenceData, setField }: Props) {
  return (
    <Card className="form-grid">
      <Field label="Chiều cao (cm)">
        <Input
          type="number"
          min={120}
          max={230}
          value={profile.height_cm || ""}
          onChange={(event) =>
            setField(
              "height_cm",
              event.target.value ? Number(event.target.value) : null,
            )
          }
        />
      </Field>
      <Field label="Quê quán">
        <Select
          value={profile.hometown_province || ""}
          onChange={(event) =>
            setField("hometown_province", event.target.value)
          }
        >
          <option value="">Chọn</option>
          {referenceData.provinces.map((province) => (
            <option key={province.code} value={province.code}>
              {province.name}
            </option>
          ))}
        </Select>
      </Field>
      <Field label="Nhóm nghề nghiệp">
        <Select
          value={profile.occupation_category || ""}
          onChange={(event) =>
            setField("occupation_category", event.target.value)
          }
        >
          <option value="">Chọn</option>
          {referenceData.occupations.map((occupation) => (
            <option key={occupation.id} value={occupation.id}>
              {occupation.name}
            </option>
          ))}
        </Select>
      </Field>
      <Field label="Nghề nghiệp cụ thể">
        <Input
          maxLength={160}
          value={profile.occupation_text || ""}
          onChange={(event) =>
            setField("occupation_text", event.target.value)
          }
        />
      </Field>
      <Field label="Học vấn">
        <Select
          value={profile.education_level || ""}
          onChange={(event) =>
            setField("education_level", event.target.value)
          }
        >
          <option value="">Chọn</option>
          {options(referenceData.choices.education)}
        </Select>
      </Field>
      <Field label="Khoảng thu nhập">
        <Select
          value={profile.income_band || ""}
          onChange={(event) => setField("income_band", event.target.value)}
        >
          <option value="">Không khai báo</option>
          {options(referenceData.choices.income)}
        </Select>
      </Field>
      <Field label="Tôn giáo">
        <Input
          maxLength={100}
          value={profile.religion || ""}
          onChange={(event) => setField("religion", event.target.value)}
        />
      </Field>
      <Field label="Hút thuốc">
        <Select
          value={profile.smoking_status || ""}
          onChange={(event) =>
            setField("smoking_status", event.target.value)
          }
        >
          <option value="">Không khai báo</option>
          {options(referenceData.choices.habits)}
        </Select>
      </Field>
      <Field label="Uống rượu">
        <Select
          value={profile.drinking_status || ""}
          onChange={(event) =>
            setField("drinking_status", event.target.value)
          }
        >
          <option value="">Không khai báo</option>
          {options(referenceData.choices.habits)}
        </Select>
      </Field>
      <Field label="Con cái">
        <Select
          value={profile.children_status || ""}
          onChange={(event) =>
            setField("children_status", event.target.value)
          }
        >
          <option value="">Không khai báo</option>
          {options(referenceData.choices.children)}
        </Select>
      </Field>
      <Field label="Kế hoạch sinh con">
        <Select
          value={profile.children_plan || ""}
          onChange={(event) =>
            setField("children_plan", event.target.value)
          }
        >
          <option value="">Không khai báo</option>
          {options(referenceData.choices.children_plan)}
        </Select>
      </Field>
    </Card>
  );
}

export function ProfileTextAndInterests({
  profile,
  referenceData,
  setField,
}: Props) {
  return (
    <Card className="form-stack">
      <Field
        label="Giới thiệu bản thân"
        hint="Tối thiểu 50, tối đa 1.500 ký tự."
      >
        <Textarea
          rows={7}
          minLength={50}
          maxLength={1500}
          value={profile.bio || ""}
          onChange={(event) => setField("bio", event.target.value)}
        />
      </Field>
      <Field label="Mong muốn ở đối phương">
        <Textarea
          rows={5}
          maxLength={1000}
          value={profile.looking_for || ""}
          onChange={(event) => setField("looking_for", event.target.value)}
        />
      </Field>
      <Field label="Sở thích (tối đa 10)">
        <div className="checkbox-grid">
          {referenceData.interests.map((interest) => (
            <label className="check" key={interest.id}>
              <input
                type="checkbox"
                checked={(profile.interest_ids || []).includes(interest.id)}
                onChange={(event) => {
                  const current: string[] = profile.interest_ids || [];
                  if (event.target.checked && current.length < 10) {
                    setField("interest_ids", [...current, interest.id]);
                  } else if (!event.target.checked) {
                    setField(
                      "interest_ids",
                      current.filter((id) => id !== interest.id),
                    );
                  }
                }}
              />
              {interest.name}
            </label>
          ))}
        </div>
      </Field>
    </Card>
  );
}

const privacyFields: Record<string, string> = {
  income_band: "Thu nhập",
  hometown_province: "Quê quán",
  current_province: "Nơi ở",
  education_level: "Học vấn",
  religion: "Tôn giáo",
  smoking_status: "Hút thuốc",
  drinking_status: "Uống rượu",
  children_status: "Con cái",
  children_plan: "Kế hoạch sinh con",
};

export function PrivacyProfileFields({ profile, setField }: Props) {
  return (
    <Card>
      <h2>Ai có thể xem?</h2>
      <p className="muted">
        Email, số điện thoại và ngày sinh đầy đủ luôn được giữ riêng tư.
      </p>
      {Object.entries(privacyFields).map(([field, label]) => (
        <Field key={field} label={label}>
          <Select
            value={(profile.field_visibility || {})[field] || "members"}
            onChange={(event) =>
              setField("field_visibility", {
                ...(profile.field_visibility || {}),
                [field]: event.target.value,
              })
            }
          >
            <option value="members">Thành viên đã đăng nhập</option>
            <option value="connections">Chỉ người đã kết nối</option>
            <option value="private">Chỉ mình tôi</option>
          </Select>
        </Field>
      ))}
    </Card>
  );
}

export function ProfileReview({ profile }: { profile: any }) {
  return (
    <Card>
      <h2>
        {profile.display_name || "Hồ sơ của bạn"}, {profile.age}
      </h2>
      <p>{profile.bio || "Chưa có giới thiệu."}</p>
      <dl className="detail-list">
        <div>
          <dt>Chiều cao</dt>
          <dd>{profile.height_cm ? `${profile.height_cm} cm` : "—"}</dd>
        </div>
        <div>
          <dt>Nghề nghiệp</dt>
          <dd>{profile.occupation_text || "—"}</dd>
        </div>
        <div>
          <dt>Ảnh</dt>
          <dd>{profile.photos.length}/6</dd>
        </div>
        <div>
          <dt>Hoàn thiện</dt>
          <dd>{profile.completion_percent}%</dd>
        </div>
      </dl>
      <p className="muted">
        Sau khi công khai, hồ sơ sẽ xuất hiện trong Khám phá. Bạn có thể ẩn hồ
        sơ bất kỳ lúc nào.
      </p>
    </Card>
  );
}
