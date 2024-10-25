import { Injectable, OnInit } from '@angular/core';
import { Item } from '../models/item.model';
import {BehaviorSubject, Observable, firstValueFrom, throwError} from 'rxjs'
import {List} from 'immutable';
import { HttpClient } from '@angular/common/http';
import { User } from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class UserService implements OnInit {
  constructor(private http: HttpClient) { 
  }
  ngOnInit(): void {
  }
  self(): Observable<User> {
    return this.http.get<User>(`/api/users/self`);
  }
  update(user: User): Observable<User> {
    return this.http.patch<User>(`/api/users/${user._id}`, user)
  }
}

