"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Bell,
  HeartHandshake,
  LogOut,
  Menu,
  MessageCircle,
  MoreHorizontal,
  Search,
  Settings,
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

const primaryNav = [
  ["/discover", "Khám phá", Search],
  ["/connections", "Kết nối", HeartHandshake],
  ["/messages", "Tin nhắn", MessageCircle],
] as const;

const secondaryNav = [
  ["/verification", "Xác minh", ShieldCheck],
  ["/notifications", "Thông báo", Bell],
  ["/me/profile", "Hồ sơ", UserRound],
  ["/settings/account", "Cài đặt", Settings],
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const { incomingCall, clearIncoming } = useRealtime();
  const router = useRouter();
  const pathname = usePathname();
  const [profile, setProfile] = useState<{
    photos?: { public_url: string; thumbnail_url?: string; is_primary?: boolean }[];
    display_name?: string;
    verification_level?: string;
  } | null>(null);
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const accountButtonRef = useRef<HTMLButtonElement>(null);
  const logoutButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    api<any>("/profiles/me").then(setProfile).catch(() => null);
  }, [user?.email]);

  useEffect(() => {
    if (!accountMenuOpen) return;
    const first = logoutButtonRef.current;
    if (first) first.focus();
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.stopPropagation();
        closeAccountMenu();
        accountButtonRef.current?.focus();
      }
      if (event.key === "Tab") {
        const items = [
          ...document.querySelectorAll<HTMLElement>(
            ".account-menu a, .account-menu button",
          ),
        ].filter((el) => el.offsetParent !== null);
        if (!items.length) return;
        const firstItem = items[0];
        const lastItem = items[items.length - 1];
        if (event.shiftKey && document.activeElement === firstItem) {
          event.preventDefault();
          lastItem.focus();
        } else if (!event.shiftKey && document.activeElement === lastItem) {
          event.preventDefault();
          firstItem.focus();
        }
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [accountMenuOpen]);

  async function respond(accepted: boolean) {
    if (!incomingCall) return;
    try {
      const response = await api<any>(`/calls/${incomingCall.id}/respond`, {
        method: "POST",
        body: JSON.stringify({ accept: accepted }),
      });
      if (accepted) router.push(`/calls/${response.id}`);
    } finally {
      clearIncoming();
    }
  }

  async function signOut() {
    try {
      await api("/auth/logout", { method: "POST" });
    } catch {
      // Proceed with local state cleanup even if the request fails.
    }
    await logout();
    router.push("/");
  }

  function closeAccountMenu() {
    setAccountMenuOpen(false);
  }

  function closeMobileMenu() {
    setMobileMenuOpen(false);
  }

  const photo =
    profile?.photos?.find((x) => x.is_primary)?.thumbnail_url ||
    profile?.photos?.find((x) => x.is_primary)?.public_url ||
    profile?.photos?.[0]?.thumbnail_url ||
    profile?.photos?.[0]?.public_url ||
    "";
  const needsVerification =
    profile?.verification_level &&
    !["verified", "pending", "in_review"].includes(profile.verification_level);

  const isMobile = typeof window !== "undefined" && window.innerWidth <= 980;

  const primaryLinks = primaryNav;
  const secondaryLinks = secondaryNav;

  return (
    <div className="app-layout">
      <header className="topbar">
        <Link className="brand" href="/">
          LoveLink
        </Link>
        <nav className="primary-nav" aria-label="Điều hướng chính">
          {primaryLinks.map(([href, label, Icon]) => (
            <Link
              key={href}
              href={href}
              className={pathname.startsWith(href) ? "active" : ""}
            >
              <Icon size={18} aria-hidden="true" />
              <span>{label}</span>
            </Link>
          ))}
        </nav>
        <nav className="secondary-nav" aria-label="Điều hướng phụ">
          {secondaryLinks.map(([href, label, Icon]) => (
            <Link
              key={href}
              href={href}
              className={pathname.startsWith(href) ? "active" : ""}
            >
              <Icon size={18} aria-hidden="true" />
              <span>{label}</span>
            </Link>
          ))}
        </nav>
        <div className="account-area">
          <button
            ref={accountButtonRef}
            className="avatar-button"
            type="button"
            aria-label="Mở menu tài khoản"
            aria-expanded={accountMenuOpen}
            onClick={() => {
              setAccountMenuOpen((open) => !open);
            }}
          >
            {photo ? (
              <img
                src={photo}
                alt=""
                width={36}
                height={36}
                decoding="async"
                loading="lazy"
              />
            ) : (
              <UserRound size={18} aria-hidden="true" />
            )}
            {needsVerification ? <span className="status-dot" aria-hidden="true" /> : null}
          </button>

          <button
            className="mobile-menu-button"
            type="button"
            aria-label={mobileMenuOpen ? "Đóng menu" : "Mở menu"}
            aria-expanded={mobileMenuOpen}
            onClick={() => setMobileMenuOpen((open) => !open)}
          >
            {mobileMenuOpen ? <X size={20} aria-hidden="true" /> : <Menu size={20} aria-hidden="true" />}
          </button>
        </div>
      </header>

      <main className="app-main">{children}</main>

      {accountMenuOpen ? (
        <div
          className="account-menu"
          role="menu"
          aria-label="Menu tài khoản"
        >
          <Link role="menuitem" href="/me/profile" onClick={closeAccountMenu}>
            Hồ sơ
          </Link>
          <Link role="menuitem" href="/settings/account" onClick={closeAccountMenu}>
            Cài đặt
          </Link>
          <div className="account-divider" />
          <button
            ref={logoutButtonRef}
            type="button"
            role="menuitem"
            className="account-logout-button"
            onClick={signOut}
          >
            Đăng xuất
          </button>
        </div>
      ) : null}

      {mobileMenuOpen ? (
        <div
          className="mobile-menu"
          role="dialog"
          aria-modal="true"
          aria-label="Menu di động"
        >
          <button
            className="mobile-menu-close"
            type="button"
            aria-label="Đóng menu"
            onClick={closeMobileMenu}
          >
            <X size={20} aria-hidden="true" />
          </button>
          <nav className="mobile-nav-list" aria-label="Điều hướng di động">
            {primaryLinks.map(([href, label, Icon]) => (
              <Link
                key={href}
                href={href}
                onClick={closeMobileMenu}
                className={pathname.startsWith(href) ? "active" : ""}
              >
                <Icon size={18} aria-hidden="true" />
                {label}
              </Link>
            ))}
            <div className="mobile-divider" />
            {secondaryLinks.map(([href, label, Icon]) => (
              <Link
                key={href}
                href={href}
                onClick={closeMobileMenu}
                className={pathname.startsWith(href) ? "active" : ""}
              >
                <Icon size={18} aria-hidden="true" />
                {label}
                {href === "/verification" && needsVerification ? (
                  <span className="status-dot" aria-hidden="true" />
                ) : null}
              </Link>
            ))}
          </nav>
        </div>
      ) : null}

      {incomingCall ? (
        <Dialog
          title={`${incomingCall.caller.display_name} đang gọi bạn`}
          onClose={clearIncoming}
        >
          <div className="incoming-call">
            <div className="incoming-call-avatar">
              {incomingCall.caller.primary_photo?.thumbnail_url ||
              incomingCall.caller.primary_photo?.public_url ? (
                <img
                  src={
                    incomingCall.caller.primary_photo.thumbnail_url ||
                    incomingCall.caller.primary_photo.public_url
                  }
                  alt=""
                  width={120}
                  height={120}
                  decoding="async"
                />
              ) : (
                <UserRound size={48} aria-hidden="true" />
              )}
            </div>
            <p>
              {needsVerification
                ? "Bạn chưa xác minh danh tính. Cuộc gọi có thể không an toàn."
                : "Cuộc gọi video đến."}
            </p>
            <div className="incoming-call-actions">
              <Button variant="secondary" onClick={() => void respond(false)}>
                Từ chối
              </Button>
              <Button variant="primary" onClick={() => void respond(true)}>
                <Video size={16} aria-hidden="true" />
                Trả lời
              </Button>
            </div>
          </div>
        </Dialog>
      ) : null}
    </div>
  );
}
