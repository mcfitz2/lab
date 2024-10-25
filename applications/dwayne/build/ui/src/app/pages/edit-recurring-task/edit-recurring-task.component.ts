import { Component, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { RecurringService } from 'src/app/models/recurring-service.model';
import { ServiceSubject } from 'src/app/models/service-subject.model';
import { SubjectStore } from 'src/app/services/subject-store.service';

@Component({
  selector: 'app-edit-recurring-task',
  templateUrl: './edit-recurring-task.component.html',
  styleUrls: ['./edit-recurring-task.component.css']
})
export class EditRecurringTaskComponent implements OnInit {
  @Input() subjectId: string;
  @Input() taskName: string;
  subject: ServiceSubject = new ServiceSubject();
  task: RecurringService = new RecurringService();
  constructor(private subjectStore: SubjectStore, private router: Router) {

  }
  ngOnInit(): void {
    this.subjectStore.get(this.subjectId).subscribe((subject) => {
      this.subject = subject;
      this.task = this.subject.recurringTasks.filter((t) => t.name == this.taskName)[0]
    });
  }
  submit() {
    this.subjectStore.updateRecurringTask(this.subject, this.task).subscribe(() => {
      this.router.navigate(["/app/maintenance"])
    })
  }
}