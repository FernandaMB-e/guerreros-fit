import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Client, Plan, Proof, ProofCounts, ProofStatus } from '../../core/models/models';

@Injectable({ providedIn: 'root' })
export class ProofsApi {
  private http = inject(HttpClient);

  list(status: ProofStatus) {
    return this.http.get<Proof[]>('/api/proofs', { params: { status } });
  }

  counts() {
    return this.http.get<ProofCounts>('/api/proofs/summary');
  }

  plans() {
    return this.http.get<Plan[]>('/api/plans');
  }

  clients(q: string) {
    return this.http.get<Client[]>('/api/clients', { params: { q, limit: 5 } });
  }

  /** Subida manual: el comprobante queda pendiente, sin cliente ni plan. */
  upload(file: File) {
    const body = new FormData();
    body.append('file', file);
    return this.http.post<Proof>('/api/proofs', body);
  }

  approve(id: number, body: { client_id: number; plan_id: number }) {
    return this.http.post<Proof>(`/api/proofs/${id}/approve`, body);
  }

  reject(id: number, reason: string | null) {
    return this.http.post<Proof>(`/api/proofs/${id}/reject`, { reason });
  }
}