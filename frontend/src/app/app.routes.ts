import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { Shell } from './layout/shell';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login').then((m) => m.Login),
  },
  {
    path: '',
    component: Shell,
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'inicio' },
      {
        path: 'inicio',
        loadComponent: () => import('./features/dashboard/dashboard').then((m) => m.Dashboard),
      },
      {
        path: 'clientes',
        loadComponent: () => import('./features/clients/clients').then((m) => m.Clients),
      },
      {
        path: 'comprobantes',
        loadComponent: () => import('./features/proofs/proofs').then((m) => m.Proofs),
      },
      {
        path: 'horarios',
        loadComponent: () => import('./features/schedules/schedules').then((m) => m.Schedules),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];