import mongoose from "mongoose";
const sensor=new mongoose.Schema({name:String,value:Number,unit:String,source:String,recordedAt:{type:Date,default:Date.now}},{_id:false});
const schema=new mongoose.Schema({equipmentId:{type:mongoose.Schema.Types.ObjectId,ref:"Equipment",required:true},description:{type:String,required:true},operatingEvents:[String],sensorReadings:[sensor],thresholdChecks:{type:Array,default:[]},conflicts:{type:Array,default:[]},aiAnalysis:{type:Object,default:null}},{timestamps:true});
export default mongoose.model("Issue",schema);
