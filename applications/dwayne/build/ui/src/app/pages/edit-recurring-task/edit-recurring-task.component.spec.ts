import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EditRecurringTaskComponent } from './edit-recurring-task.component';

describe('EditRecurringTaskComponent', () => {
  let component: EditRecurringTaskComponent;
  let fixture: ComponentFixture<EditRecurringTaskComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [EditRecurringTaskComponent]
    });
    fixture = TestBed.createComponent(EditRecurringTaskComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
