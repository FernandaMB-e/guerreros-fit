import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      const isAuthCall = req.url.includes('/api/auth/');
      if (err.status === 401 && !isAuthCall) {
        auth.user.set(null);
        router.navigateByUrl('/login');
      }
      return throwError(() => err);
    }),
  );
};