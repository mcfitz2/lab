import { Component, OnInit } from '@angular/core';
import { ServiceSubject } from '../../models/service-subject.model';
import {timer, tap, takeUntil, switchMap, Subject, filter} from 'rxjs';
import { SubjectStore } from 'src/app/services/subject-store.service';
import { List } from "immutable"
import { NavigationEnd, Router } from '@angular/router';
@Component({
  selector: 'app-maintenance-dashboard',
  templateUrl: './maintenance-dashboard.component.html',
  styleUrls: ['./maintenance-dashboard.component.css'],
})

export class MaintenanceDashboardComponent implements OnInit {
  subjects: List<ServiceSubject>;
  constructor(private subjectStore: SubjectStore, private router: Router) {}
  ngOnInit(): void {
    this.subjectStore.subjects.subscribe(subjects => this.subjects = subjects)
    this.router.events
      .pipe(filter(value => value instanceof NavigationEnd))
      .subscribe((event:NavigationEnd) => {
        if (event.url == '/app/maintenance') {
          this.subjectStore.loadInitialData();
        }
    });
  }

  ngOnDestroy(): void {
  }
}
