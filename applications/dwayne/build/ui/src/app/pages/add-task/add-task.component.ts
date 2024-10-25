import { Component, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ServiceSubject } from 'src/app/models/service-subject.model';
import { ServiceTask } from 'src/app/models/service-task.model';
import { SubjectStore } from 'src/app/services/subject-store.service';

@Component({
  selector: 'app-add-task',
  templateUrl: './add-task.component.html',
  styleUrls: ['./add-task.component.css']
})
export class AddTaskComponent implements OnInit {
  @Input() subjectId: string;
  subject: ServiceSubject = new ServiceSubject();
  task: ServiceTask = new ServiceTask();
  constructor(private subjectStore: SubjectStore, private router: Router) {

  }
  ngOnInit(): void {
    this.subjectStore.get(this.subjectId).subscribe((subject) => {
      this.subject = subject;
    });
  }
  submit() {    
    this.task.dueDate = new Date(Date.parse(this.task.dueDateString));
    this.subjectStore.addTask(this.subject, this.task).subscribe((res) => {
      this.router.navigate(["/app/maintenance"])
    })
  }
}
