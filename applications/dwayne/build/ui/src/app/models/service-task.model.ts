import { ServiceSubject } from "./service-subject.model";

export class ServiceTask {
    _id: string;
    name: string;
    completedMeterValue: number;
    completedDate: Date;
    completedDateString: string;
    notes: string;
    completed: boolean;
    confirm:boolean;
    todoistId: string;
    dueDate: Date;
    dueDateString: string;
}