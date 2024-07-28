import {Injectable} from '@angular/core';
import {CourseInstance, DetailCourseInstance, DetailLevel, SimpleCourseInstance} from "../models/course.model";
import {Assignment} from "../models/assignment.model";
import {Student} from "../models/student.model";
import {EditPartition} from "../models/edit-partition.model";
import {HttpClient} from "@angular/common/http";

@Injectable({
  providedIn: 'root'
})
export class CourseService {

  constructor(private http: HttpClient) {
  }

  getCourse<T extends SimpleCourseInstance>(courseId: number, level: DetailLevel) {
    let extension = level === DetailLevel.NORMAL ? '' : `?level=${level}`;
    return this.http.get<T>(`course/${courseId}/${extension}`);
  }

  patchCourse<T extends SimpleCourseInstance>(courseId: number, level: DetailLevel, patch: {}) {
    let extension = level === DetailLevel.NORMAL ? '' : `?level=${level}`;
    return this.http.patch<T>(`course/${courseId}/${extension}`, patch);
  }

  getFullAssignment(assignmentId: number) {
    return this.http.get<Assignment>(`assignment/${assignmentId}/`);
  }

  getStudentsInGroupsByCourse(courseId: number) {
    return this.http.get<{ groupedStudents: { [groupNr: string]: Student[] } }>(`student-group/${courseId}/`);
  }

  patchStudentsCourseGroup(courseId: number, students: { [groupNr: string]: Student[] }) {
    return this.http.patch<{ groupedStudents: { [groupNr: string]: Student[] } }>(`student-group/${courseId}/`,
      {groupedStudents: students});
  }

  getTutorAssignmentPartition(courseId: number) {
    return this.http.get<{ partition: EditPartition[], groups: number[] }>(`course-partition/${courseId}/`);
  }

  putAssignmentPartition(courseId: number, partition: EditPartition[]) {
    return this.http.put<{ partition: EditPartition[], groups: number[] }>(`course-partition/${courseId}/`,
      {partition: partition});
  }
}
