import {Component, OnInit} from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {ConfirmationService, MenuItem, MessageService} from 'primeng/api';
import {Student} from "../../models/student.model";
import {EditPartition} from "../../models/edit-partition.model";
import {CourseService} from "../../services/course.service";
import {ToastModule} from "primeng/toast";
import {ConfirmDialogModule} from "primeng/confirmdialog";
import {EditGroupComponent} from "./edit-group/edit-group.component";
import {EditPartitionComponent} from "./edit-partition/edit-partition.component";
import {TranslatePipe} from "../../../../shared/pipes/translate.pipe";
import {TranslationService} from "../../../../shared/services/translation.service";
import {TabMenuModule} from "primeng/tabmenu";
import {EditGeneralComponent} from "./edit-general/edit-general.component";
import {CourseInstance, DetailLevel} from "../../models/course.model";
import {AssignmentService} from "../../../assignment/services/assignment.service";

@Component({
  selector: 'ms-edit-view',
  templateUrl: './edit-view.component.html',
  standalone: true,
  imports: [
    ToastModule,
    ConfirmDialogModule,
    EditGroupComponent,
    EditPartitionComponent,
    TranslatePipe,
    TabMenuModule,
    EditGeneralComponent
  ]
})
export class EditViewComponent implements OnInit {
  menuItems: MenuItem[] | undefined;
  activeItem: MenuItem | undefined;

  // grouped students
  courseId: number = -1;
  groupedStudents: { [groupNr: string]: Student[] } = {};
  groupedStudentsBefore: { [groupNr: string]: Student[] } = {};

  // group partition
  partition: EditPartition[] = [];
  partitionBefore: EditPartition[] = [];
  groups: number[] = [];

  // general
  course: CourseInstance = {} as CourseInstance;
  courseBefore: CourseInstance = {} as CourseInstance;

  constructor(private courseService: CourseService,
              private route: ActivatedRoute,
              private confirmationService: ConfirmationService,
              private messageService: MessageService,
              private translationService: TranslationService,
              private assignmentService: AssignmentService) {
  }

  ngOnInit() {
    this.menuItems = [
      {label: this.translationService.translate('edit.title-students')},
      {label: this.translationService.translate('edit.title-partition')},
      {label: this.translationService.translate('edit.title-general')}
    ];

    this.activeItem = this.menuItems[0]

    // grouped students
    this.courseId = this.route.parent!.snapshot.params['courseId'];
    this.courseService.getStudentsInGroupsByCourse(this.courseId).subscribe({
      next: students => {
        this.groupedStudents = students.groupedStudents;
        this.adjustInactiveGroup();
        this.groupedStudentsBefore = JSON.parse(JSON.stringify(students.groupedStudents));
      }
    });

    // group partition
    this.assignmentService.getTutorAssignmentPartition(this.courseId).subscribe({
      next: partition => {
        this.partition = partition.partition;
        this.partitionBefore = JSON.parse(JSON.stringify(partition.partition));
        this.groups = partition.groups;
      }
    });

    // general
    this.courseService.getCourse<CourseInstance>(this.courseId, DetailLevel.NORMAL).subscribe({
      next: course => {
        this.course = course;
        this.courseBefore = JSON.parse(JSON.stringify(course));
      }
    });
  }

  onActiveItemChange(event: MenuItem) {
    this.activeItem = event;
  }

  adjustInactiveGroup() {
    if (!('-1' in this.groupedStudents)) {
      this.groupedStudents['-1'] = [];
    }
  }

  private hasChanged() {
    return this.groupHasChanged() || this.partitionHasChanged() || this.courseHasChanged();
  }

  private groupHasChanged() {
    return JSON.stringify(this.groupedStudents) !== JSON.stringify(this.groupedStudentsBefore);
  }

  private partitionHasChanged() {
    return JSON.stringify(this.partition) !== JSON.stringify(this.partitionBefore);
  }

  private courseHasChanged() {
    return JSON.stringify(this.course) !== JSON.stringify(this.courseBefore);
  }

  checkChanges() {
    if (!this.hasChanged()) {
      return true;
    }
    return this.confirmDialog().then(
      result => {
        return result;
      }
    )
  }

  private confirmDialog(): Promise<boolean> {
    return new Promise((resolve) => {
      this.confirmationService.confirm({
        message: this.translationService.translate('common.confirmDialog.message'),
        header: this.translationService.translate('common.confirmDialog.header'),
        icon: 'pi pi-exclamation-triangle',
        acceptIcon: "none",
        rejectIcon: "none",
        rejectButtonStyleClass: "p-button-text",
        accept: () => {
          resolve(true);
        },
        reject: () => {
          resolve(false);
        }
      });
    });
  }

  onSaveBtnClick() {
    if (!this.hasChanged()) {
      this.showInfoMessage('common.noChangesInfo');
      return;
    }

    if (this.groupHasChanged()) {
      this.courseService.patchStudentsCourseGroup(this.courseId, this.groupedStudents).subscribe({
        next: groupedStudents => {
          this.groupedStudents = groupedStudents.groupedStudents;
          this.groupedStudentsBefore = JSON.parse(JSON.stringify(this.groupedStudents));
          this.showInfoMessage('common.saved');
        }
      });
    }

    if (this.partitionHasChanged()) {
      this.assignmentService.putAssignmentPartition(this.courseId, this.partition).subscribe({
        next: partition => {
          this.partition = partition.partition;
          this.partitionBefore = JSON.parse(JSON.stringify(partition.partition));
          this.groups = partition.groups;
          this.showInfoMessage('common.saved');
        }
      });
    }

    if (this.courseHasChanged()) {
      this.courseService.patchCourse<CourseInstance>(this.courseId, DetailLevel.NORMAL, {
        allowLateSubmission: this.course.allowLateSubmission,
        lateSubmissionPenalty: this.course.lateSubmissionPenalty,
        pointStepSize: this.course.pointStepSize
      }).subscribe({
        next: course => {
          this.course = course;
          this.courseBefore = JSON.parse(JSON.stringify(course));
          this.showInfoMessage('common.saved');
        }
      });
    }
  }

  showInfoMessage(key: string) {
    const text = this.translationService.translate(key);
    this.messageService.add({
      severity: 'info',
      summary: 'Info',
      detail: text
    });
  }
}
