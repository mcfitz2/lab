import { Injectable, OnInit } from '@angular/core';
import { ServiceSubject } from '../models/service-subject.model';
import { BehaviorSubject, Observable, firstValueFrom, map, take, throwError } from 'rxjs'
import { List } from 'immutable';
import { RecurringService } from '../models/recurring-service.model';
import { ServiceTask } from '../models/service-task.model';
import { HttpClient } from '@angular/common/http';
import { Document } from "../models/document.model"
@Injectable({
  providedIn: 'root'
})
export class SubjectStore implements OnInit {
  private _subjects: BehaviorSubject<List<ServiceSubject>> = new BehaviorSubject(List([]));
  public readonly subjects: Observable<List<ServiceSubject>> = this._subjects.asObservable();

  constructor(private http: HttpClient) {
    this.loadInitialData().subscribe()
  }
  ngOnInit(): void {
  }

  private buildUrl(id: string) {
    return `/api/subjects/${id}`;
  }
  getAll(): Observable<ServiceSubject[]> {
    return this.http.get<ServiceSubject[]>("/api/subjects");
  }
  get(id: string): Observable<ServiceSubject> {
    return this.http.get<ServiceSubject>(`/api/subjects/${id}`);
  }
  update(id: string, subject: ServiceSubject): Observable<ServiceSubject> {
    return this.http.patch<ServiceSubject>(this.buildUrl(id), subject);
  }
  delete(id: string): Observable<ServiceSubject> {
    return this.http.delete<ServiceSubject>(this.buildUrl(id));
  }
  create(subject: ServiceSubject): Observable<ServiceSubject> {
    return this.http.post<ServiceSubject>("/api/subjects", subject);
  }


  loadInitialData(): Observable<ServiceSubject[]> {
    let obs: Observable<ServiceSubject[]> = this.getAll()
    return obs.pipe(map(
      res => {
        let subjects = (<ServiceSubject[]>res)
        this._subjects.next(List(subjects));
        console.log("ST", this._subjects, this.subjects)
        return subjects;
      }
    ));
  }
  updateSubject(updated: ServiceSubject): Observable<ServiceSubject> {
    let obs: Observable<ServiceSubject> = this.update(updated._id, updated);

    return obs.pipe(map(
      res => {
        let subjects = this._subjects.getValue();
        let index = subjects.findIndex((subject: ServiceSubject) => subject._id === updated._id);
        let subject: ServiceSubject = subjects.get(index);
        this._subjects.next(subjects.set(index, updated));
        return updated;
      }
    ));
  }
  createSubject(created: ServiceSubject): Observable<ServiceSubject> {
    let obs: Observable<ServiceSubject> = this.create(created)
    return obs.pipe(map(
      res => {
        let subjects = this._subjects.getValue();
        this._subjects.next(subjects.push(created));
        return created;
      }))
  }
  deleteSubject(deleted: ServiceSubject): Observable<ServiceSubject> {
    let obs: Observable<ServiceSubject> = this.delete(deleted._id);

    return obs.pipe(map(
      res => {
        let subjects = this._subjects.getValue();
        let index = subjects.findIndex((subject: ServiceSubject) => subject._id === deleted._id);
        delete subjects[index]
        this._subjects.next(subjects);
        return deleted;
      }
    ));
  }
  addRecurringTask(subject: ServiceSubject, task: RecurringService): Observable<ServiceSubject> {
    subject.recurringTasks.push(task);
    return this.updateSubject(subject)
  }
  addTask(subject: ServiceSubject, task: ServiceTask): Observable<ServiceSubject> {
    subject.tasks.push(task);
    return this.updateSubject(subject)
  }
  deleteTask(subject: ServiceSubject, deleted: ServiceTask): Observable<ServiceSubject> {
    let index = subject.tasks.findIndex((task: ServiceTask) => task._id === deleted._id);
    subject.tasks.splice(index, 1);
    return this.updateSubject(subject)
  }
  deleteRecurringTask(subject: ServiceSubject, deleted: RecurringService): Observable<ServiceSubject> {
    let index = subject.recurringTasks.findIndex((task: RecurringService) => task._id === deleted._id);
    subject.recurringTasks.splice(index, 1);
    return this.updateSubject(subject)
  }
  completeTask(subject: ServiceSubject, completed: ServiceTask): Observable<ServiceSubject> {
    let index = subject.tasks.findIndex((task: ServiceTask) => task._id == completed._id)
    subject.tasks[index] = completed
    subject.tasks[index].completed = true
    if (subject.meterValue < completed.completedMeterValue) {
      subject.meterValue = completed.completedMeterValue;
    }
    return this.updateSubject(subject);
  }
  updateTask(subject: ServiceSubject, updated: ServiceTask): Observable<ServiceSubject> {
    let index = subject.tasks.findIndex((task: ServiceTask) => task._id == updated._id)
    subject.tasks[index] = updated
    return this.updateSubject(subject);
  }
  updateRecurringTask(subject: ServiceSubject, updated: RecurringService): Observable<ServiceSubject> {
    let index = subject.recurringTasks.findIndex((task: RecurringService) => task._id == updated._id)
    subject.recurringTasks[index] = updated
    return this.updateSubject(subject);
  }
  uploadFile(subject: ServiceSubject, form: FormData): Observable<ServiceSubject> {

    let name = form.get('name')
    let index = subject.documents.findIndex((doc: Document) => doc.name == name)
    if (index >= 0) {
      return throwError("Document already exists")
    }
    let obs: Observable<ServiceSubject> = this.http.post<ServiceSubject>(`${this.buildUrl(subject._id)}/upload`, form);
    return obs;
  }
  deleteFile(subject: ServiceSubject, document: Document): Observable<ServiceSubject> {
    let index = subject.documents.findIndex((doc: Document) => doc._id == document._id)
    subject.documents.splice(index, 1);
    return this.updateSubject(subject);
  }
}

