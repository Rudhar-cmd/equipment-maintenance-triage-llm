import express from "express";
import WorkOrder from "../models/WorkOrder.js";
import Equipment from "../models/Equipment.js";
const r=express.Router();
r.patch("/:id",async(req,res)=>{
 try{
  if(!["APPROVED","REJECTED","DRAFT"].includes(req.body.status))return res.status(400).json({error:"Invalid work-order status."});
  const wo=await WorkOrder.findById(req.params.id); if(!wo)return res.status(404).json({error:"Work order not found."});
  wo.status=req.body.status; await wo.save();
  if(req.body.status==="APPROVED") await Equipment.updateOne({_id:wo.equipmentId},{$push:{maintenanceHistory:{issueId:wo.issueId,action:wo.description,status:"APPROVED"}}});
  res.json(wo);
 }catch(e){res.status(400).json({error:e.message})}
});
export default r;
