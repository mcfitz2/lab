import { Component, Input, OnInit } from '@angular/core';
import { ServiceSubject } from '../../models/service-subject.model';
import '@cds/core/checkbox/register.js';
import { SubjectStore } from 'src/app/services/subject-store.service';


@Component({
  selector: 'app-recurring-service-task-datagrid',
  templateUrl: './recurring-service-task-datagrid.component.html',
  styleUrls: ['./recurring-service-task-datagrid.component.css']
})
export class RecurringServiceTaskDatagridComponent implements OnInit {
  @Input() subject: ServiceSubject; // decorate the property with @Input()
  constructor(public subjectStore: SubjectStore) {}
  ngOnInit() {
  }  
}
