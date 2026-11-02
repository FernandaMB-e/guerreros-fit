import { Component, ElementRef, inject, signal, viewChild } from '@angular/core';

import { Plan, Proof, ProofCounts, ProofStatus } from '../../core/models/models';
import { BadgesService } from '../../core/services/badges.service';
import { ProofCard } from './proof-card';
import { apiError } from './proof-utils';
import { ProofsApi } from './proofs-api';

@Component({
  selector: 'app-proofs',
  imports: [ProofCard],
  templateUrl: './proofs.html',
  styleUrl: './proofs.css',
})
export class Proofs {
  private api = inject(ProofsApi);
  private badges = inject(BadgesService);
  private viewer = viewChild.required<ElementRef<HTMLDialogElement>>('viewer');

  protected tabs: { status: ProofStatus; label: string }[] = [
    { status: 'pending', label: 'Por revisar' },
    { status: 'approved', label: 'Aprobados' },
    { status: 'rejected', label: 'Rechazados' },
  ];

  protected status = signal<ProofStatus>('pending');
  protected proofs = signal<Proof[]>([]);
  protected counts = signal<ProofCounts | null>(null);
  protected plans = signal<Plan[]>([]);
  protected loading = signal(true);
  protected error = signal(false);
  protected uploading = signal(false);
  protected uploadError = signal('');
  protected viewing = signal<Proof | null>(null);

  constructor() {
    this.api.plans().subscribe((plans) => this.plans.set(plans));
    this.reload();
  }

  protected select(status: ProofStatus) {
    if (status === this.status()) return;
    this.status.set(status);
    this.reload();
  }

  protected reload() {
    const requested = this.status();
    this.loading.set(true);
    this.error.set(false);

    this.api.list(requested).subscribe({
      next: (list) => {
        if (this.status() !== requested) return; // cambió de pestaña mientras cargaba
        this.proofs.set(list);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.error.set(true);
      },
    });

    // Las pestañas y el número rojo del menú
    this.api.counts().subscribe((counts) => {
      this.counts.set(counts);
      this.badges.pendingProofs.set(counts.pending);
    });
  }

  protected emptyText(): string {
    switch (this.status()) {
      case 'pending':
        return 'No hay comprobantes por revisar.';
      case 'approved':
        return 'Todavía no hay comprobantes aprobados.';
      default:
        return 'Todavía no hay comprobantes rechazados.';
    }
  }

  protected onFile(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = ''; // permite elegir el mismo archivo otra vez
    if (!file) return;

    this.uploading.set(true);
    this.uploadError.set('');
    this.api.upload(file).subscribe({
      next: () => {
        this.uploading.set(false);
        this.status.set('pending');
        this.reload();
      },
      error: (err) => {
        this.uploading.set(false);
        this.uploadError.set(apiError(err));
      },
    });
  }

  protected zoom(proof: Proof) {
    this.viewing.set(proof);
    this.viewer().nativeElement.showModal();
  }

  protected closeViewer() {
    this.viewer().nativeElement.close();
  }

  protected onBackdrop(event: MouseEvent) {
    if (event.target === this.viewer().nativeElement) this.closeViewer();
  }
}