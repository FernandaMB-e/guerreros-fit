import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ClientDetail, Discipline, ScheduleDetail } from '../../core/models/models';
import { Avatar } from '../../shared/avatar';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-clients',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, Avatar],
  providers: [DatePipe],
  templateUrl: './clients.html',
  styleUrls: ['./clients.css'],
})
export class Clients implements OnInit {
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private datePipe = inject(DatePipe);

  isListView = signal(true);
  isNew = signal(true);
  clientId = signal<number | null>(null);

  clientsList = signal<any[]>([]);
  searchTerm = signal('');

  clientName = signal('NUEVO CLIENTE');
  clientInitials = signal('NC');
  selectedPlan = signal<'Mensual' | '15 días'>('Mensual');

  existingClient = signal<ClientDetail | null>(null);
  photoFile = signal<File | null>(null);
  photoPreview = signal<string | null>(null);
  proofFile = signal<File | null>(null);

  // NUEVO: filtro que llega desde el Inicio (/clientes?membership=vencida o por_vencer)
  membershipFilter = signal<string | null>(null);

  // NUEVO: texto que se muestra en la etiqueta del filtro activo
  membershipFilterLabel = computed(() => {
    switch (this.membershipFilter()) {
      case 'vencida':
        return 'Vencidas';
      case 'por_vencer':
        return 'Por vencer';
      case 'activa':
        return 'Activas';
      case 'sin_suscripcion':
        return 'Sin suscripción';
      default:
        return null;
    }
  });

  form = this.fb.nonNullable.group({
    first_name: ['', Validators.required],
    last_name: ['', Validators.required],
    phone: ['', [Validators.required, Validators.minLength(10)]],
    discipline: ['crossfit' as Discipline, Validators.required],
  });

  nuevaVigencia = computed(() => {
    const start = new Date();
    const end = new Date();
    if (this.selectedPlan() === 'Mensual') {
      end.setDate(start.getDate() + 30);
    } else {
      end.setDate(start.getDate() + 15);
    }
    const startStr = this.datePipe.transform(start, 'dd MMM');
    const endStr = this.datePipe.transform(end, 'dd MMM');
    return `${startStr} - ${endStr}`;
  });

  // NUEVO: ahora aplica el filtro de membresía además del buscador
  filteredClients = computed(() => {
    const term = this.searchTerm().toLowerCase().trim();
    const status = this.membershipFilter();

    return this.clientsList().filter((c) => {
      if (status && c.membership?.status !== status) return false;
      if (!term) return true;

      const name = this.getClientDisplayName(c).toLowerCase();
      const phone = c.phone || '';
      return name.includes(term) || phone.includes(term);
    });
  });

  ngOnInit() {
    // NUEVO: lee el filtro de la dirección. Se actualiza también cuando solo cambia
    // la parte de "?membership=..." sin cambiar de pantalla (por ejemplo, al quitar el filtro)
    this.route.queryParamMap.subscribe((q) => this.membershipFilter.set(q.get('membership')));

    this.route.paramMap.subscribe((params) => {
      const idParam = params.get('id');
      const currentUrl = this.router.url;

      if (currentUrl.includes('/clientes/nuevo')) {
        this.isListView.set(false);
        this.isNew.set(true);
        this.resetForm();
      } else if (idParam) {
        this.isListView.set(false);
        this.isNew.set(false);
        this.clientId.set(Number(idParam));
        this.loadClientData(idParam);
      } else {
        this.isListView.set(true);
        this.loadAllClients();
      }
    });

    this.form.valueChanges.subscribe((val) => {
      if (this.isNew()) {
        const f = (val.first_name || '').trim();
        const l = (val.last_name || '').trim();
        const fullName = `${f} ${l}`.trim();
        this.clientName.set(fullName ? fullName.toUpperCase() : 'NUEVO CLIENTE');
        this.clientInitials.set(((f[0] || '') + (l[0] || '')).toUpperCase() || 'NC');
      }
    });
  }

