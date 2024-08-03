import {Injectable} from '@angular/core';
import {
  Course,
  DetailCourse,
  DetailLevel,
  SimpleCourseInstance
} from "../models/course.model";
import {Student} from "../models/student.model";
import {HttpClient} from "@angular/common/http";
import {ChartData} from "../models/chart-data.model";
import {DegreeProgram} from "../../degree-program/models/degree-program.model";

@Injectable({
  providedIn: 'root'
})
export class CourseService {

  constructor(private http: HttpClient) {
  }

  getCourseInstances(degreeProgramAbbreviation: string | null = null) {
    const extension = degreeProgramAbbreviation !== null ? `?dp=${degreeProgramAbbreviation}` : '';
    return this.http.get<SimpleCourseInstance[]>(`course-instances/${extension}`)
  }

  getCourse<T extends SimpleCourseInstance>(courseId: number, level: DetailLevel) {
    const extension = level === DetailLevel.NORMAL ? '' : `?level=${level}`;
    return this.http.get<T>(`course/${courseId}/${extension}`);
  }

  patchCourse<T extends SimpleCourseInstance>(courseId: number, level: DetailLevel, patch: {}) {
    let extension = level === DetailLevel.NORMAL ? '' : `?level=${level}`;
    return this.http.patch<T>(`course/${courseId}/${extension}`, patch);
  }

  getStudentsInGroupsByCourse(courseId: number) {
    return this.http.get<{ groupedStudents: { [groupNr: string]: Student[] } }>(`student-group/${courseId}/`);
  }

  patchStudentsCourseGroup(courseId: number, students: { [groupNr: string]: Student[] }) {
    return this.http.patch<{ groupedStudents: { [groupNr: string]: Student[] } }>(`student-group/${courseId}/`,
      {groupedStudents: students});
  }

  getChartData(courseId: number) {
    return this.http.get<{ dataExpense: ChartData, dataPoints: ChartData }>(`course-chart/${courseId}/`);
  }

  createCourse(degreeProgram: DegreeProgram, course: Course) {
    return this.http.post('course/create/', {degreeProgram: degreeProgram.name, ...course});
  }

  getCoursesAssignments(degreeProgramAbbreviation: string) {
    return this.http.get<DetailCourse[]>(`courses/?dp=${degreeProgramAbbreviation}`);
  }

  createCourseInstance(courseId: number, year: number) {
    return this.http.post('course-instance/create/', {courseId: courseId, year: year});
  }
}
