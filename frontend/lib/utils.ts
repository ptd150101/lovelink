import { genericProfileLabel } from "./profile";

export function cn(...v: (string | false | null | undefined)[]) {
  return v.filter(Boolean).join(" ");
}

export function formatDate(v?: string | null) {
  return v
    ? new Intl.DateTimeFormat("vi-VN", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(v))
    : "";
}

export function label(value?: string | null) {
  return genericProfileLabel(value);
}

export function avatar(profile: {
  display_name?: string;
  photos?: {
    public_url: string;
    thumbnail_url?: string;
    is_primary?: boolean;
  }[];
}) {
  const photo =
    profile.photos?.find((item) => item.is_primary) || profile.photos?.[0];
  return photo?.thumbnail_url || photo?.public_url || "";
}

const connectionLabels: Record<string, string> = {
  none: "Chưa gửi lời làm quen",
  pending: "Đang chờ phản hồi",
  accepted: "Đã kết nối",
  declined: "Lời làm quen đã bị từ chối",
  cancelled: "Lời làm quen đã được hủy",
  expired: "Lời làm quen đã hết hạn",
  blocked: "Kết nối đã bị chặn",
};

export function connectionStatusLabel(status?: string | null) {
  if (!status) return connectionLabels.none;
  if (status.startsWith("sent_")) {
    return `Bạn đã gửi · ${
      connectionLabels[status.slice(5)] || "Trạng thái chưa xác định"
    }`;
  }
  if (status.startsWith("received_")) {
    return `Bạn đã nhận · ${
      connectionLabels[status.slice(9)] || "Trạng thái chưa xác định"
    }`;
  }
  return connectionLabels[status] || "Trạng thái kết nối chưa xác định";
}

export function safeErrorMessage() {
  return "Không thể hoàn tất thao tác. Hãy thử lại.";
}
