import express from "express";
import Equipment from "../models/Equipment.js";
const r=express.Router();
r.get("/",async(req,res)=>{try{res.json(await Equipment.find().sort({updatedAt:-1}))}catch(e){res.status(500).json({error:e.message})}});
r.post("/",async(req,res)=>{try{res.status(201).json(await Equipment.create({type:req.body.type,identifier:req.body.identifier}))}catch(e){res.status(400).json({error:e.message})}});
export default r;
