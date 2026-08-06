import type { Metadata } from "next";
import "./globals.css";
import "./mvp-completion.css";
import { AuthProvider } from "@/components/auth-provider";
import { RealtimeProvider } from "@/components/realtime-provider";
import { AppShell } from "@/components/app-shell";

export const metadata: Metadata = {
  title: "LoveLink — Kết nối chân thành",
  description: "Nền tảng hẹn hò với hồ sơ được xác minh",
  icons: { icon: "/icon.svg" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <AuthProvider>
          <RealtimeProvider>
            <AppShell>{children}</AppShell>
          </RealtimeProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
