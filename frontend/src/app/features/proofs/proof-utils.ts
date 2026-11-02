/** Mensaje de error de la API, en español y listo para mostrar. */
export function apiError(err: unknown): string {
  const detail = (err as { error?: { detail?: unknown } })?.error?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
  return 'Algo salió mal. Intenta de nuevo.';
}

/** "hoy 10:42", "ayer 20:03" o "30 oct 18:10". La API manda la hora en UTC. */
export function whenText(iso: string): string {
  const d = new Date(iso.endsWith('Z') ? iso : iso + 'Z');
  const startOfDay = (x: Date) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const days = Math.round((startOfDay(new Date()) - startOfDay(d)) / 86_400_000);
  const time = d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });

  if (days === 0) return `hoy ${time}`;
  if (days === 1) return `ayer ${time}`;
  const date = d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' }).replace('.', '');
  return `${date} ${time}`;
}

const pad = (n: number) => String(n).padStart(2, '0');
const toIso = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

/**
 * Vigencia que tendría la nueva suscripción. Misma regla que el backend:
 * empieza donde termina la actual, o hoy si ya venció o no tiene.
 */
export function newPeriod(currentEnd: string | null, durationDays: number) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let start = today;
  if (currentEnd) {
    const [y, m, d] = currentEnd.split('-').map(Number);
    const end = new Date(y, m - 1, d);
    if (end > today) start = end;
  }
  const finish = new Date(start);
  finish.setDate(finish.getDate() + durationDays);
  return { start: toIso(start), end: toIso(finish) };
}