  loadAllClients() {
    // Consultamos los clientes y los horarios simultáneamente para obtener los detalles de inscripción
    this.http.get<any[]>('/api/schedules').subscribe({
      next: (schedulesList) => {
        // Pedimos los detalles completos de cada horario activo en paralelo
        const scheduleRequests = schedulesList.map((s) =>
          this.http.get<ScheduleDetail>(`/api/schedules/${s.id}`)
        );

        forkJoin({
          clients: this.http.get<any[]>('/api/clients'),
          schedulesDetails: scheduleRequests.length > 0 ? forkJoin(scheduleRequests) : forkJoin([])
        }).subscribe({
          next: ({ clients, schedulesDetails }) => {
            // Mapeo dinámico: asociamos el ID de cada cliente con la disciplina correspondiente
            const clientDisciplineMap = new Map<number, string>();

            schedulesDetails.forEach((sch) => {
              if (sch.students && sch.students.length > 0) {
                sch.students.forEach((student) => {
                  const disciplineLabel = sch.discipline === 'crossfit' ? 'CrossFit' : 'Karate';
                  clientDisciplineMap.set(student.id, disciplineLabel);
                });
              }
            });

            const mappedClients = clients.map((c) => ({
              ...c,
              computedDiscipline: clientDisciplineMap.get(c.id) || 'Sin clase'
            }));

            this.clientsList.set(mappedClients);
          },
          error: (err) => console.error('Error al mapear detalles de clientes:', err)
        });
      },
      error: () => {
        // Fallback simple si la consulta de horarios falla
        this.http.get<any[]>('/api/clients').subscribe((data) => this.clientsList.set(data));
      }
    });
  }

  loadClientData(id: string) {
    this.http.get<ClientDetail>(`/api/clients/${id}`).subscribe({
      next: (data) => {
        this.existingClient.set(data);
        const name = this.getClientDisplayName(data);
        this.clientName.set(name);
        this.photoPreview.set(data.photo_url);
        const f = (data.first_name || '')[0] || '';
        const l = (data.last_name || '')[0] || '';
        this.clientInitials.set((f + l).toUpperCase() || 'CL');
      },
      error: () => this.router.navigate(['/clientes']),
    });
  }

  resetForm() {
    this.existingClient.set(null);
    this.clientName.set('NUEVO CLIENTE');
    this.clientInitials.set('NC');
    this.photoFile.set(null);
    this.photoPreview.set(null);
    this.proofFile.set(null);
    this.form.reset({ discipline: 'crossfit' });
  }

  selectPlan(plan: 'Mensual' | '15 días') {
    this.selectedPlan.set(plan);
  }

