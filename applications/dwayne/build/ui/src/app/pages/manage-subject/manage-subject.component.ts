import { Component, ElementRef, Input, OnInit, ViewChild } from '@angular/core';
import { SubjectStore } from 'src/app/services/subject-store.service';
import { ServiceSubject } from 'src/app/models/service-subject.model';
import { Router } from '@angular/router';
@Component({
  selector: 'app-manage-subject',
  templateUrl: './manage-subject.component.html',
  styleUrls: ['./manage-subject.component.css']
})
export class ManageSubjectComponent implements OnInit {
  @Input() subjectId: string;
  @ViewChild('file') cdsfile: ElementRef;
  subject: ServiceSubject = new ServiceSubject();
  confirm: Boolean = false;
  constructor(private subjectStore: SubjectStore, private router: Router) {}
  ngOnInit(): void {
    this.subjectStore.get(this.subjectId).subscribe((subject) => {
      this.subject = subject;
    })
  }
  delete() {
    this.subjectStore.deleteSubject(this.subject).subscribe(() => {
      this.router.navigate(['/app/maintenance'])
    })
  }
  submit() {
    this.subjectStore.updateSubject(this.subject).subscribe(() => {
      this.router.navigate(["/app/maintenance"])
    })
  }
  changeListener($event): void {
    this.cdsfile.nativeElement.setAttribute("status", "neutral")
    let file: File = $event.target.files[0];
    let reader: FileReader = new FileReader();
    reader.onloadend = (e) => {
        this.subject.thumbnail = reader.result.toString();
        this.cdsfile.nativeElement.setAttribute("status", "success")
    }

    reader.readAsDataURL(file);
  }
}
