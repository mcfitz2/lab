import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class GptService {
  apiKey: string = "token"
  constructor() { }
}
