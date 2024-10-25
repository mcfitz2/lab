import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  email: String;
  password: String;
  constructor(private http: HttpClient, private router:Router) {

  }
  login() {
    this.http.post("/api/login", {email: this.email, password: this.password}, {withCredentials: true}).subscribe((res)=> {
      this.router.navigate(['app/maintenance']);
    })
  }
}