  onFileSelected(event: any, type: 'photo' | 'proof') {
    const file = event.target.files[0] || null;
    if (type === 'photo' && file) {
      this.photoFile.set(file);
      const reader = new FileReader();
      reader.onload = () => this.photoPreview.set(reader.result as string);
      reader.readAsDataURL(file);
    } else if (type === 'proof' && file) {
      this.proofFile.set(file);
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
  }

  onDrop(event: DragEvent, type: 'photo' | 'proof') {
    event.preventDefault();
    const file = event.dataTransfer?.files[0] || null;
    if (file) {
      this.onFileSelected({ target: { files: [file] } }, type);
    }
  }

  getClientDisplayName(c: any): string {
    if (c.full_name) return c.full_name;
    const f = c.first_name || '';
    const l = c.last_name || '';
    return `${f} ${l}`.trim() || 'Cliente sin nombre';
  }

  getClientDisciplineName(c: any): string {
    if (c.computedDiscipline && c.computedDiscipline !== 'Sin clase') {
      return c.computedDiscipline;
    }
    if (c.schedules && c.schedules.length > 0 && c.schedules[0].discipline) {
      return c.schedules[0].discipline.toLowerCase() === 'crossfit' ? 'CrossFit' : 'Karate';
    }
    return 'Sin clase';
  }

  getDaysLeft(c: any): number | null {
    if (c.membership && c.membership.days_left !== undefined && c.membership.days_left !== null) {
      return c.membership.days_left;
    }
    if (c.membership && c.membership.end_date) {
      const parts = c.membership.end_date.split('-').map(Number);
      const endDate = new Date(parts[0], parts[1] - 1, parts[2]);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const diffTime = endDate.getTime() - today.getTime();
      return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }
    return null;
  }

  getBadgeText(c: any): string {
    if (!c || !c.membership || c.membership.status === 'sin_suscripcion') {
      return 'Sin suscripción';
    }

    const days = this.getDaysLeft(c);
    if (days === null) return 'Sin suscripción';

    if (days < 0) {
      return `Vencida hace ${Math.abs(days)} ${Math.abs(days) === 1 ? 'día' : 'días'}`;
    }
    if (days === 0) return 'Vence hoy';
    if (days === 1) return 'Vence mañana';
    if (days <= 5) return `Vence en ${days} días`;
    return 'Al corriente';
  }

  getBadgeClass(c: any): string {
    if (!c || !c.membership || c.membership.status === 'sin_suscripcion') {
      return 'tag-gray';
    }
    const days = this.getDaysLeft(c);
    if (days === null || days < 0) return 'tag-red';
    if (days <= 5) return 'tag-amber';
    return 'tag-gray';
  }

  save() {
    if (this.isNew()) {
      if (this.form.invalid) return;
      const val = this.form.getRawValue();

      // 1. Consultar los horarios reales de la base de datos para mapear el ID correcto
      this.http.get<any[]>('/api/schedules').subscribe({
        next: (schedules) => {
          // Buscar el id del primer horario activo que coincida con la disciplina elegida
          const targetSchedule = schedules.find(
            (s) => s.discipline.toLowerCase() === val.discipline.toLowerCase()
          );

          // Si no encuentra coincidencia directa, se pasa la lista de schedules para que no quede huérfano
          const assignedScheduleIds = targetSchedule ? [targetSchedule.id] : [];

          const clientData = {
            first_name: val.first_name,
            last_name: val.last_name,
            phone: val.phone,
            schedule_ids: assignedScheduleIds,
          };

          // 2. Crear el cliente con el ID de horario correcto
          this.http.post<ClientDetail>('/api/clients', clientData).subscribe({
            next: (created) => {
              const tasks = [];

              if (this.photoFile()) {
                const fdPhoto = new FormData();
                fdPhoto.append('file', this.photoFile()!);
                tasks.push(this.http.post(`/api/clients/${created.id}/photo`, fdPhoto));
              }

              if (this.proofFile()) {
                const fdProof = new FormData();
                fdProof.append('file', this.proofFile()!);
                fdProof.append('client_id', created.id.toString());
                fdProof.append('plan_id', this.selectedPlan() === 'Mensual' ? '1' : '2');
                tasks.push(this.http.post('/api/proofs', fdProof));
              }

              if (tasks.length > 0) {
                forkJoin(tasks).subscribe({
                  next: () => this.router.navigate(['/clientes']),
                  error: (err) => console.error('Error al subir archivos:', err),
                });
              } else {
                this.router.navigate(['/clientes']);
              }
            },
            error: (err) => console.error('Error registrando cliente:', err),
          });
        },
        error: (err) => console.error('Error al obtener lista de horarios:', err),
      });
    } else {
      // Flujo de renovación para cliente existente
      const c = this.existingClient();
      if (!c) return;

      const tasks = [];

      if (this.photoFile()) {
        const fdPhoto = new FormData();
        fdPhoto.append('file', this.photoFile()!);
        tasks.push(this.http.post(`/api/clients/${c.id}/photo`, fdPhoto));
      }

      if (this.proofFile()) {
        const planId = this.selectedPlan() === 'Mensual' ? '1' : '2';
        const fdProof = new FormData();
        fdProof.append('file', this.proofFile()!);
        fdProof.append('client_id', c.id.toString());
        fdProof.append('plan_id', planId);
        tasks.push(this.http.post('/api/proofs', fdProof));
      }

      if (tasks.length > 0) {
        forkJoin(tasks).subscribe({
          next: () => this.router.navigate(['/clientes']),
          error: (err) => console.error('Error al actualizar cliente:', err),
        });
      } else {
        this.router.navigate(['/clientes']);
      }
    }
  }
}