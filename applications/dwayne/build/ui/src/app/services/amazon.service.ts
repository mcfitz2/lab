import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, map } from 'rxjs';
import { OrderInfo } from '../models/order-info.model';

@Injectable({
  providedIn: 'root'
})
export class AmazonService {

  constructor(private http: HttpClient) { 

  }
  getProductInfo(url: string): Observable<OrderInfo> {
    return this.http.post<OrderInfo>('/api/product-info', {url: url});
  }
}
