import { Injectable, OnInit } from '@angular/core';
import { Item } from '../models/item.model';
import {BehaviorSubject, Observable, firstValueFrom, throwError} from 'rxjs'
import {List} from 'immutable';
import { HttpClient } from '@angular/common/http';
import { map, take } from 'rxjs/operators';
@Injectable({
  providedIn: 'root'
})
export class ItemStore implements OnInit {
  private _items: BehaviorSubject<Item[]> = new BehaviorSubject([]);
  public readonly items: Observable<Item[]> = this._items.asObservable();

  constructor(private http: HttpClient) { 
      this.loadInitialData().subscribe()
  }
  ngOnInit(): void {
  }

  private buildUrl(id: string) {
    return `/api/items/${id}`;
  }
  getAll(): Observable<Item[]> {
    return this.http.get<Item[]>("/api/items");
  }
  get(id: string): Observable<Item> {
    return this.http.get<Item>(`/api/items/${id}`);
  }
  update(updated: Item): Observable<Item> {
    let obs = this.http.patch<Item>(this.buildUrl(updated._id), updated);
    return obs.pipe(map((updated) => {
      let current = this._items.getValue()
      let index = current.findIndex((item: Item) => updated._id === item._id);
      let item:Item = current[index];
      current[index] = item;
      this._items.next(current);
      return updated;
    }))
  }
  delete(deleted: Item): Observable<Item> {
    let obs = this.http.delete<Item>(this.buildUrl(deleted._id))
    console.log("deleting", deleted);
    return obs.pipe(map((deleted) => {
      console.log(deleted)
      let current = this._items.getValue()
        let index = current.findIndex((item: Item) => deleted._id === item._id);
          let item:Item = current[index];
          delete current[index];
          this._items.next(current);
          return deleted;
    }))
  }

  create(item: Item): Observable<Item> {
    let obs = this.http.post<Item>('/api/items', item)
    return obs.pipe(map((created) => {
        let current = this._items.getValue()
        current.push(item)
        this._items.next(current)
        return created;
    }))
  }

  loadInitialData(): Observable<Item[]> {
    let obs: Observable<Item[]> = this.getAll()
    return obs.pipe(map(
      items => {
                this._items.next(items);
                return items;
            }
        ));


  }
}

