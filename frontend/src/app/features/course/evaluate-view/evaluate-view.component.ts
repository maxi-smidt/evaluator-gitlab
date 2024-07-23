import {Component, OnDestroy, OnInit} from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {ConfirmationService, MenuItem, MessageService} from "primeng/api";
import {Correction, Draft} from "../models/correction.model";
import {CorrectionService} from "../services/correction.service";
import {EvaluateTableComponent} from "./evaluate-table/evaluate-table.component";
import {ContextMenuModule} from "primeng/contextmenu";
import {ConfirmDialogModule} from "primeng/confirmdialog";
import {ToastModule} from "primeng/toast";
import {TranslatePipe} from "../../../shared/pipes/translate.pipe";
import {BlockUIModule} from "primeng/blockui";
import {DialogModule} from "primeng/dialog";
import {FormsModule} from "@angular/forms";
import {UserService} from "../../../core/services/user.service";
import {tap} from "rxjs";
import {FloatLabelModule} from "primeng/floatlabel";
import {InputTextModule} from "primeng/inputtext";
import {ToggleButtonModule} from "primeng/togglebutton";
import {Student} from "../models/student.model";
import {TranslationService} from "../../../shared/services/translation.service";

@Component({
  selector: 'ms-evaluate-view',
  templateUrl: './evaluate-view.component.html',
  standalone: true,
  imports: [
    EvaluateTableComponent,
    ContextMenuModule,
    ConfirmDialogModule,
    ToastModule,
    TranslatePipe,
    BlockUIModule,
    DialogModule,
    FormsModule,
    FloatLabelModule,
    InputTextModule,
    ToggleButtonModule
  ]
})
export class EvaluateViewComponent implements OnInit, OnDestroy {
  interval: number = 0;
  courseId: number;
  assignmentId: number;
  correctionId: number | undefined;

  correction: Correction;
  correctionBefore: Correction;
  contextMenuItems: MenuItem[];

  displayLock: boolean = false;
  readOnly: boolean = false;

  expenseElement: {minute: number, hour: number} = {minute: 0, hour: 0};
  expenseNotSet: boolean = false;

  annotationPoints: number = 0;
  pointsDistribution: { [exerciseKey: string]: { [subExerciseKey: string]: number } } = {};

  constructor(private correctionService: CorrectionService,
              private route: ActivatedRoute,
              private confirmationService: ConfirmationService,
              protected messageService: MessageService,
              private userService: UserService,
              private router: Router,
              private translationService: TranslationService) {
    this.correction = {id: -1, expense: null, points: -1, draft: {} as Draft, status: "", student: {} as Student, assignment: {points: -1, name: ""}, tutorUsername: ""};
    this.correctionBefore = {} as Correction;
    this.assignmentId = -1;
    this.courseId = -1;

    this.contextMenuItems = [
      {
        label: 'Save',
        icon: 'pi pi-fw pi-save',
        command: () => {
          this.saveCorrectionIfChanged(true);
        }
      },
      {
        label: 'Download',
        icon: 'pi pi-fw pi-download',
        command: () => {
          this.saveCorrection().subscribe({
            complete: () => {
              this.correctionService.downloadCorrection(this.correctionId!);
            }
          });
        }
      },
      {
        separator: true
      },
      {
        label: 'Back',
        icon: 'pi pi-fw pi-arrow-left',
        command: () => {
          this.router.navigate(['../../'], {relativeTo: this.route}).then();
        }
      }
    ];
  }

  ngOnInit() {
    this.courseId = this.route.parent!.parent!.snapshot.params['courseId'];
    this.assignmentId = this.route.parent!.snapshot.params['assignmentId'];
    this.correctionId = this.route.snapshot.params['correctionId'];

    this.userService.getUser().subscribe({
      next: user => {
        this.correctionService.getCorrection(this.correctionId!).subscribe({
          next: correction => {
            this.correction = correction;
            this.parseExpense();
            this.correctionBefore = JSON.parse(JSON.stringify(correction));
            this.displayLock = this.correction.status === 'CORRECTED';
            this.readOnly = correction.tutorUsername !== user.username;
          },
          complete: () => {
            this.initPoints();
          }
        });
      }
    });


    this.interval = setInterval(() => {
      this.saveCorrectionIfChanged();
    }, 10000);
  }

