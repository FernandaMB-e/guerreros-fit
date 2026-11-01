import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { catchError, map, of, tap } from 'rxjs';
import { User } from '../models/models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);

  /** Usuario conectado, o null si no hay sesión. */
  readonly user = signal<User | null>(null);

  login(email: string, password: string) {
    return this.http
      .post<User>('/api/auth/login', { email, password })
      .pipe(tap((user) => this.user.set(user)));
  }

  logout() {
    return this.http.post('/api/auth/logout', {}).pipe(tap(() => this.user.set(null)));
  }

  /** Pregunta al servidor si la cookie de sesión sigue vigente (por ejemplo, al recargar la página). */
  restore() {
    return this.http.get<User>('/api/auth/me').pipe(
      tap((user) => this.user.set(user)),
      map(() => true),
      catchError(() => of(false)),
    );
  }
}