import {Component, OnInit} from '@angular/core';
import {TranslatePipe} from "../../../../shared/pipes/translate.pipe";
import {CourseService} from "../../services/course.service";
import {SimpleCourse, SimpleCourseInstance} from "../../models/course.model";
import {AccordionModule} from "primeng/accordion";
import {BadgeModule} from "primeng/badge";
import {Button} from "primeng/button";
import {DataViewModule} from "primeng/dataview";
import {PrimeTemplate} from "primeng/api";
import {TagModule} from "primeng/tag";
import {ActivatedRoute} from "@angular/router";
import {UrlParamService} from "../../../../shared/services/url-param.service";

@Component({
  selector: 'ms-course-instance-list',
  standalone: true,
  imports: [
    TranslatePipe,
    AccordionModule,
    BadgeModule,
    Button,
    DataViewModule,
    PrimeTemplate,
    TagModule
  ],
  templateUrl: './course-instance-list.component.html'
})
export class CourseInstanceListComponent implements OnInit {
  courseInstances: SimpleCourseInstance[] = [];
  sortedCourses: { course: SimpleCourse, courseInstances: SimpleCourseInstance[] }[] = [];

  constructor(private courseService: CourseService,
              private route: ActivatedRoute,
              private urlParamService: UrlParamService) {
  }

  ngOnInit() {
    const degreeProgramAbbreviation = this.urlParamService.findParam('abbreviation', this.route);

    this.courseService.getCourseInstances(degreeProgramAbbreviation).subscribe({
      next: value => {
        this.courseInstances = value;

        this.courseInstances.forEach(courseInstance => {
          let obj = this.sortedCourses.find(x => courseInstance.course.id === x.course.id);
          if (obj === undefined) {
            this.sortedCourses.push({course: courseInstance.course, courseInstances: [courseInstance]})
          } else {
            obj.courseInstances.push(courseInstance);
          }
        });
      }
    });
  }
}
