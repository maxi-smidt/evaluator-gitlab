import {Routes} from "@angular/router";
import {DegreeProgramComponent} from "./degree-program.component";
import {userAuthGuard} from "../../core/guards/user-auth.guard";
import {UserFormComponent} from "../../shared/forms/user-form/user-form.component";
import {FullUserListComponent} from "./staff-view/full-user-list/full-user-list.component";
import {StaffListComponent} from "./staff-view/staff-list/staff-list.component";
import {CourseFormComponent} from "../../shared/forms/course-form/course-form.component";
import {CourseInstanceListComponent} from "./courses-view/course-instance-list/course-instance-list.component";
import {CourseListComponent} from "./courses-view/course-list/course-list.component";


export const dpRoutes: Routes = [{
  path: '',
  component: DegreeProgramComponent,
  canActivate: [userAuthGuard],
  canActivateChild: [userAuthGuard],
  children: [
    {
      path: 'staff', children: [
        {path: 'form', component: UserFormComponent},
        {path: 'no-staff', component: FullUserListComponent},
        {path: 'all', component: StaffListComponent}
      ]
    },
    {
      path: 'courses', children: [
        {path: 'form', component: CourseFormComponent},
        {path: 'all', component: CourseListComponent},
        {path: 'instances', component: CourseInstanceListComponent}
      ]
    }
  ]
}]
