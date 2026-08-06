"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  VideoTrack,
  useLocalParticipant,
  useParticipants,
  useTracks,
} from "@livekit/components-react";
import "@livekit/components-styles";
import {
  ConnectionQuality,
  LocalVideoTrack,
  ParticipantEvent,
  Track,
} from "livekit-client";
import {
  Flag,
  Mic,
  MicOff,
  PhoneOff,
  Signal,
  SwitchCamera,
  Video,
  VideoOff,
} from "lucide-react";
import { api } from "@/lib/api";
import type { CallSession } from "@/lib/types";
import { Button, Toast } from "@/components/ui";
import { useAuth } from "@/components/auth-provider";

function qualityLabel(quality: ConnectionQuality) {
  if (quality === ConnectionQuality.Excellent) return "Kết nối rất tốt";
  if (quality === ConnectionQuality.Good) return "Kết nối tốt";
  if (quality === ConnectionQuality.Poor) return "Kết nối yếu";
  if (quality === ConnectionQuality.Lost) return "Mất kết nối";
  return "Đang đo chất lượng";
}

function Stage({
  call,
  onEnd,
  currentUserId,
}: {
  call: CallSession;
  onEnd: () => void;
  currentUserId: string;
}) {
  const tracks = useTracks([Track.Source.Camera]);
  const participants = useParticipants();
  const { localParticipant } = useLocalParticipant();
  const [mic, setMic] = useState(false);
  const [cam, setCam] = useState(false);
  const [mediaMessage, setMediaMessage] = useState("");
  const [cameras, setCameras] = useState<MediaDeviceInfo[]>([]);
  const [quality, setQuality] = useState(ConnectionQuality.Unknown);
  const [reportMessage, setReportMessage] = useState("");

  const remoteParticipant = useMemo(
    () => participants.find((participant) => !participant.isLocal),
    [participants],
  );

  useEffect(() => {
    let cancelled = false;
    async function startMedia() {
      try {
        await localParticipant.setMicrophoneEnabled(true);
        if (!cancelled) setMic(true);
      } catch {
        if (!cancelled) {
          setMediaMessage(
            "Không thể sử dụng microphone. Bạn vẫn có thể tham gia và bật lại sau.",
          );
        }
      }
      try {
        await localParticipant.setCameraEnabled(true);
        if (!cancelled) setCam(true);
      } catch {
        if (!cancelled) {
          setCam(false);
          setMediaMessage(
            "Camera chưa được cấp quyền. Cuộc gọi đang tiếp tục ở chế độ chỉ âm thanh.",
          );
        }
      }
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        if (!cancelled) {
          setCameras(devices.filter((device) => device.kind === "videoinput"));
        }
      } catch {
        // Camera switching remains unavailable when device enumeration is blocked.
      }
    }
    void startMedia();
    return () => {
      cancelled = true;
    };
  }, [localParticipant]);

  useEffect(() => {
    if (!remoteParticipant) {
      setQuality(ConnectionQuality.Unknown);
      return;
    }
    const update = () => setQuality(remoteParticipant.connectionQuality);
    update();
    remoteParticipant.on(ParticipantEvent.ConnectionQualityChanged, update);
    return () => {
      remoteParticipant.off(ParticipantEvent.ConnectionQualityChanged, update);
    };
  }, [remoteParticipant]);

  async function toggleMicrophone() {
    try {
      const next = !mic;
      await localParticipant.setMicrophoneEnabled(next);
      setMic(next);
      setMediaMessage("");
    } catch {
      setMediaMessage("Không thể thay đổi trạng thái microphone.");
    }
  }

  async function toggleCamera() {
    try {
      const next = !cam;
      await localParticipant.setCameraEnabled(next);
      setCam(next);
      setMediaMessage("");
      if (next) {
        const devices = await navigator.mediaDevices.enumerateDevices();
        setCameras(devices.filter((device) => device.kind === "videoinput"));
      }
    } catch {
      setCam(false);
      setMediaMessage(
        "Không thể bật camera. Hãy kiểm tra quyền camera của trình duyệt.",
      );
    }
  }

  async function switchCamera() {
    try {
      const publication = localParticipant.getTrackPublication(
        Track.Source.Camera,
      );
      const localTrack = publication?.track as LocalVideoTrack | undefined;
      if (!localTrack) {
        setMediaMessage("Hãy bật camera trước khi chuyển camera.");
        return;
      }
      const available = cameras.length
        ? cameras
        : (await navigator.mediaDevices.enumerateDevices()).filter(
            (device) => device.kind === "videoinput",
          );
      if (available.length < 2) {
        setMediaMessage("Thiết bị chỉ có một camera khả dụng.");
        return;
      }
      const currentDeviceId = localTrack.mediaStreamTrack.getSettings().deviceId;
      const currentIndex = Math.max(
        0,
        available.findIndex((device) => device.deviceId === currentDeviceId),
      );
      const next = available[(currentIndex + 1) % available.length];
      await localTrack.restartTrack({ deviceId: next.deviceId });
      setCameras(available);
      setMediaMessage("");
    } catch {
      setMediaMessage("Không thể chuyển camera trên thiết bị này.");
    }
  }

  async function report() {
    const other =
      call.caller_user_id === currentUserId ? call.callee : call.caller;
    await api("/reports", {
      method: "POST",
      body: JSON.stringify({
        reported_user_public_id: other.public_id,
        target_type: "call",
        target_id: call.id,
        reason_code: "harassment",
        description: "Báo cáo từ màn hình cuộc gọi",
      }),
    });
    setReportMessage("Đã gửi báo cáo.");
  }

  return (
    <div className="video-stage">
      {tracks.map((track) => (
        <VideoTrack
          key={`${track.participant.identity}-${track.source}`}
          trackRef={track}
          className={
            track.participant.isLocal ? "local-video" : "remote-video"
          }
        />
      ))}
      <RoomAudioRenderer />
      <div className={`connection-quality quality-${quality}`}>
        <Signal size={16} /> {qualityLabel(quality)}
      </div>
      {mediaMessage && <div className="call-media-message">{mediaMessage}</div>}
      {reportMessage && (
        <Toast onDismiss={() => setReportMessage("")}>{reportMessage}</Toast>
      )}
      <div className="call-controls">
        <Button
          variant="secondary"
          title="Microphone"
          onClick={() => void toggleMicrophone()}
        >
          {mic ? <Mic /> : <MicOff />}
        </Button>
        <Button
          variant="secondary"
          title="Camera"
          onClick={() => void toggleCamera()}
        >
          {cam ? <Video /> : <VideoOff />}
        </Button>
        <Button
          variant="secondary"
          title="Chuyển camera trước/sau"
          disabled={!cam}
          onClick={() => void switchCamera()}
        >
          <SwitchCamera />
        </Button>
        <Button
          variant="secondary"
          title="Báo cáo"
          onClick={() => void report()}
        >
          <Flag />
        </Button>
        <Button variant="danger" onClick={onEnd}>
          <PhoneOff /> Kết thúc
        </Button>
      </div>
    </div>
  );
}

