import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { ProofCounts } from '../models/models';

@Injectable({ providedIn: 'root' })
export class BadgesService {
  private http = inject(HttpClient);

  /** Comprobantes por revisar. Después de aprobar o rechazar uno, llama a refresh(). */
  readonly pendingProofs = signal(0);

  refresh() {
    this.http.get<ProofCounts>('/api/proofs/summary').subscribe({
      next: (counts) => this.pendingProofs.set(counts.pending),
      error: () => {},
    });
  }
}