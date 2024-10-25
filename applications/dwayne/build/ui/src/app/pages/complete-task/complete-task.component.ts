import { Component, Input, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { ServiceSubject } from 'src/app/models/service-subject.model';
import { ServiceTask } from 'src/app/models/service-task.model';
import { SubjectStore } from 'src/app/services/subject-store.service';
import { slugify } from 'src/app/utils/slugify';

@Component({
  selector: 'app-complete-task',
  templateUrl: './complete-task.component.html',
  styleUrls: ['./complete-task.component.css']
})
export class CompleteTaskComponent implements OnInit {
  @Input() subjectId: string;
  @Input() taskName: string;
  subject: ServiceSubject = new ServiceSubject();
  task: ServiceTask = new ServiceTask();
  loading: Boolean = false;
  constructor(private subjectStore: SubjectStore, private router: Router) {

  }
  ngOnInit(): void {
    this.subjectStore.get(this.subjectId).subscribe((subject) => {
      this.subject = subject;
      this.task = this.subject.tasks.filter((t) => t.name == this.taskName)[0]
      this.task.completedMeterValue = this.subject.meterValue
    });
  }
  submit() {
    this.task.completed = true;
    this.task.completedDate = new Date(Date.parse(this.task.completedDateString));
    this.loading = true;
    this.subjectStore.completeTask(this.subject, this.task).subscribe(() => {
      this.loading = false;
      this.router.navigate(["/app/maintenance"])
    })
  }
}