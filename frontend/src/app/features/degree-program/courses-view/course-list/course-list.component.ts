import {Component, OnInit} from '@angular/core';
import {CourseService} from "../../../course/services/course.service";
import {AccordionModule} from "primeng/accordion";
import {BadgeModule} from "primeng/badge";
import {DetailCourse} from "../../../course/models/course.model";
import {DataViewModule} from "primeng/dataview";
import {NgClass} from "@angular/common";
import {Button} from "primeng/button";
import {DialogModule} from "primeng/dialog";
import {InputOtpModule} from "primeng/inputotp";
import {FormsModule} from "@angular/forms";
import {MessageService} from "primeng/api";
import {ToastModule} from "primeng/toast";
import {TranslatePipe} from "../../../../shared/pipes/translate.pipe";
import {TranslationService} from "../../../../shared/services/translation.service";
import {ActivatedRoute} from "@angular/router";
import {UrlParamService} from "../../../../shared/services/url-param.service";

@Component({
  selector: 'ms-course-list',
  standalone: true,
  imports: [
    AccordionModule,
    BadgeModule,
    DataViewModule,
    NgClass,
    Button,
    DialogModule,
    InputOtpModule,
    FormsModule,
    ToastModule,
    TranslatePipe
  ],
  templateUrl: './course-list.component.html'
})
export class CourseListComponent implements OnInit {
  detailCourses: DetailCourse[] = [];
  dialogVisible: boolean = false;
  year: number | undefined;
  selectedCourseId: number | undefined;

  constructor(private courseService: CourseService,
              private messageService: MessageService,
              private translationService: TranslationService,
              private route: ActivatedRoute,
              private urlParamService: UrlParamService) {
  }

  ngOnInit() {
    const degreeProgramAbbreviation = this.urlParamService.findParam('abbreviation', this.route);

    this.courseService.getCoursesAssignments(degreeProgramAbbreviation).subscribe({
      next: value => {
        this.detailCourses = value;
      }
    });
  }

  onNewInstanceClick(event: MouseEvent, courseId: number) {
    this.dialogVisible = true;
    event.stopPropagation();
    this.selectedCourseId = courseId;
  }

  onSaveNewInstanceClick(){
    if (this.year === undefined || this.year < (new Date()).getFullYear() - 1) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: this.translationService.translate('degree-program.courses-view.course-list.error')
      })
      return;
    }

    this.dialogVisible = false;
    this.courseService.createCourseInstance(this.selectedCourseId!, this.year!).subscribe({
      next: () => {
        this.year = undefined;
      }
    });
  }
}
