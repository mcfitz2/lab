import { Component, Input, OnInit } from '@angular/core';
import { ServiceSubject } from '../../models/service-subject.model';
import '@cds/core/checkbox/register.js';
import { RecurringService } from '../../models/recurring-service.model'
import { SubjectStore } from 'src/app/services/subject-store.service';


@Component({
  selector: 'app-subject-card',
  templateUrl: './subject-card.component.html',
  styleUrls: ['./subject-card.component.css'],
  providers: []
})

export class SubjectCardComponent implements OnInit {
  @Input() subject: ServiceSubject; 
  constructor(
    private subjectStore: SubjectStore,
  ) {}


  ngOnInit() {
    
  }
}
