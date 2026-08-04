"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Connection } from "@/lib/types";
import { Button, Card, Empty } from "@/components/ui";
import { formatDate } from "@/lib/utils";

type Tab = "received" | "sent" | "accepted";

export default function Connections() {
  const [tab, setTab] = useState<Tab>("received");
  const [items, setItems] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);

  async function load(nextTab = tab) {
    setLoading(true);
    try {
      const response = await api<any>(`/connections/${nextTab}`);
      setItems(response.results || response);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [tab]);

  async function action(id: string, name: string) {
    await api(`/connections/${id}/${name}`, { method: "POST" });
    await load();
  }

  async function disconnect(connection: Connection) {
    if (
      !confirm(
        `Hủy kết nối với ${connection.other_user.display_name}? Hai bên sẽ không thể nhắn tin hoặc gọi video cho đến khi kết nối lại.`,
      )
    ) {
      return;
    }
    await api(`/connections/${connection.id}`, { method: "DELETE" });
    await load();
  }

  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Kết nối</span>
          <h1>Lời làm quen</h1>
        </div>
      </div>
      <div className="tabs">
        {[
          ["received", "Đã nhận"],
          ["sent", "Đã gửi"],
          ["accepted", "Đã kết nối"],
        ].map(([value, label]) => (
          <button
            key={value}
            className={tab === value ? "active" : ""}
            onClick={() => setTab(value as Tab)}
          >
            {label}
          </button>
        ))}
      </div>
      {loading ? (
        <p>Đang tải…</p>
      ) : items.length ? (
        <div className="stack-list">
          {items.map((connection) => {
            const other = connection.other_user;
            const photo = other.primary_photo?.public_url;
            return (
              <Card key={connection.id} className="connection-card">
                <div className="mini-avatar">
                  {photo ? <img src={photo} alt="" /> : other.display_name[0]}
                </div>
                <div className="grow">
                  <h3>
                    <Link href={`/profiles/${other.public_id}`}>
                      {other.display_name}
                    </Link>
                  </h3>
                  <p>{connection.intro_message}</p>
                  <small>
                    {formatDate(connection.sent_at)} · {connection.status}
                  </small>
                </div>
                <div className="connection-actions">
                  {tab === "received" && connection.status === "pending" && (
                    <>
                      <Button
                        variant="secondary"
                        onClick={() => action(connection.id, "decline")}
                      >
                        Từ chối
                      </Button>
                      <Button onClick={() => action(connection.id, "accept")}>
                        Chấp nhận
                      </Button>
                    </>
                  )}
                  {tab === "sent" && connection.status === "pending" && (
                    <Button
                      variant="secondary"
                      onClick={() => action(connection.id, "cancel")}
                    >
                      Hủy yêu cầu
                    </Button>
                  )}
                  {tab === "accepted" && (
                    <>
                      <Link className="btn btn-primary" href="/messages">
                        Nhắn tin
                      </Link>
                      <Button
                        variant="secondary"
                        onClick={() => disconnect(connection)}
                      >
                        Hủy kết nối
                      </Button>
                    </>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      ) : (
        <Empty
          title="Chưa có dữ liệu"
          body={
            tab === "received"
              ? "Các lời làm quen gửi tới bạn sẽ xuất hiện ở đây."
              : tab === "sent"
                ? "Bạn chưa gửi lời làm quen nào."
                : "Kết nối được chấp nhận sẽ xuất hiện ở đây."
          }
        />
      )}
    </div>
  );
}
