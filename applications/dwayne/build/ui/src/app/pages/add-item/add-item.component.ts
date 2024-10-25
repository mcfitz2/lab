import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Item } from 'src/app/models/item.model';
import { User } from 'src/app/models/user.model';
import { ItemStore } from 'src/app/services/item-store.service';
import { SubjectStore } from 'src/app/services/subject-store.service';
import { UserService } from 'src/app/services/user.service';
import { Location } from 'src/app/models/location.model';

@Component({
  selector: 'app-add-item',
  templateUrl: './add-item.component.html',
  styleUrls: ['./add-item.component.css']
})
export class AddItemComponent implements OnInit {
  item: Item = new Item();
  user: User = new User();
  loading: Boolean = false;
  constructor(private itemStore: ItemStore, private userService: UserService, private router: Router) {}
  ngOnInit(): void {
    this.userService.self().subscribe((user) => {
      this.user = user;
      this.item.locations = this.user.locations.map((name) => {
        let l = new Location()
        l.name = name;
        l.quantityHave = 0;
        l.quantityNeed = 0;
        return l;
      })
    })
  }
  updateShelfLife(value, unit, neverExpires) {
    if (neverExpires) {
      this.item.shelfLife = -1
      this.item.expirationDate = null;
    } else {
      this.item.shelfLife = value*unit;
      this.item.expirationDate = new Date(new Date().getTime() + (this.item.shelfLife * 24*60*60*1000))
    }
  }
  submit() {
    this.loading = true;
    this.itemStore.create(this.item).subscribe(() => {
      this.loading = false;
      this.router.navigate(["/app/inventory"])
    })
  }
}