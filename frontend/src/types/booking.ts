export type BookingTimeline = {
  requested_at?: string | null;
  accepted_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  cancelled_at?: string | null;
};

export type BookingPermissions = {
  is_customer: boolean;
  is_worker: boolean;
  is_admin: boolean;
  can_accept: boolean;
  can_decline?: boolean;
  can_cancel: boolean;
  can_review: boolean;
};

export type BookingDetail = {
  id: string;
  customer_id: string;
  worker_id: string | null;
  service_category: string;
  service_description: string;
  problem_description?: string;
  skills_required: string[];
  service_address: Record<string, unknown>;
  address: string;
  preferred_date: string;
  preferred_time_slot: string;
  estimated_duration_hours?: number;
  estimated_price: number;
  final_price?: number | null;
  status: string;
  payment_status: string;
  special_instructions?: string | null;
  cancellation_reason?: string | null;
  materials_required?: string[];
  customer: { id: string; name: string; email?: string | null; phone?: string | null };
  worker: { id: string; name: string; phone?: string | null } | null;
  timeline: BookingTimeline;
  customer_attachments?: string[];
  permissions: BookingPermissions & { can_upload_photos?: boolean };
};
