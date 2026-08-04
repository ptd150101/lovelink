export type User = {
  id: string;
  email: string;
  phone?: string | null;
  status: string;
  is_email_verified: boolean;
  is_phone_verified: boolean;
  created_at: string;
};

export type Presence = {
  status: "online" | "recently_active" | "offline";
};

export type Photo = {
  id: string;
  public_url: string;
  thumbnail_url?: string;
  position: number;
  is_primary: boolean;
};

export type Named = { id?: string; code?: string; name: string };

export type Profile = {
  public_id: string;
  display_name: string;
  birth_date?: string;
  age: number;
  gender: string;
  interested_genders?: string[];
  current_province?: Named | null;
  hometown_province?: Named | null;
  height_cm?: number | null;
  occupation_category?: Named | null;
  occupation_text?: string;
  education_level?: string | null;
  income_band?: string | null;
  relationship_status?: string;
  relationship_goal?: string;
  religion?: string | null;
  smoking_status?: string | null;
  drinking_status?: string | null;
  children_status?: string | null;
  children_plan?: string | null;
  bio: string;
  looking_for?: string;
  interests: Named[];
  photos: Photo[];
  field_visibility?: Record<string, string>;
  visibility_status?: string;
  completion_percent: number;
  verification_level: string;
  verified_at?: string | null;
  connection_status?: string;
  presence?: Presence | null;
};

export type CompactUser = {
  public_id: string;
  display_name: string;
  verification_level: string;
  primary_photo?: Photo | null;
  presence?: Presence | null;
};

export type Connection = {
  id: string;
  sender: CompactUser;
  receiver: CompactUser;
  other_user: CompactUser;
  intro_message: string;
  status: string;
  sent_at: string;
  responded_at?: string | null;
  expires_at: string;
};

export type Message = {
  id: string;
  conversation: string;
  sender_public_id: string;
  client_message_id: string;
  message_type: string;
  text: string;
  created_at: string;
};

export type Conversation = {
  id: string;
  other_user: CompactUser;
  last_message?: Message | null;
  last_message_at?: string | null;
  unread_count: number;
  created_at: string;
};

export type Notification = {
  id: string;
  type: string;
  actor?: { public_id: string; display_name: string } | null;
  entity_type: string;
  entity_id: string;
  title: string;
  body: string;
  read_at?: string | null;
  created_at: string;
};

export type CallSession = {
  id: string;
  room_name: string;
  caller_user_id: string;
  callee_user_id: string;
  caller: CompactUser;
  callee: CompactUser;
  conversation: string;
  call_type: string;
  status: string;
  created_at: string;
  ringing_at?: string;
  accepted_at?: string;
  connected_at?: string;
  ended_at?: string;
  end_reason?: string;
};
