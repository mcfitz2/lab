import { Component } from '@angular/core';
import '@cds/core/icon/register.js';
import { ClarityIcons, angleIcon } from '@cds/core/icon';
import '@cds/core/file/register.js';
ClarityIcons.addIcons(angleIcon);
@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'ui';
}
