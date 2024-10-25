import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-page-wrapper',
  templateUrl: './page-wrapper.component.html',
  styleUrls: ['./page-wrapper.component.css']
})
export class PageWrapperComponent {
  @Input() headerText: string;

}
