import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ScheduleBrief, ScheduleDetail, Discipline } from '../../core/models/models';
import { Avatar } from '../../shared/avatar';
import { membershipTag } from '../../core/utils/format';

interface ScheduleItem extends ScheduleBrief {
  is_active: boolean;
  student_count: number;
}

@Component({
  selector: 'app-schedules',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, Avatar],
  templateUrl: './schedules.html',
  styleUrl: './schedules.css',
})
export class Schedules implements OnInit {
  private http = inject(HttpClient);
  private fb = inject(FormBuilder);

  schedules = signal<ScheduleItem[]>([]);
  selectedSchedule = signal<ScheduleDetail | null>(null);
  showCreateModal = signal(false);

  weekDays = [
    { id: 0, label: 'LUN' },
    { id: 1, label: 'MAR' },
    { id: 2, label: 'MIÉ' },
    { id: 3, label: 'JUE' },
    { id: 4, label: 'VIE' },
  ];

  hoursList = ['06:00', '07:00', '08:00', '16:00', '17:00', '18:00', '19:00'];

  hours = computed(() => {
    const custom = this.schedules().map((s) => s.start_time.substring(0, 5));
    return Array.from(new Set([...this.hoursList, ...custom])).sort();
  });

  createForm = this.fb.nonNullable.group({
    discipline: ['karate' as Discipline, Validators.required],
    start_time: ['16:00', Validators.required],
    end_time: ['17:00', Validators.required],
    weekdays: [[0, 1, 2, 3, 4], Validators.required],
  });

  ngOnInit() {
    this.loadSchedules();
  }

  loadSchedules() {
    this.http.get<ScheduleItem[]>('/api/schedules').subscribe({
      next: (data) => {
        this.schedules.set(data);
        if (data.length > 0) {
          const activeId = this.selectedSchedule()?.id;
          const exists = data.some((s) => s.id === activeId);
          this.selectSchedule(exists ? activeId! : data[0].id);
        } else {
          this.selectedSchedule.set(null);
        }
      },
    });
  }

  selectSchedule(id: number) {
    this.http.get<ScheduleDetail>(`/api/schedules/${id}`).subscribe({
      next: (detail) => this.selectedSchedule.set(detail),
    });
  }

  getScheduleForSlot(hourStr: string, dayIndex: number): ScheduleItem | undefined {
    return this.schedules().find((s) => {
      const start = s.start_time.substring(0, 5);
      return start === hourStr && s.weekdays.includes(dayIndex);
    });
  }

  openCreateModal() {
    this.showCreateModal.set(true);
  }

  closeCreateModal() {
    this.showCreateModal.set(false);
    this.createForm.reset({
      discipline: 'karate',
      start_time: '16:00',
      end_time: '17:00',
      weekdays: [0, 1, 2, 3, 4],
    });
  }

  toggleDay(dayId: number) {
    const currentDays = [...this.createForm.controls.weekdays.value];
    const idx = currentDays.indexOf(dayId);
    if (idx > -1) {
      currentDays.splice(idx, 1);
    } else {
      currentDays.push(dayId);
    }
    this.createForm.controls.weekdays.setValue(currentDays.sort());
  }

  isDaySelected(dayId: number): boolean {
    return this.createForm.controls.weekdays.value.includes(dayId);
  }

  createSchedule() {
    if (this.createForm.invalid) return;

    const val = this.createForm.getRawValue();
    const startTimeFormatted = `${val.start_time}:00`;
    const endTimeFormatted = `${val.end_time}:00`;

    // Busca si ya existe un bloque a la misma hora en el cliente
    const existing = this.schedules().find(
      (s) => s.start_time.substring(0, 5) === val.start_time
    );

    const payload = {
      discipline: val.discipline,
      start_time: startTimeFormatted,
      end_time: endTimeFormatted,
      weekdays: val.weekdays,
    };

    if (existing) {
      // Usa el PATCH que ya existe en routers/schedules.py para actualizar el horario sin duplicarlo
      this.http.patch<ScheduleItem>(`/api/schedules/${existing.id}`, payload).subscribe({
        next: (updated) => {
          this.closeCreateModal();
          this.loadSchedules();
          this.selectSchedule(updated.id);
        },
        error: (err) => console.error('Error al actualizar horario existente:', err),
      });
    } else {
      // Si la hora es nueva, usa POST /api/schedules
      this.http.post<ScheduleItem>('/api/schedules', payload).subscribe({
        next: (created) => {
          this.closeCreateModal();
          this.loadSchedules();
          this.selectSchedule(created.id);
        },
        error: (err) => console.error('Error al crear horario:', err),
      });
    }
  }

  formatTime(timeStr: string): string {
    return timeStr ? timeStr.substring(0, 5) : '';
  }

  getStudentStatusLabel(client: any): { text: string; css: string } {
    if (!client.membership) return { text: 'Sin suscripción', css: 'tag-gray' };
    const { label, css } = membershipTag(client.membership.status);
    if (client.membership.status === 'por_vencer' && client.membership.days_left !== null) {
      const d = client.membership.days_left;
      const text = d === 0 ? 'Vence hoy' : d === 1 ? 'Vence en 1 día' : `Vence en ${d} días`;
      return { text, css };
    }
    return { text: label, css };
  }
}