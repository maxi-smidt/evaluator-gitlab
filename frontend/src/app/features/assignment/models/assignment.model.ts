import {AssignmentStudent} from "../../course/models/student.model";

export interface AssignmentInstance extends SimpleAssignmentInstance {
  groupedStudents: { [groupNr: string]: AssignmentStudent[] };
  targetGroups: number[]
}

export interface SimpleAssignmentInstance {
  id: number,
  name: string,
  dueTo: Date,
  status: string,
  participantsLeft: number
}

export interface Assignment {
  id: number
  name: string,
  points: number
}
