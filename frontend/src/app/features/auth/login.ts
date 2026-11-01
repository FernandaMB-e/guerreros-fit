import { Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  private auth = inject(AuthService);
  private router = inject(Router);
  private fb = inject(NonNullableFormBuilder);

  protected form = this.fb.group({
    email: ['', Validators.required],
    password: ['', Validators.required],
  });
  protected error = signal('');
  protected loading = signal(false);

  protected submit() {
    if (this.form.invalid || this.loading()) return;

    this.loading.set(true);
    this.error.set('');
    const { email, password } = this.form.getRawValue();

    this.auth.login(email, password).subscribe({
      next: () => this.router.navigateByUrl('/inicio'),
      error: (err) => {
        this.loading.set(false);
        this.error.set(
          err.status === 401
            ? 'Correo o contraseña incorrectos'
            : 'No se pudo conectar con el servidor',
        );
      },
    });
  }
}