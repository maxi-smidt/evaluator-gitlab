import {Component, OnInit} from '@angular/core';
import {UserService} from "../../../core/services/user.service";
import {TranslatePipe} from "../../../shared/pipes/translate.pipe";
import {CourseCardComponent} from "./course-card/course-card.component";
import {SimpleCourseInstance} from "../../course/models/course.model";
import {DropdownModule} from "primeng/dropdown";
import {FormsModule} from "@angular/forms";
import {TranslationService} from "../../../shared/services/translation.service";

@Component({
  selector: 'ms-tutor-home',
  templateUrl: './tutor-home.component.html',
  standalone: true,
  imports: [TranslatePipe, CourseCardComponent, DropdownModule, FormsModule]
})
export class TutorHomeComponent implements OnInit {
  courseInstances: SimpleCourseInstance[] = [];
  yearItems: string[] = [];
  selectedYear: string | undefined;
  allString: string;

  constructor(private userService: UserService,
              private translationService: TranslationService) {
    this.allString = this.translationService.translate('home.tutorHome.all');
  }

  ngOnInit() {
    this.userService.getUserCourses().subscribe({
      next: courseInstances => {
        this.courseInstances = courseInstances;
        this.fillItems();
      }
    });
  }

  private fillItems() {
    this.yearItems = this.courseInstances.map( ci => ci.year.toString());
    this.yearItems.push(this.allString);
    this.selectedYear = this.allString;
  }
}
