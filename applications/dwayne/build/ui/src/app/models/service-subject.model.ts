import { RecurringService } from "./recurring-service.model";
import { ServiceTask } from "./service-task.model"
import { Document } from "./document.model";
export class ServiceSubject {
    _id: string;
    meterUnit: string;
    meterValue: number;
    thumbnail?: string;
    type: string;
    brand: string;
    model: string;
    year: number;
    tasks: ServiceTask[]
    recurringTasks: RecurringService[]
    name: string;
    documents: Document[]

}