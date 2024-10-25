import {ItemStore } from '../../services/item-store.service'
import { Component, OnInit } from '@angular/core';
import { List } from "immutable"
import {Item} from '../../models/item.model'
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs';
@Component({
  selector: 'app-inventory-dashboard',
  templateUrl: './inventory-dashboard.component.html',
  styleUrls: ['./inventory-dashboard.component.css']
})
export class InventoryDashboardComponent implements OnInit {
  items: Item[];
  constructor(public itemStore: ItemStore, private router:Router) {
    this.router.events
    .pipe(filter(value => value instanceof NavigationEnd))
    .subscribe((event:NavigationEnd) => {
      if (event.url == '/app/inventory') {
        this.itemStore.loadInitialData().subscribe();
        this.itemStore.items.subscribe((items) => {
          this.items = items
        });
      }
  });
  }
  delete(item) {
    this.itemStore.delete(item)
  }
  ngOnInit(): void {
    this.itemStore.items.subscribe((items) => {
      this.items = items
    });
  }
}