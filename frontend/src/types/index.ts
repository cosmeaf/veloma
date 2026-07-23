export type ApiResponse<T> = {
  success: boolean;
  message: string;
  data?: T;
  errors?: Record<string, unknown>;
};

export type User = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  last_login: string | null;
  roles: string[];
  status: string;
  is_active: boolean;
  is_admin: boolean;
  is_platform_staff: boolean;
  must_change_credentials?: boolean;
  two_factor_email?: boolean;
  preferences?: { theme: 'light' | 'dark'; sound_enabled: boolean };
};

export type Session = {
  id: string;
  status: string;
  ip_address: string | null;
  device: string;
  country_code: string;
  created_at: string;
  last_activity_at: string;
  expires_at: string;
  revoked_at: string | null;
  revoke_reason: string;
  metadata?: { new_device?: boolean; new_ip?: boolean; new_country?: boolean };
};

export type AccessEvent = {
  id: string;
  event_type: string;
  status: string;
  ip_address: string | null;
  country_code: string;
  device: string;
  reason: string;
  new_device: boolean;
  new_ip: boolean;
  new_country: boolean;
  created_at: string;
};

export type ClientSummary = {
  id: string;
  legal_name: string;
  commercial_name: string;
  nif: string;
  entity_type: string;
  status: string;
  assigned_staff: number | null;
  created_at: string;
};

export type ClientDetail = ClientSummary & {
  activity_code: string;
  activity_description: string;
  email: string;
  phone: string;
  website: string;
  address_line: string;
  postal_code: string;
  city: string;
  district: string;
  country: string;
  member_count: number;
  deactivation_reason: string;
  archive_reason: string;
};

export type Protocol = {
  id: string;
  number: string;
  client: string;
  client_name: string;
  title: string;
  category: string;
  priority: string;
  status: string;
  display_status: string;
  due_date: string | null;
  assigned_to: number | null;
  created_at: string;
  description?: string;
  competence_month?: number | null;
  competence_year?: number | null;
  completed_at?: string | null;
};

export type Requirement = {
  id: string;
  protocol: string;
  title: string;
  description: string;
  category: string;
  required: boolean;
  due_date: string | null;
  status: 'pending' | 'uploaded' | 'accepted' | 'rejected' | 'waived';
  fulfilled_by_document: string | null;
  completed_at: string | null;
  created_at: string;
};

export type Comment = {
  id: string;
  protocol: string;
  author_name_snapshot: string;
  message: string;
  visibility: 'public' | 'internal';
  is_edited: boolean;
  edited_at: string | null;
  created_at: string;
};

export type TimelineEvent = {
  id: string;
  event_type: string;
  actor_name_snapshot: string;
  old_value: string;
  new_value: string;
  created_at: string;
  metadata?: Record<string, unknown>;
  ip_address?: string | null;
};

export type DocumentVersion = {
  id: string;
  version_number: number;
  original_name: string;
  content_type: string;
  detected_mime_type: string;
  size: number;
  checksum_sha256: string;
  uploader_name_snapshot: string;
  scan_status: 'pending' | 'clean' | 'infected' | 'error' | 'skipped';
  change_reason: string;
  created_at: string;
};

export type PortalDocument = {
  id: string;
  client: string;
  client_name: string;
  protocol: string | null;
  folder: string | null;
  title: string;
  original_name: string;
  category: string;
  status: string;
  visibility: string;
  uploader_name_snapshot: string;
  current_version: DocumentVersion | null;
  rejection_reason: string;
  archived_at: string | null;
  created_at: string;
};

export type Invitation = {
  id: string;
  client: string;
  client_name: string;
  email: string;
  role: string;
  status: 'pending' | 'accepted' | 'expired' | 'revoked' | 'cancelled';
  expires_at: string;
  accepted_at: string | null;
  resend_count: number;
  created_at: string;
};

export type Member = {
  id: string;
  client: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  position: string;
  phone: string;
  status: string;
  can_upload: boolean;
  can_download: boolean;
  can_comment: boolean;
  can_manage_members: boolean;
  joined_at: string;
};

export type Dashboard = {
  protocols: Record<string, number>;
  recent_protocols: Protocol[];
  requirements_pending?: number;
  staff?: {
    overdue: number;
    pending_scan: number;
    quarantined: number;
    pending_invitations: number;
    expired_invitations: number;
    clients: number;
  };
};
