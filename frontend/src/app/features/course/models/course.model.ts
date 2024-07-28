import {SimpleAssignment} from "./assignment.model";


export interface Course {
  name: string,
  abbreviation: string
}

export interface SimpleCourseInstance {
  id: number,
  year: number,
  course: Course
}

export interface CourseInstance extends SimpleCourseInstance {
  allowLateSubmission: boolean;
  lateSubmissionPenalty: number | null;
  pointStepSize: number;
}

export interface DetailCourseInstance extends CourseInstance {
  assignments: SimpleAssignment[];
}

export enum DetailLevel {
  NORMAL = 'normal',
  DETAIL = 'detail',
  SIMPLE = 'simple'
}
