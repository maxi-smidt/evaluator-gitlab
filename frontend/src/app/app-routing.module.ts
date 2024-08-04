import {NgModule} from '@angular/core';
import {RouterModule, Routes} from '@angular/router';
import {LoginComponent} from "./core/login/login.component";
import {userAuthGuard} from "./core/guards/user-auth.guard";
import {SettingsViewComponent} from "./features/user/settings-view/settings-view.component";
import {courseRoutes} from "./features/course/course.routing";
import {HomeComponent} from "./features/home/home.component";
import {dpRoutes} from "./features/degree-program/degree-program.routing";
import {LayoutComponent} from "./core/layout/layout.component";
import {ReportComponent} from "./features/report/report.component";
import {PlagScanComponent} from "./features/plag-scan/plag-scan.component";
import {AssignmentViewComponent} from "./features/assignment/assignment-view/assignment-view.component";

const routes: Routes = [
  {path: 'login', component: LoginComponent},
  {
    path: '',
    component: LayoutComponent,
    children: [
      {path: '', redirectTo: 'home', pathMatch: 'full'},
      {path: 'home', component: HomeComponent, canActivate: [userAuthGuard]},
      {path: 'plag-scan', component: PlagScanComponent, canActivate: [userAuthGuard]},
      {path: 'settings', component: SettingsViewComponent, canActivate: [userAuthGuard]},
      {path: 'report', component: ReportComponent, canActivate: [userAuthGuard]},
      {path: 'course/:courseId', children: courseRoutes, canActivate: [userAuthGuard], canActivateChild: [userAuthGuard]},
      {path: 'degree-program/:abbreviation', children: dpRoutes},
      {path: 'assignment/:assignmentId', component: AssignmentViewComponent, canActivate: [userAuthGuard]}
    ]
  },
  {path: '**', redirectTo: 'home', pathMatch: "full"}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {
}
