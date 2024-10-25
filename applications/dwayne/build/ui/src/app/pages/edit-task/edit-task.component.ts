import { Component, Input } from '@angular/core';
import { Router } from '@angular/router';
import { ServiceSubject } from 'src/app/models/service-subject.model';
import { ServiceTask } from 'src/app/models/service-task.model';
import { SubjectStore } from 'src/app/services/subject-store.service';

@Component({
  selector: 'app-edit-task',
  templateUrl: './edit-task.component.html',
  styleUrls: ['./edit-task.component.css']
})
export class EditTaskComponent {
  @Input() subjectId: string;
  @Input() taskName: string;
  subject: ServiceSubject = new ServiceSubject();
  task: ServiceTask = new ServiceTask();
  constructor(private subjectStore: SubjectStore, private router: Router) {

  }
  ngOnInit(): void {
      this.subjectStore.get(this.subjectId).subscribe((subject) => {
        this.subject = subject;
        this.task = this.subject.tasks.filter((t) => t.name == this.taskName)[0]
      });

  }
  submit() {
    this.subjectStore.updateTask(this.subject, this.task).subscribe(() => {
      this.router.navigate(["/app/maintenance"])
    })
  }
}
