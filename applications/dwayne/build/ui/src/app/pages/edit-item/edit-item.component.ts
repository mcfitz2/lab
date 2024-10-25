import { Component, ElementRef, Input, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { Item } from 'src/app/models/item.model';
import { User } from 'src/app/models/user.model';
import { ItemStore } from 'src/app/services/item-store.service';
import { UserService } from 'src/app/services/user.service';
import { Location } from 'src/app/models/location.model'
import { OrderInfo } from 'src/app/models/order-info.model';
import { AmazonService } from 'src/app/services/amazon.service';
@Component({
  selector: 'app-edit-item',
  templateUrl: './edit-item.component.html',
  styleUrls: ['./edit-item.component.css']
})
export class EditItemComponent implements OnInit {
  @Input() itemId: string;
  item: Item = new Item();
  user: User = new User();
  @ViewChild("neverCheck") neverCheck: ElementRef;
  loading: Boolean = false;
  constructor(private itemStore: ItemStore, private userService: UserService, private router: Router, private amazonService: AmazonService) { }
  ngOnInit(): void {
    this.itemStore.get(this.itemId).subscribe((item) => {
      this.item = item;
      if (item.shelfLife == -1) {
        this.neverCheck.nativeElement.setAttribute("checked", true)
      }
      if (!this.item.orderInfo) {
        this.item.orderInfo = new OrderInfo();
      }
      this.userService.self().subscribe((user) => {
        let existing = this.item.locations.map((_) => _.name)
        for (let l of user.locations) {
          if (!existing.includes(l)) {
            let loc = new Location();
            loc.name = l;
            loc.quantityHave = 0;
            loc.quantityNeed = 0;
            this.item.locations.push(loc)
          }
        }
      })

    })
  }
  updateShelfLife(value, unit, neverExpires) {
    if (neverExpires) {
      this.item.shelfLife = -1
      this.item.expirationDate = null;
    } else {
      this.item.shelfLife = value * unit;
      this.item.expirationDate = new Date(new Date().getTime() + (this.item.shelfLife * 24 * 60 * 60 * 1000))
    }
  }
  async loadInfo() {
    if (this.item.orderInfo.url) {
      this.amazonService.getProductInfo(this.item.orderInfo.url).subscribe((oi) => {
        this.item.orderInfo.price = oi.price;
        this.item.orderInfo.retailer = oi.retailer;
        this.item.orderInfo.retailerId = oi.retailerId;
      });
    }
  }
  submit() {
    this.loading = true;
    this.itemStore.update(this.item).subscribe(() => {
      this.loading = false;
      this.router.navigate(["/app/inventory"])
    })
  }
}