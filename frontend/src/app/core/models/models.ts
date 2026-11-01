export type MembershipState = 'activa' | 'por_vencer' | 'vencida' | 'sin_suscripcion';
export type Discipline = 'crossfit' | 'karate';
export type ProofStatus = 'pending' | 'approved' | 'rejected';

export interface User {
  id: number;
  email: string;
  full_name: string;
}

export interface Membership {
  status: MembershipState;
  plan: string | null;
  end_date: string | null; // formato 2026-11-15
  days_left: number | null; // negativo si ya venció
}

export interface Plan {
  id: number;
  name: string;
  duration_days: number;
  price: number;
  is_active: boolean;
}

export interface ScheduleBrief {
  id: number;
  discipline: Discipline;
  start_time: string; // 16:00:00
  end_time: string;
  weekdays: number[]; // 0 = lunes ... 6 = domingo
}

export interface Client {
  id: number;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  email: string | null;
  guardian_name: string | null;
  notes: string | null;
  photo_url: string | null;
  is_active: boolean;
  created_at: string;
  membership: Membership;
}

export interface ClientDetail extends Client {
  schedules: ScheduleBrief[];
}

export interface Subscription {
  id: number;
  client_id: number;
  plan: Plan;
  start_date: string;
  end_date: string;
  status: 'active' | 'cancelled';
  is_expired: boolean;
  days_left: number;
}

export interface ProofClient {
  id: number;
  full_name: string;
  phone: string;
  photo_url: string | null;
  membership: Membership;
}

export interface Proof {
  id: number;
  status: ProofStatus;
  source: string; // whatsapp o manual
  sender_phone: string | null;
  image_url: string;
  received_at: string; // en UTC
  reviewed_at: string | null;
  rejection_reason: string | null;
  subscription_id: number | null;
  client: ProofClient | null;
  plan: Plan | null;
}

export interface ProofCounts {
  pending: number;
  approved: number;
  rejected: number;
}

export interface DashboardSummary {
  total_clients: number;
  up_to_date: number;
  pending_payment: number;
  expiring_soon: number;
  no_subscription: number;
  proofs_pending: number;
}

export interface DashboardClient {
  client_id: number;
  full_name: string;
  photo_url: string | null;
  disciplines: Discipline[];
  plan: string | null;
  status: MembershipState;
  end_date: string | null;
  days_left: number | null;
  urgency: 'urgente' | 'proximo' | null;
  reminder_sent: boolean;
}

export interface MembershipSlice {
  label: string;
  count: number;
}

export interface Dashboard {
  summary: DashboardSummary;
  overdue: DashboardClient[];
  upcoming: DashboardClient[];
  memberships: MembershipSlice[];
}