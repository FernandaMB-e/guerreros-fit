import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../core/services/auth.service';
import { BadgesService } from '../core/services/badges.service';

@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './shell.html',
  styleUrl: './shell.css',
})
export class Shell {
  protected auth = inject(AuthService);
  protected badges = inject(BadgesService);
  private router = inject(Router);

  constructor() {
    this.badges.refresh();
  }

  protected logout() {
    this.auth.logout().subscribe(() => this.router.navigateByUrl('/login'));
  }
}