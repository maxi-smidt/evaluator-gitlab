import {Component} from '@angular/core';
import {HeaderComponent} from "./header/header.component";
import {RouterOutlet} from "@angular/router";

@Component({
  selector: 'ms-layout',
  templateUrl: './layout.component.html',
  standalone: true,
  imports: [
    HeaderComponent,
    RouterOutlet,
  ]
})
export class LayoutComponent {
  constructor() {
  }
}