export default function CallPage() {
  const { callId } = useParams<{ callId: string }>();
  const [token, setToken] = useState("");
  const [url, setUrl] = useState(
    process.env.NEXT_PUBLIC_LIVEKIT_URL || "",
  );
  const [call, setCall] = useState<CallSession | null>(null);
  const [error, setError] = useState("");
  const router = useRouter();
  const { user } = useAuth();

  useEffect(() => {
    let cancelled = false;
    async function refresh() {
      try {
        const currentCall = await api<CallSession>(`/calls/${callId}`);
        if (cancelled) return;
        setCall(currentCall);
        if (
          ["declined", "cancelled", "missed", "ended", "failed"].includes(
            currentCall.status,
          )
        ) {
          router.replace("/messages");
          return;
        }
        if (
          !token &&
          ["accepted", "active", "connecting"].includes(currentCall.status)
        ) {
          const credentials = await api<any>(`/calls/${callId}/token`, {
            method: "POST",
          });
          if (!cancelled) {
            setToken(credentials.token);
            setUrl(credentials.url);
          }
        }
      } catch (caught: any) {
        if (!cancelled) setError(caught.message);
      }
    }
    void refresh();
    const timer = setInterval(refresh, 1500);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [callId, token, router]);

  async function end() {
    try {
      await api(`/calls/${callId}/end`, {
        method: "POST",
        body: JSON.stringify({ reason: "hangup" }),
      });
    } finally {
      router.push("/messages");
    }
  }

  if (error)
    return (
      <main className="call-wait">
        <h1>Không thể gọi</h1>
        <p>{error}</p>
      </main>
    );
  if (!token || !call)
    return (
      <main className="call-wait">
        <Video size={50} />
        <h1>
          {call?.status === "ringing" ? "Đang đổ chuông…" : "Đang kết nối…"}
        </h1>
        <p>
          Bạn có thể tham gia chỉ với âm thanh nếu không cấp quyền camera.
        </p>
        <Button
          variant="danger"
          onClick={async () => {
            await api(`/calls/${callId}/cancel`, { method: "POST" });
            router.push("/messages");
          }}
        >
          Hủy cuộc gọi
        </Button>
      </main>
    );
  return (
    <LiveKitRoom
      serverUrl={url}
      token={token}
      connect
      audio={false}
      video={false}
      onDisconnected={() => router.push("/messages")}
    >
      <Stage
        call={call}
        currentUserId={user!.id}
        onEnd={() => void end()}
      />
    </LiveKitRoom>
  );
}
