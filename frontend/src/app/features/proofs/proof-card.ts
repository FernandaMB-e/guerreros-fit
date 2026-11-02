import { Component, computed, inject, input, output, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { catchError, debounceTime, distinctUntilChanged, map, of, switchMap } from 'rxjs';

import { Client, Plan, Proof } from '../../core/models/models';
import { formatPhone, membershipTag, shortDate } from '../../core/utils/format';
import { Avatar } from '../../shared/avatar';
import { apiError, newPeriod, whenText } from './proof-utils';
import { ProofsApi } from './proofs-api';

@Component({
  selector: 'app-proof-card',
  imports: [ReactiveFormsModule, Avatar],
  templateUrl: './proof-card.html',
  styleUrl: './proof-card.css',
})
export class ProofCard {
  proof = input.required<Proof>();
  plans = input.required<Plan[]>();
  zoom = output<void>();
  reviewed = output<void>();

  private api = inject(ProofsApi);
  protected phone = formatPhone;
  protected when = whenText;

  // Lo que elige el encargado; si no elige nada, vale lo que trae el comprobante
  protected picked = signal<Client | null>(null);
  private planOverride = signal<number | null | undefined>(undefined);
  protected changingPlan = signal(false);
  protected rejecting = signal(false);
  protected busy = signal(false);
  protected error = signal('');

  protected query = new FormControl('', { nonNullable: true });
  protected reason = new FormControl('', { nonNullable: true });

  // Buscador de cliente, para comprobantes de un número que no está registrado
  protected matches = toSignal(
    this.query.valueChanges.pipe(
      debounceTime(250),
      map((q) => q.trim()),
      distinctUntilChanged(),
      switchMap((q) =>
        q.length < 2
          ? of([] as Client[])
          : this.api.clients(q).pipe(catchError(() => of([] as Client[]))),
      ),
    ),
    { initialValue: [] as Client[] },
  );

  protected client = computed(() => this.picked() ?? this.proof().client);
  protected clientId = computed(() => this.client()?.id ?? null);

  protected planId = computed(() => {
    const chosen = this.planOverride();
    return chosen === undefined ? (this.proof().plan?.id ?? null) : chosen;
  });

  protected plan = computed(() => {
    const id = this.planId();
    if (id === null) return null;
    return this.plans().find((p) => p.id === id) ?? this.proof().plan;
  });

  protected tag = computed(() => {
    const membership = this.client()?.membership;
    return membership ? membershipTag(membership.status) : null;
  });

  protected origin = computed(() => {
    const p = this.proof();
    const source = p.source === 'whatsapp' ? 'WhatsApp' : 'Subido a mano';
    const sender = !this.client() && p.sender_phone ? `${formatPhone(p.sender_phone)} · ` : '';
    return `${sender}${source} · ${whenText(p.received_at)}`;
  });

  /** "14 oct – 13 nov": la vigencia que se activaría al aprobar. */
  protected period = computed(() => {
    const plan = this.plan();
    const client = this.client();
    if (!plan || !client) return null;
    const { start, end } = newPeriod(client.membership.end_date, plan.duration_days);
    return `${shortDate(start)} – ${shortDate(end)}`;
  });

  protected missing = computed(() => {
    if (!this.clientId()) return 'Elige a qué cliente pertenece.';
    if (!this.planId()) return 'Elige qué plan pagó.';
    return '';
  });

  protected canApprove = computed(() => !this.missing() && !this.busy());

  protected pickClient(client: Client) {
    this.picked.set(client);
    this.query.setValue('');
  }

  protected onPlan(value: string) {
    this.planOverride.set(value ? Number(value) : null);
    this.changingPlan.set(false);
  }

  protected approve() {
    const client_id = this.clientId();
    const plan_id = this.planId();
    if (!client_id || !plan_id || this.busy()) return;

    this.busy.set(true);
    this.error.set('');
    this.api.approve(this.proof().id, { client_id, plan_id }).subscribe({
      next: () => this.reviewed.emit(),
      error: (err) => {
        this.busy.set(false);
        this.error.set(apiError(err));
      },
    });
  }

  protected reject() {
    if (this.busy()) return;

    this.busy.set(true);
    this.error.set('');
    this.api.reject(this.proof().id, this.reason.value.trim() || null).subscribe({
      next: () => this.reviewed.emit(),
      error: (err) => {
        this.busy.set(false);
        this.error.set(apiError(err));
      },
    });
  }
}