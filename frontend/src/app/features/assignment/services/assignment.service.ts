import {Injectable} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {AssignmentInstance} from "../models/assignment.model";
import {EditPartition} from "../../course/models/edit-partition.model";

@Injectable({
  providedIn: 'root'
})
export class AssignmentService {

  constructor(private http: HttpClient) {
  }

  getFullAssignment(assignmentId: number) {
    return this.http.get<AssignmentInstance>(`assignment/${assignmentId}/`);
  }

  getTutorAssignmentPartition(courseId: number) {
    return this.http.get<{ partition: EditPartition[], groups: number[] }>(`course-partition/${courseId}/`);
  }

  putAssignmentPartition(courseId: number, partition: EditPartition[]) {
    return this.http.put<{ partition: EditPartition[], groups: number[] }>(`course-partition/${courseId}/`,
      {partition: partition});
  }
}
