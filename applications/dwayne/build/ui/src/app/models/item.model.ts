import { Location } from "./location.model";
import { OrderInfo } from "./order-info.model";
export class Item {
    _id: string;
    name: string;
    category: string;
    confirm: boolean;
    orderInfo: OrderInfo = new OrderInfo();
    locations: Location[];
    shelfLife: number;
    expirationDate: Date;
    unit: string = "ea";
    status: string;
    restockCost: number;
    unitsNeeded: number;
    needsAttention: boolean; 
}




