import mongoose from "mongoose";
const schema=new mongoose.Schema({issueId:{type:mongoose.Schema.Types.ObjectId,ref:"Issue",required:true},equipmentId:{type:mongoose.Schema.Types.ObjectId,ref:"Equipment",required:true},title:String,description:String,priority:String,status:{type:String,enum:["DRAFT","APPROVED","REJECTED"],default:"DRAFT"}},{timestamps:true});
export default mongoose.model("WorkOrder",schema);
