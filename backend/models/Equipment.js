import mongoose from "mongoose";
const schema=new mongoose.Schema({type:{type:String,required:true},identifier:{type:String,required:true,unique:true},maintenanceHistory:[{issueId:mongoose.Schema.Types.ObjectId,action:String,status:String,date:{type:Date,default:Date.now}}]},{timestamps:true});
export default mongoose.model("Equipment",schema);
