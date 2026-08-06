"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Bell,
  HeartHandshake,
  MessageCircle,
  Search,
  ShieldCheck,
  UserRound,
  Video,
  X,
} from "lucide-react";
import { useAuth } from "./auth-provider";
import { useRealtime } from "./realtime-provider";
import { api } from "@/lib/api";
import { Button } from "./ui";
import { Dialog } from "./dialog";

const nav = [
  ["/discover", "Khám phá", Search],
  ["/connections", "Kết nối", HeartHandshake],
  ["/messages", "Tin nhắn", MessageCircle],
  ["/verification", "Xác minh", ShieldCheck],
  ["/notifications", "Thông báo", Bell],
  ["/me/profile", "Hồ sơ", UserRound],
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const { user, loading, logout } = useAuth();
  const { incomingCall, clearIncoming } = useRealtime();

  if (loading) {
    return <main className="center-page">Đang tải…</main>;
  }

  const publicPath =
    path === "/" ||
    path.startsWith("/auth/") ||
    path === "/terms" ||
    path === "/privacy";

  if (publicPath || !user) {
    return <>{children}</>;
  }

  async function respond(accept: boolean) {
    if (!incomingCall) return;
    try {
      if (accept) {
        await api(`/calls/${incomingCall.id}/accept`, { method: "POST" });
        router.push(`/calls/${incomingCall.id}`);
      } else {
        await api(`/calls/${incomingCall.id}/decline`, { method: "POST" });
      }
    } finally {
      clearIncoming();
    }
  }

  return (
    <div className="app-layout">
      <header className="topbar">
        <Link href="/discover" className="brand">
          LoveLink
        </Link>
        <nav>
          {nav.map(([href, label, Icon]) => (
            <Link
              key={href}
              href={href}
              className={path.startsWith(href) ? "active" : ""}
            >
              <Icon size={18} />
              <span>{label}</span>
            </Link>
          ))}
        </nav>
        <button
          className="avatar-button"
          onClick={logout}
          title="Đăng xuất"
        >
          {user.email.slice(0, 1).toUpperCase()}
        </button>
      </header>

      <main className="app-main">{children}</main>

      <nav className="bottom-nav">
        {nav
          .slice(0, 3)
          .concat(nav.slice(5))
          .map(([href, label, Icon]) => (
            <Link
              key={href}
              href={href}
              className={path.startsWith(href) ? "active" : ""}
            >
              <Icon />
              <span>{label}</span>
            </Link>
          ))}
      </nav>

      {incomingCall && (
        <Dialog
          title={incomingCall.caller.display_name}
          onClose={() => void respond(false)}
          leading={<Video size={36} />}
          overlayClassName="call-overlay"
          contentClassName="incoming-card"
        >
          <p>đang gọi video cho bạn</p>
          <div>
            <Button variant="danger" onClick={() => void respond(false)}>
              <X size={18} /> Từ chối
            </Button>
            <Button onClick={() => void respond(true)}>
              <Video size={18} /> Trả lời
            </Button>
          </div>
        </Dialog>
      )}
    </div>
  );
}
