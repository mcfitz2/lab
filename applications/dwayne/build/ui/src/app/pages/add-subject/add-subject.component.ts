import { Component, ElementRef, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { ServiceSubject } from 'src/app/models/service-subject.model';
import { SubjectStore } from 'src/app/services/subject-store.service';

@Component({
  selector: 'app-add-subject',
  templateUrl: './add-subject.component.html',
  styleUrls: ['./add-subject.component.css']
})
export class AddSubjectComponent {
  subject: ServiceSubject = new ServiceSubject();
  @ViewChild("file") cdsfile: ElementRef;
  constructor(private subjectStore: SubjectStore, private router: Router) {

  }
  ngOnInit(): void {
   
  }
  submit() {
    this.subjectStore.createSubject(this.subject).subscribe(() => {
      this.router.navigate(['/app/maintenance'])
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
