import type { Photo } from "./types";

export const PROFILE_LABELS = {
  gender: {
    male: "Nam",
    female: "Nữ",
    non_binary: "Phi nhị nguyên",
    other: "Khác",
  },
  education: {
    high_school: "THPT",
    college: "Cao đẳng",
    university: "Đại học",
    postgraduate: "Sau đại học",
    other: "Khác",
  },
  income: {
    under_10: "Dưới 10 triệu",
    "10_20": "10–20 triệu",
    "20_30": "20–30 triệu",
    "30_50": "30–50 triệu",
    "50_100": "50–100 triệu",
    above_100: "Trên 100 triệu",
    private: "Không muốn công khai",
  },
  relationshipGoal: {
    friendship: "Làm quen",
    serious: "Tìm hiểu nghiêm túc",
    long_term: "Hẹn hò lâu dài",
    marriage: "Hướng tới kết hôn",
  },
  relationshipStatus: {
    single: "Độc thân",
    divorced: "Đã ly hôn",
    widowed: "Góa",
  },
  habit: {
    never: "Không bao giờ",
    sometimes: "Thỉnh thoảng",
    often: "Thường xuyên",
    private: "Không muốn chia sẻ",
  },
  children: {
    none: "Chưa có",
    has: "Đã có",
    yes: "Đã có",
    no: "Chưa có",
    private: "Không muốn chia sẻ",
  },
  childrenPlan: {
    want: "Muốn có",
    not_want: "Không muốn",
    yes: "Muốn có",
    no: "Không muốn",
    unsure: "Chưa chắc chắn",
    unsured: "Chưa chắc chắn",
    private: "Không muốn chia sẻ",
  },
  visibility: {
    draft: "Bản nháp",
    published: "Công khai",
    hidden_by_user: "Đã ẩn",
    hidden_by_moderator: "Bị kiểm duyệt ẩn",
    suspended: "Đình chỉ",
    deleted: "Đã xóa",
  },
  verification: {
    none: "Chưa xác minh",
    identity_verified: "Đã xác minh danh tính",
    recheck_required: "Cần xác minh lại",
    revoked: "Đã thu hồi xác minh",
  },
} as const;

export type ProfileLabelField = keyof typeof PROFILE_LABELS;

const RELIGION_LABELS: Record<string, string> = {
  buddhism: "Phật giáo",
  buddhist: "Phật giáo",
  catholic: "Công giáo",
  catholicism: "Công giáo",
  christian: "Kitô giáo",
  christianity: "Kitô giáo",
  protestant: "Tin Lành",
  protestantism: "Tin Lành",
  islam: "Hồi giáo",
  muslim: "Hồi giáo",
  none: "Không theo tôn giáo",
  private: "Không muốn chia sẻ",
};

export function profileLabel(
  field: ProfileLabelField,
  value?: string | null,
  fallback = "Chưa cập nhật",
) {
  if (!value?.trim()) return fallback;
  const normalized = value.trim().toLowerCase();
  const labels = PROFILE_LABELS[field] as Record<string, string>;
  return labels[normalized] ?? fallback;
}

export function religionLabel(value?: string | null) {
  if (!value?.trim()) return "Chưa chia sẻ";
  const normalized = value.trim().toLowerCase();
  return RELIGION_LABELS[normalized] ?? value.trim();
}

export function genericProfileLabel(value?: string | null) {
  if (!value?.trim()) return "Chưa cập nhật";
  const normalized = value.trim().toLowerCase();
  const preferredFields: ProfileLabelField[] = [
    "gender",
    "education",
    "income",
    "relationshipGoal",
    "relationshipStatus",
    "habit",
    "children",
    "childrenPlan",
    "verification",
    "visibility",
  ];

  for (const field of preferredFields) {
    const labels = PROFILE_LABELS[field] as Record<string, string>;
    if (normalized in labels) return labels[normalized];
  }

  return "Chưa cập nhật";
}

export function orderProfilePhotos(photos: Photo[]) {
  const ordered = [...photos].sort(
    (left, right) => left.position - right.position,
  );
  const primaryIndex = ordered.findIndex((photo) => photo.is_primary);

  if (primaryIndex > 0) {
    const [primary] = ordered.splice(primaryIndex, 1);
    ordered.unshift(primary);
  }

  return ordered;
}
