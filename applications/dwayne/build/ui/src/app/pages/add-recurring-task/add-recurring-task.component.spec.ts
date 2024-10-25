import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddRecurringTaskComponent } from './add-recurring-task.component';

describe('AddRecurringTaskComponent', () => {
  let component: AddRecurringTaskComponent;
  let fixture: ComponentFixture<AddRecurringTaskComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [AddRecurringTaskComponent]
    });
    fixture = TestBed.createComponent(AddRecurringTaskComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
