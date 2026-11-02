import { Component, computed, input } from '@angular/core';
import { initials } from '../core/utils/format';

/** Foto redonda del cliente; si no tiene, muestra sus iniciales. */
@Component({
  selector: 'app-avatar',
  template: `
    <span
      class="avatar"
      [style.width.px]="size()"
      [style.height.px]="size()"
      [style.font-size.px]="size() * 0.34"
    >
      @if (photoUrl()) {
        <img [src]="photoUrl()" alt="" />
      } @else {
        <span aria-hidden="true">{{ initials() }}</span>
      }
    </span>
  `,
  styles: ':host { display: inline-flex; }',
})
export class Avatar {
  name = input.required<string>();
  photoUrl = input<string | null>(null);
  size = input(44);

  protected initials = computed(() => initials(this.name()));
}