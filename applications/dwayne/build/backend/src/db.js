import mongoose, { mongo } from "mongoose";
import mongodb from 'mongodb'
const url = process.env.MONGO_URL || "mongodb://user:pass@127.0.01/test?authSource=admin"
async function connectDB() {
  await mongoose.connect(url);
}
function getBucket() {
  let client = mongoose.connection.getClient()
  let db = client.db('test');
 return new mongodb.GridFSBucket(db, {bucketName: "files"});
}


export { getBucket, connectDB, url };