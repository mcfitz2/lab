import { ObjectId } from "mongodb";
import { Schema, mongoose } from "mongoose";
import schedule from "node-schedule"

const units = [
     "in",
    "lb",
    "gal",
    "oz",
     "ea",
     "l",
    "meal",
     "dollar",
     "qt",
     "ft",
     "btl",
]

/***********************************************
 * Models
 ***********************************************/
const recurringTaskSchema = new Schema({
    name: String,
    meterInterval: Number,
    timeInterval: Number,
    notes: String,
}, {
    methods: {
        async getChildTasks() {
            return mongoose.model('Task').find({ parentTask: this._id })
        }
    }
})
mongoose.model('RecurringTask', recurringTaskSchema)
const taskSchema = new Schema({
    name: String,
    completedMeterValue: Number,
    completedDate: Date,
    completed: Boolean,
    notes: String,
    todoistId: String,
    dueDate: Date,
})
mongoose.model('Task', taskSchema)
const documentSchema = new Schema({
    name: String,
    gridId: ObjectId
})
mongoose.model('Document', documentSchema)

const serviceSubjectSchema = new Schema({
    brand: String,
    model: String,
    year: Number,
    meterValue: Number,
    meterUnit: String,
    type: String,
    thumbnail: String,

    tasks: [taskSchema],
    recurringTasks: [recurringTaskSchema],
    documents: [documentSchema],
    owner: {type: mongoose.Schema.Types.ObjectId, ref: 'User'},

}, {
    methods: {
        getCompletedTasksByName(name) {
            return this.tasks.filter((task) => task.name == name && task.completed)
        },
        alreadyPending(task) {
            for (const existingTask of this.tasks) {
                if (!existingTask.completed && existingTask.name == task.name) {
                    return true
                }
            }
            return false;
        }
    }, timestamps: true
})

serviceSubjectSchema.virtual('name').get(function () {
    return `${this.year} ${this.brand} ${this.model}`
});
serviceSubjectSchema.set('toJSON', { virtuals: true });
const userSchema = new Schema({
    todoistToken: String,
    todoistProjectId: String,
    email: String,
    units: [{
        long: String,
        short: String,
    }],
    locations: [String]
}, {
    methods: {
       
    }, 
    timestamps: true
})

let User = mongoose.model('User', userSchema)


const itemSchema = new Schema({
    category: {
        type: String,
    },
    name: String,
    packageSize: Number,
    shelfLife: Number,
    expirationDate: Date,
    locations: [{
        name: String,
        quantityHave: Number,
        quantityNeed: Number
    }],
    orderInfo: {
        retailer: String,
        url: String,
        retailerId: String,
        packageSize: Number,
        price: Number,
        unitPrice: Number
    }, 
    unit: {
        type: String, 
    }, 
    owner: {type: mongoose.Schema.Types.ObjectId, ref: 'User'},
}, {minimize:false, timestamps: true})
itemSchema.virtual('status').get(function () {

    let missing = this.locations.reduce((missing, location) => {
        if (location.quantityHave < location.quantityNeed) {
            missing[location.name] = location.quantityNeed - location.quantityHave
        }
        return missing;
    }, {})
    let locationsMissingItems = Object.keys(missing).length;
    let totalMissingItems = Object.values(missing).reduce((sum, quant) => {
        sum += quant;
        return sum;
    }, 0);
    if (locationsMissingItems > 1) {
        return `Missing ${totalMissingItems} ${this.unit} from ${locationsMissingItems} locations`
    } else if (locationsMissingItems == 1) {
        return `Missing ${totalMissingItems} ${this.unit} from ${Object.keys(missing)[0]}`
    } else if (locationsMissingItems == 0) {
        return "Fully Stocked"
    }
    return 
});
itemSchema.virtual('unitsNeeded').get(function () {

    let missing = this.locations.reduce((missing, location) => {
        if (location.quantityHave < location.quantityNeed) {
            missing[location.name] = location.quantityNeed - location.quantityHave
        }
        return missing;
    }, {})
    let locationsMissingItems = Object.keys(missing).length;
    let totalMissingItems = Object.values(missing).reduce((sum, quant) => {
        sum += quant;
        return sum;
    }, 0);
    
    return totalMissingItems;
});
itemSchema.virtual('restockCost').get(function () {
    if (this.orderInfo && this.unitsNeeded > 0) {
        return Math.ceil(this.unitsNeeded / this.orderInfo.packageSize) * this.orderInfo.price;
    } else if (this.unitsNeeded == 0) {
        return 0;
    }
    return null;
});
itemSchema.virtual('needsAttention').get(function () {
    let missing = this.locations.reduce((missing, location) => {
        if (location.quantityHave < location.quantityNeed) {
            missing[location.name] = location.quantityNeed - location.quantityHave
        }
        return missing;
    }, {})
    let locationsMissingItems = Object.keys(missing).length;
    if (locationsMissingItems > 0) {
        return true
    } else if (locationsMissingItems == 0) {
        return false
    } 
});
itemSchema.set('toJSON', { virtuals: true });

let Item = mongoose.model('Item', itemSchema)


/***********************************************
 * Hooks
 ***********************************************/

function meterIntervalPassed(subject, recurringTask) {
    let currentMeterReading = subject.meterValue;
    if (!recurringTask.meterInterval) {
        return false;
    }
    let tasks = subject.getCompletedTasksByName(recurringTask.name).filter((task) => {
        console.log(task.completedMeterValue, (currentMeterReading - recurringTask.meterInterval))
        return task.completedMeterValue > (currentMeterReading - recurringTask.meterInterval)
    })
    return tasks.length == 0
}
function timeIntervalPassed(subject, recurringTask) {


    let tasks = subject.getCompletedTasksByName(recurringTask.name).filter((task) => {
        return task.completedDate > new Date(new Date().getTime() - (recurringTask.timeInterval * 24*60*60*1000));
    })
    return tasks.length == 0
}
const ServiceSubject = mongoose.model("ServiceSubject", serviceSubjectSchema);

async function checkRecurringTasks(subject) {
    for (const recurringTask of subject.recurringTasks) {
        let task = {
            name: recurringTask.name,
            completed: false,
            notes: recurringTask.notes,
            parentTask: recurringTask,
            dueDate: new Date()
        }
        if (subject.alreadyPending(task)) {
            console.log("Recurring task already has a pending task, not creating a new one")
        } else {
            if (timeIntervalPassed(subject, recurringTask)) {
                console.log('Time interval has passed, adding pending task')
                subject.tasks.push(task);
                await subject.save()
            } else if (meterIntervalPassed(subject, recurringTask)) {
                console.log('Meter interval has passed, adding pending task')
                subject.tasks.push(task);
                await subject.save()
            } else {
                console.log("Task has been completed recently")
            }
        }
    }
    return Promise.resolve();
}
async function checkAllRecurringTasks() {
    let subjects = await ServiceSubject.find();
    for (let sub of subjects) {
        await checkRecurringTasks(sub);
    }
}



schedule.scheduleJob("* * * * *", async () => await checkAllRecurringTasks());

export { ServiceSubject, checkRecurringTasks, Item, User}