import express from "express";
import morgan from "morgan";
import cors from "cors";
import { connectDB, url } from "./db.js";
import { PrivateRouter, PublicRouter }  from "./routes.js";
import cookieParser from "cookie-parser"
import session from 'express-session';
import MongoStore from 'connect-mongo'
import passport from "passport";

process.on( 'unhandledRejection', ( error, promise ) => {
  console.log( 'UPR: ' + promise + ' with ' + error )
  console.log( error.stack )
} )
process.on('uncaughtException', function(err) {
  console.error(err);
});
const app = express();
app.use(session({
  secret: 'keyboard cat',
  resave: false,
  saveUninitialized: false,
  store: new MongoStore({
    mongoUrl: url,
    ttl: 14 * 24 * 60 * 60,
    autoRemove: 'native' 
})}))

app.use(express.json({limit: '50mb'}));
app.use(express.urlencoded({limit: '50mb'}));
app.use(morgan("dev"));
app.use(cookieParser())

app.use(cors());

app.set('json spaces', 4);
app.use("/api/login", PublicRouter)

app.use("/api", PrivateRouter);

app.all("*", (req, res) => {
  res.status(404).json({
    status: "fail",
    message: `Route: ${req.originalUrl} does not exist on this server`,
  });
});
app.use((err, req, res, next) => {
  console.error(err.stack)
  res.status(500).send('Something broke!')
})
const PORT = 8000;
app.listen(PORT, async () => {
    console.log("🚀Server started Successfully");
    await connectDB()
});