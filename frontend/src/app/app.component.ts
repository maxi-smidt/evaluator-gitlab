import {Component, OnInit} from '@angular/core';
import {UserService} from "./core/services/user.service";

@Component({
  selector: 'ms-root',
  templateUrl: './app.component.html'
})
export class AppComponent implements OnInit{
  title = 'frontend';

  constructor(private userService: UserService) {
  }

  ngOnInit() {
    this.isLoggedIn();
  }

  isLoggedIn() {
    return this.userService.isAuthenticated;
  }
}
