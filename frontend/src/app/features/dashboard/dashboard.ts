import { HttpClient } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { catchError, debounceTime, distinctUntilChanged, map, of, switchMap } from 'rxjs';

import { Client, Dashboard as DashboardData, DashboardClient } from '../../core/models/models';
import { BadgesService } from '../../core/services/badges.service';
import { disciplineLabel, formatPhone, membershipTag, shortDate } from '../../core/utils/format';
import { Avatar } from '../../shared/avatar';

const RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
const PLAN_COLORS = ['#F5B700', '#3A3A36', '#8A8578'];

@Component({
  selector: 'app-dashboard',
  imports: [RouterLink, ReactiveFormsModule, Avatar],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard {
  private http = inject(HttpClient);
  private badges = inject(BadgesService);

  protected data = signal<DashboardData | null>(null);
  protected error = signal(false);

  protected radius = RADIUS;
  protected circumference = CIRCUMFERENCE;
  protected tagOf = membershipTag;
  protected phone = formatPhone;

  // Buscador: espera 250 ms después de teclear y consulta a la API.
  // null = no hay búsqueda activa; [] = no hubo resultados
  protected search = new FormControl('', { nonNullable: true });
  protected results = toSignal(
    this.search.valueChanges.pipe(
      debounceTime(250),
      map((q) => q.trim()),
      distinctUntilChanged(),
      switchMap((q) =>
        q.length < 2
          ? of(null)
          : this.http
              .get<Client[]>('/api/clients', { params: { q, limit: 6 } })
              .pipe(catchError(() => of([] as Client[]))),
      ),
    ),
    { initialValue: null },
  );

  // Dona: cada plan con su color, y "Vencidas" y "Sin suscripción" en grises
  protected total = computed(() => (this.data()?.memberships ?? []).reduce((n, s) => n + s.count, 0));
  protected segments = computed(() => {
    const total = this.total();
    let planIndex = 0;
    let offset = 0;
    return (this.data()?.memberships ?? []).map((s) => {
      const color =
        s.label === 'Vencidas'
          ? '#D9D5C8'
          : s.label === 'Sin suscripción'
            ? '#B9B5A8'
            : PLAN_COLORS[planIndex++ % PLAN_COLORS.length];
      const length = total ? (s.count / total) * CIRCUMFERENCE : 0;
      const segment = { ...s, color, length, offset };
      offset += length;
      return segment;
    });
  });

  constructor() {
    this.load();
  }

  protected load() {
    this.error.set(false);
    this.http.get<DashboardData>('/api/dashboard').subscribe({
      next: (d) => {
        this.data.set(d);
        this.badges.pendingProofs.set(d.summary.proofs_pending); // mantiene al día el número del menú
      },
      error: () => this.error.set(true),
    });
  }

  private parts(...items: (string | null | undefined)[]): string {
    return items.filter(Boolean).join(' · ');
  }

  protected overdueText(i: DashboardClient): string {
    return this.parts(disciplineLabel(i.disciplines), i.plan, `venció el ${shortDate(i.end_date)}`);
  }

  protected overdueAge(i: DashboardClient): string {
    const days = -(i.days_left ?? 0);
    return days === 1 ? 'Hace 1 día' : `Hace ${days} días`;
  }

  protected upcomingText(i: DashboardClient): string {
    const days = i.days_left ?? 0;
    const when = days === 0 ? 'Vence hoy' : days === 1 ? 'Vence mañana' : `Vence en ${days} días`;
    return this.parts(`${when} (${shortDate(i.end_date)})`, disciplineLabel(i.disciplines), i.plan);
  }
}