import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { CdsModule } from '@cds/angular';

import { AppComponent } from './app.component';
import { FormsModule } from '@angular/forms';
import { MaintenanceDashboardComponent } from './pages/maintenance-dashboard/maintenance-dashboard.component';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { SubjectCardComponent } from './components/subject-card/subject-card.component';
import { ClarityModule } from "@clr/angular";
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { ServiceTaskDatagridComponent } from './components/service-task-datagrid/service-task-datagrid.component';
import { RecurringServiceTaskDatagridComponent } from './components/recurring-service-task-datagrid/recurring-service-task-datagrid.component';
import { RouterModule, Routes, provideRouter, withComponentInputBinding } from '@angular/router';
import { InventoryDashboardComponent } from './pages/inventory-dashboard/inventory-dashboard.component';
import { LoggedInWrapperComponent } from './components/logged-in-wrapper/logged-in-wrapper.component';
import { LoginComponent } from './pages/login/login.component';
import { AuthInterceptor } from './auth.interceptor';
import { AddItemComponent } from './pages/add-item/add-item.component';
import '@cds/core/icon/register.js';
import { ClarityIcons, angleIcon, plusIcon, timesIcon } from '@cds/core/icon';
import '@cds/core/file/register.js';
import { PageWrapperComponent } from './components/page-wrapper/page-wrapper.component';
import { ManageSubjectComponent } from './pages/manage-subject/manage-subject.component';
import { AddTaskComponent } from './pages/add-task/add-task.component';
import { AddRecurringTaskComponent } from './pages/add-recurring-task/add-recurring-task.component';
import { CompleteTaskComponent } from './pages/complete-task/complete-task.component';
import { AddSubjectComponent } from './pages/add-subject/add-subject.component';
import { EditTaskComponent } from './pages/edit-task/edit-task.component';
import { EditRecurringTaskComponent } from './pages/edit-recurring-task/edit-recurring-task.component';
import { ManageLocationsComponent } from './pages/manage-locations/manage-locations.component';
import { EditItemComponent } from './pages/edit-item/edit-item.component';
import { OrderPageComponent } from './pages/order-page/order-page.component';
import { SafePipe } from './utils/safe-pipe';
ClarityIcons.addIcons(angleIcon, plusIcon, timesIcon);
const routes: Routes = [
  { path: 'login', component: LoginComponent},
  { path: 'app', 
    component: LoggedInWrapperComponent, 
    children: [
      { path: 'inventory', 
        component: InventoryDashboardComponent, 
      },
      { 
        path: 'inventory/create-item', 
        component: AddItemComponent 
      },
      { 
        path: 'inventory/manage-locations', 
        component: ManageLocationsComponent 
      },
      { path: 'maintenance', 
        component: MaintenanceDashboardComponent 
      },
      { path: 'maintenance/subject/:subjectId', 
        component: ManageSubjectComponent 
      },
      { path: 'inventory/item/:itemId', 
        component: EditItemComponent 
      },
      { path: 'maintenance/create-subject', 
        component: AddSubjectComponent 
      },
      { path: 'maintenance/subject/:subjectId/add-task', 
        component: AddTaskComponent 
      },
      { path: 'maintenance/subject/:subjectId/add-recurring-task', 
        component: AddRecurringTaskComponent 
      },
      { path: 'maintenance/subject/:subjectId/complete-task/:taskName', 
        component: CompleteTaskComponent 
      },
      { path: 'maintenance/subject/:subjectId/edit-recurring-task/:taskName', 
        component: EditRecurringTaskComponent 
      },
      { path: 'maintenance/subject/:subjectId/edit-task/:taskName', 
        component: EditTaskComponent 
      },
      { path: 'inventory/order/:itemId', 
        component: OrderPageComponent 
      },

  ]
  },
  { path: '', redirectTo: '/app/maintenance', pathMatch: 'full' },
]

@NgModule({
  declarations: [
    AppComponent,
    MaintenanceDashboardComponent,
    SubjectCardComponent,
    ServiceTaskDatagridComponent,
    RecurringServiceTaskDatagridComponent,
    InventoryDashboardComponent,
    LoggedInWrapperComponent,
    LoginComponent,
    AddItemComponent,
    PageWrapperComponent,
    ManageSubjectComponent,
    AddTaskComponent,
    AddRecurringTaskComponent,
    CompleteTaskComponent,
    AddSubjectComponent,
    EditTaskComponent,
    EditRecurringTaskComponent,
    ManageLocationsComponent,
    EditItemComponent,
    OrderPageComponent,
    SafePipe
  ],
  imports: [
    BrowserModule,
    FormsModule,
    HttpClientModule,
    ClarityModule,
    BrowserAnimationsModule,
    CdsModule,
    RouterModule
  ],
  providers: [
    provideRouter(routes, withComponentInputBinding()), 
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true
    }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
