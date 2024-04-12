import {Component} from '@angular/core';

@Component({
  selector: 'ms-root',
  template: `<router-outlet/>`
})
export class AppComponent{
  title = 'frontend';
  constructor() {
  }
}
