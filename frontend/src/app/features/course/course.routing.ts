import {Routes} from "@angular/router";
import {userAuthGuard} from "../../core/guards/user-auth.guard";
import {CourseComponent} from "./course.component";
import {CourseInstanceViewComponent} from "./course-instance-view/course-instance-view.component";
import {EditViewComponent} from "./edit-view/edit-view.component";
import {AssignmentInstanceViewComponent} from "../assignment/assignment-instance-view/assignment-instance-view.component";
import {CorrectionViewComponent} from "./correction-view/correction-view.component";

export const courseRoutes: Routes = [{
  path: '',
  component: CourseComponent,
  canActivate: [userAuthGuard],
  canActivateChild: [userAuthGuard],
  children: [
    {path: '', component: CourseInstanceViewComponent},
    {path: 'edit', component: EditViewComponent, canDeactivate: [(component: EditViewComponent) => component.checkChanges()]},
    {
      path: 'assignment/:assignmentId',
      children: [
        {path: '', component: AssignmentInstanceViewComponent},
        {path: 'correction/:correctionId', component: CorrectionViewComponent, canDeactivate: [(component: CorrectionViewComponent) => component.checkChanges()]}
      ]
    }
  ]
}]
