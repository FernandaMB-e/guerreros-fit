import { Discipline, MembershipState } from '../models/models';

/** "Luis Ángel Ruiz" -> "LR" (primera y última palabra). */
export function initials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  const last = parts.length > 1 ? parts[parts.length - 1][0] : '';
  return (parts[0][0] + last).toUpperCase();
}

/** "2026-10-15" -> "15 oct". Se arma con el calendario local para que no se corra un día por la zona horaria. */
export function shortDate(iso: string | null): string {
  if (!iso) return '';
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d)
    .toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })
    .replace('.', '');
}

/** "529711234567" -> "971 123 4567". */
export function formatPhone(phone: string): string {
  if (phone.length === 12 && phone.startsWith('52')) {
    return `${phone.slice(2, 5)} ${phone.slice(5, 8)} ${phone.slice(8)}`;
  }
  return phone;
}

const DISCIPLINES: Record<Discipline, string> = { crossfit: 'CrossFit', karate: 'Karate' };

export function disciplineLabel(list: Discipline[]): string {
  return list.map((d) => DISCIPLINES[d]).join(' y ');
}

/** Texto y clase de color de la etiqueta de membresía. */
export function membershipTag(status: MembershipState): { label: string; css: string } {
  switch (status) {
    case 'vencida':
      return { label: 'Vencida', css: 'tag-red' };
    case 'por_vencer':
      return { label: 'Por vencer', css: 'tag-amber' };
    case 'activa':
      return { label: 'Activa', css: 'tag-gray' };
    default:
      return { label: 'Sin suscripción', css: 'tag-gray' };
  }
}