import express from "express";
import {
    createServiceSubjectController,
    deleteServiceSubjectController,
    findAllServiceSubjectsController,
    findServiceSubjectController,
    updateServiceSubjectController,
//    uploadDocumentController,
//    downloadDocumentController
} from "./controllers/service-subject.controller.js";
import {
    createItemController,
    deleteItemController,
    findAllItemsController,
    findItemController,
    updateItemController,
} from "./controllers/item.controller.js";
import {
//    createUserController,
//    deleteUserController,
//    findAllUsersController,
    findUserController,
    updateUserController,
} from "./controllers/user.controller.js";
import { url } from './db.js'
import multer from 'multer'
import { GridFsStorage } from 'multer-gridfs-storage';
import { loginController } from "./controllers/auth.controller.js";
import passport from "passport";
import { getProductInfo } from "./controllers/product-info.controller.js";
export const PrivateRouter = express.Router();
export const PublicRouter = express.Router();

const storage = new GridFsStorage({ url: url });

// Set multer storage engine to the newly created object
const upload = multer({ storage });
PrivateRouter.use(passport.authenticate('session'));
PrivateRouter.use(passport.authenticate('jwt'))
PrivateRouter
    .route("/subjects")
    .get(findAllServiceSubjectsController)
    .post(createServiceSubjectController)

PrivateRouter
    .route("/subjects/:serviceSubjectId")
    .get(findServiceSubjectController)
    .delete(deleteServiceSubjectController)
    .patch(updateServiceSubjectController)

//PrivateRouter
//    .post("/subjects/:serviceSubjectId/upload", upload.single('file'), uploadDocumentController)
//PrivateRouter
//    .post("/subjects/:serviceSubjectId/documents/:documentId", downloadDocumentController)



PrivateRouter
    .route("/items")
    .get(findAllItemsController)
    .post(createItemController)

PrivateRouter
    .route("/items/:itemId")
    .get(findItemController)
    .delete(deleteItemController)
    .patch(updateItemController)
PrivateRouter
    .route("/users")
//    .get(findAllUsersController)
//    .post(createUserController)

PrivateRouter
    .route("/users/:userId")
    .get(findUserController)
//    .delete(deleteUserController)
    .patch(updateUserController)
PublicRouter
    .route("/")
    .post(loginController)

PrivateRouter
    .route("/product-info")
    .post(getProductInfo)