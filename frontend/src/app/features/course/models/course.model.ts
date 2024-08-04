import {SimpleAssignment, SimpleAssignmentInstance} from "../../assignment/models/assignment.model";


export interface SimpleCourse {
  id: number,
  name: string,
  abbreviation: string
}

export interface Course extends SimpleCourse {
  fileName: string
}

/**
 * Course and all its assignments.
 */
export interface DetailCourse extends SimpleCourse {
  assignments: SimpleAssignment[];
}

export interface SimpleCourseInstance {
  id: number,
  year: number,
  course: SimpleCourse
}

export interface CourseInstance extends SimpleCourseInstance {
  allowLateSubmission: boolean;
  lateSubmissionPenalty: number | null;
  pointStepSize: number;
}

export interface DetailCourseInstance extends CourseInstance {
  assignments: SimpleAssignmentInstance[];
}

export enum DetailLevel {
  NORMAL = 'normal',
  DETAIL = 'detail',
  SIMPLE = 'simple'
}