  ngOnDestroy() {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }

  private saveCorrection(triggered: boolean = false) {
    return this.correctionService.patchCorrection(this.correctionId!, {
      points: this.totalPoints,
      draft: this.correction.draft,
      expense: this.correction.expense
    }).pipe(
      tap({
        next: (response) => {
          if (triggered) {
            this.messageService.add({severity: 'info', summary: 'Info', detail: this.translate('course.evaluateView.saved')});
          }
          this.correction = response;
          this.parseExpense();
          this.correctionBefore = JSON.parse(JSON.stringify(this.correction));
        },
        error: (error) => {
          this.messageService.add({severity: 'error', summary: 'Error', detail: this.translate('course.evaluateView.couldNotSave')});
          throw error;
        }
      })
    );
  }

  private saveCorrectionIfChanged(triggered: boolean = false) {
    if (this.hasChanged()) {
      this.saveCorrection(triggered).subscribe();
    } else {
      if (triggered) {
        this.messageService.add({severity: 'info', summary: 'Info', detail: this.translate('course.evaluateView.noChangesInfo')});
      }
    }
  }

  private initPoints() {
    for (const exc of this.correction.draft.exercise) {
      this.pointsDistribution[exc.name] = {};
      for (const subExc of exc.sub) {
        const points = subExc.notes.reduce((acc, note) => acc + note.points, 0);
        this.pointsDistribution[exc.name][subExc.name] = subExc.points + points;
      }
    }
    this.annotationPoints = this.correction.draft.annotations.reduce((acc, entry) => acc + entry.points, 0);
  }

  protected updateSubExercisePoints(points: number, subExerciseName: string, exerciseName: string) {
    this.pointsDistribution[exerciseName][subExerciseName] = points;
  }

  protected updateAnnotationPoints(points: number) {
    this.annotationPoints = points;
  }

  get totalPoints() {
    let totalPoints = this.annotationPoints;
    Object.values(this.pointsDistribution).forEach(subExercises => {
      Object.values(subExercises).forEach(points => {
        totalPoints += points;
      });
    });
    return totalPoints;
  }

  protected getTotalExercisePoints(exerciseName: string) {
    return this.correction.draft.exercise.find(ex => ex.name === exerciseName)!
      .sub.reduce((acc, subExercise) => acc + subExercise.points, 0);
  }

  protected currentExercisePoints(exerciseName: string) {
    return Object.values(this.pointsDistribution[exerciseName] || {})
      .reduce((acc, points) => acc + points, 0)
  }

  private hasChanged() {
    return JSON.stringify(this.correction) !== JSON.stringify(this.correctionBefore);
  }

  public checkChanges() {
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
        message: this.translate('course.evaluateView.confirmDialog.message'),
        header: this.translate('course.evaluateView.confirmDialog.header'),
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

  private translate(key: string) {
    return this.translationService.translate(key);
  }

  private parseExpense(){
    const expense = this.correction.expense;
    if (expense !== null) {
      const day: number = this.parseDays(expense);
      const hour = this.parseHours(expense);
      const minute = this.parseMinutes(expense);
      this.expenseElement = {minute: minute, hour: hour + day * 24};
    } else {
      this.expenseNotSet = true;
    }
  }

  protected expenseToString(): void {
    const expense = this.expenseElement;
    this.correction.expense = this.expenseNotSet ? null : `${expense.hour}:${expense.minute}:00`;
  }

  private parseDays(duration: string): number {
    const parts = duration.split(' ');
    if (parts.length > 1) {
      return parseInt(parts[0], 10);
    }
    return 0;
  }

  private parseHours(duration: string): number {
    const timePart = duration.split(' ').pop();
    return parseInt(timePart!.split(':')[0], 10);
  }

  private parseMinutes(duration: string): number {
    const timePart = duration.split(' ').pop();
    return parseInt(timePart!.split(':')[1], 10);
  }
}
