import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { User } from 'src/app/models/user.model';
import { UserService } from 'src/app/services/user.service';

@Component({
  selector: 'app-manage-locations',
  templateUrl: './manage-locations.component.html',
  styleUrls: ['./manage-locations.component.css']
})
export class ManageLocationsComponent implements OnInit {
  user: User = new User();
  newName: string;
  constructor(private userService: UserService, private router:Router) {
    
  }
  ngOnInit(): void {
    this.userService.self().subscribe((user) => {
      this.user = user;
    })
  }
  submit() {
    this.userService.update(this.user).subscribe((user) => {
      this.router.navigate(["/app/inventory"])
    })
  }
  add() {
    this.user.locations.push(this.newName)
  }
  remove(location:string) {
    let index = this.user.locations.indexOf(location)
    this.user.locations.splice(index, 1)
    console.log(this.user.locations)
  }
}
