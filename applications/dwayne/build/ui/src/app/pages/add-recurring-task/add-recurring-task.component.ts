import { Component, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { RecurringService } from 'src/app/models/recurring-service.model';
import { ServiceSubject } from 'src/app/models/service-subject.model';
import { ServiceTask } from 'src/app/models/service-task.model';
import { SubjectStore } from 'src/app/services/subject-store.service';

@Component({
  selector: 'app-add-recurring-task',
  templateUrl: './add-recurring-task.component.html',
  styleUrls: ['./add-recurring-task.component.css']
})
export class AddRecurringTaskComponent implements OnInit {
  @Input() subjectId: string;
  subject: ServiceSubject = new ServiceSubject();
  task: RecurringService = new RecurringService();
  constructor(private subjectStore: SubjectStore, private router: Router) {

  }
  ngOnInit(): void {
    this.subjectStore.get(this.subjectId).subscribe((subject) => {
      this.subject = subject;
    });
  }
  submit() {
    this.subjectStore.addRecurringTask(this.subject, this.task).subscribe(() => {
      this.router.navigate(["/app/maintenance"])
    })
  }
}