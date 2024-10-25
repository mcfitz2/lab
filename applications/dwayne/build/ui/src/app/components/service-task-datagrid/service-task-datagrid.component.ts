import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { ServiceSubject } from '../../models/service-subject.model';
import { ClrModal, ClrDatagridSortOrder } from "@clr/angular";
import { ClrDatagridComparatorInterface } from "@clr/angular";
import { ServiceTask } from '../../models/service-task.model'
import { ClrDatagridFilterInterface } from "@clr/angular";
import { Subject } from 'rxjs';
import '@cds/core/checkbox/register.js';
import { RecurringService } from '../../models/recurring-service.model'
import { SubjectStore } from 'src/app/services/subject-store.service';
@Component({
  selector: 'app-service-task-datagrid',
  templateUrl: './service-task-datagrid.component.html',
  styleUrls: ['./service-task-datagrid.component.css']
})
export class ServiceTaskDatagridComponent {
  descSort = ClrDatagridSortOrder.ASC;
  confirm: boolean;
  @Input() subject: ServiceSubject;
  constructor(public subjectStore: SubjectStore) {

  }
}
