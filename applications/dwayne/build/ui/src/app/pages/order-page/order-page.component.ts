import { Component, Input } from '@angular/core';
import { Router } from '@angular/router';
import { Item } from 'src/app/models/item.model';
import { ItemStore } from 'src/app/services/item-store.service';
import { UserService } from 'src/app/services/user.service';

@Component({
  selector: 'app-order-page',
  templateUrl: './order-page.component.html',
  styleUrls: ['./order-page.component.css']
})
export class OrderPageComponent {
  @Input() itemId: string;
  item: Item = new Item()
  constructor(private itemStore: ItemStore, private userService: UserService, private router: Router) {}
  ngOnInit(): void {
    this.itemStore.get(this.itemId).subscribe((item) => {
     this.item = item;
    })
  }
}
