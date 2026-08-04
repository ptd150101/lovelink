"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { BadgeCheck, Flag, Send, UserX, Video } from "lucide-react";
import { api } from "@/lib/api";
import type {
  Conversation,
  Message,
  MessageReadReceipt,
  Presence,
} from "@/lib/types";
import { useRealtime } from "./realtime-provider";
import { Button, Textarea } from "./ui";
import { formatDate } from "@/lib/utils";

function presenceLabel(presence?: Presence | null) {
  if (!presence) return "Kết nối riêng tư";
  if (presence.status === "online") return "Đang hoạt động";
  if (presence.status === "recently_active") return "Hoạt động gần đây";
  return "Ngoại tuyến";
}

export function ChatView({ conversationId }: { conversationId: string }) {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [otherReadMessageId, setOtherReadMessageId] = useState<string | null>(
    null,
  );
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const bottom = useRef<HTMLDivElement>(null);
  const otherUserId = useRef<string | null>(null);
  const router = useRouter();
  const { on } = useRealtime();

  async function load() {
    const [conversationData, messageData] = await Promise.all([
      api<Conversation>(`/conversations/${conversationId}`),
      api<any>(`/conversations/${conversationId}/messages`),
    ]);
    setConversation(conversationData);
    otherUserId.current = conversationData.other_user.public_id;
    setOtherReadMessageId(
      conversationData.other_last_read_message_id || null,
    );
    const values = (messageData.results || messageData).slice().reverse();
    setMessages(values);
    const last = values.at(-1);
    if (last) {
      await api(`/conversations/${conversationId}/read`, {
        method: "POST",
        body: JSON.stringify({ message_id: last.id }),
      });
    }
  }

  useEffect(() => {
    void load();
    const stopCreated = on("message.created", (message: Message) => {
      if (message.conversation === conversationId) {
        setMessages((current) =>
          current.some((item) => item.id === message.id)
            ? current
            : [...current, message],
        );
        api(`/conversations/${conversationId}/read`, {
          method: "POST",
          body: JSON.stringify({ message_id: message.id }),
        }).catch(() => {});
      }
    });
    const stopRead = on("message.read", (receipt: MessageReadReceipt) => {
      if (
        receipt.conversation_id === conversationId &&
        receipt.reader_public_id === otherUserId.current
      ) {
        setOtherReadMessageId(receipt.message_id);
      }
    });
    const stopConnected = on("realtime.connected", () => {
      void load().catch(() => {});
    });
    return () => {
      stopCreated();
      stopRead();
      stopConnected();
    };
  }, [conversationId, on]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, otherReadMessageId]);

  const lastReadOwnMessageId = useMemo(() => {
    if (!conversation || !otherReadMessageId) return null;
    const readThrough = messages.findIndex(
      (message) => message.id === otherReadMessageId,
    );
    if (readThrough < 0) return null;
    for (let index = readThrough; index >= 0; index -= 1) {
      if (
        messages[index].sender_public_id !== conversation.other_user.public_id
      ) {
        return messages[index].id;
      }
    }
    return null;
  }, [conversation, messages, otherReadMessageId]);

  async function send() {
    if (!text.trim()) return;
    const value = text;
    setText("");
    try {
      await api(`/conversations/${conversationId}/messages/send`, {
        method: "POST",
        body: JSON.stringify({
          client_message_id: crypto.randomUUID(),
          text: value,
        }),
      });
    } catch (caught: any) {
      setText(value);
      setError(caught.message);
    }
  }

  async function call() {
    try {
      const result = await api<any>("/calls", {
        method: "POST",
        body: JSON.stringify({ conversation_id: conversationId }),
      });
      router.push(`/calls/${result.id}`);
    } catch (caught: any) {
      setError(caught.message);
    }
  }

  async function block() {
    if (
      !conversation ||
      !confirm(`Chặn ${conversation.other_user.display_name}?`)
    ) {
      return;
    }
    await api(`/users/${conversation.other_user.public_id}/block`, {
      method: "POST",
    });
    router.push("/messages");
  }

  async function report() {
    if (!conversation) return;
    const description =
      prompt("Mô tả ngắn nội dung cần báo cáo:") || "";
    const target = messages.at(-1)?.id || conversationId;
    try {
      await api("/reports", {
        method: "POST",
        body: JSON.stringify({
          reported_user_public_id: conversation.other_user.public_id,
          target_type: messages.length ? "message" : "profile",
          target_id: target,
          reason_code: "harassment",
          description,
        }),
      });
      setError("Đã gửi báo cáo tới đội ngũ kiểm duyệt.");
    } catch (caught: any) {
      setError(caught.message);
    }
  }

  if (!conversation) return <div className="chat-loading">Đang tải…</div>;

  return (
    <section className="chat-panel">
      <header className="chat-header">
        <div className="mini-avatar">
          {conversation.other_user.primary_photo?.public_url ? (
            <img
              src={conversation.other_user.primary_photo.public_url}
              alt=""
            />
          ) : (
            conversation.other_user.display_name[0]
          )}
        </div>
        <div className="grow">
          <b>
            {conversation.other_user.display_name}
            {conversation.other_user.is_phone_verified && (
              <BadgeCheck
                className="phone-verified-icon"
                size={15}
                aria-label="Đã xác minh số điện thoại"
              />
            )}
          </b>
          <small>{presenceLabel(conversation.other_user.presence)}</small>
        </div>
        <Button variant="ghost" title="Gọi video" onClick={call}>
          <Video />
        </Button>
        <Button variant="ghost" title="Báo cáo" onClick={report}>
          <Flag />
        </Button>
        <Button variant="ghost" title="Chặn" onClick={block}>
          <UserX />
        </Button>
      </header>
      <div className="messages">
        {messages.map((message) => {
          const mine =
            message.sender_public_id !== conversation.other_user.public_id;
          return (
            <div
              key={message.id}
              className={`bubble ${mine ? "mine" : "theirs"}`}
            >
              <p>{message.text}</p>
              <small>{formatDate(message.created_at)}</small>
              {mine && message.id === lastReadOwnMessageId && (
                <small className="read-receipt">Đã xem</small>
              )}
            </div>
          );
        })}
        <div ref={bottom} />
      </div>
      {error && <div className="error-inline">{error}</div>}
      <div className="composer">
        <Textarea
          rows={1}
          maxLength={2000}
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void send();
            }
          }}
          placeholder="Nhập tin nhắn…"
        />
        <Button onClick={() => void send()}>
          <Send size={18} />
        </Button>
      </div>
    </section>
  );
}
