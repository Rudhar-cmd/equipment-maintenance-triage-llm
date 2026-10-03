import express from "express";
import axios from "axios";
import Issue from "../models/Issue.js";
import Equipment from "../models/Equipment.js";
import WorkOrder from "../models/WorkOrder.js";
import {
  runThresholdChecks,
  detectConflicts
} from "../services/thresholds.js";

const r = express.Router();



r.get("/", async (req, res) => {
  try {
    const issues = await Issue.find()
      .populate("equipmentId")
      .sort({ createdAt: -1 });

    res.json(issues);

  } catch (e) {
    res.status(500).json({
      error: e.message
    });
  }
});


// ============================================================
// Get single issue
// ============================================================

r.get("/:id", async (req, res) => {
  try {
    const issue = await Issue.findById(req.params.id)
      .populate("equipmentId");

    if (!issue) {
      return res.status(404).json({
        error: "Issue not found."
      });
    }

    res.json(issue);

  } catch (e) {
    res.status(400).json({
      error: e.message
    });
  }
});


// ============================================================
// Create issue
// ============================================================

r.post("/", async (req, res) => {
  try {

    const equipment = await Equipment.findById(
      req.body.equipmentId
    );

    if (!equipment) {
      return res.status(404).json({
        error: "Equipment not found."
      });
    }

    const readings = Array.isArray(req.body.sensorReadings)
      ? req.body.sensorReadings
      : [];

    const issue = await Issue.create({
      equipmentId: equipment._id,
      description: req.body.description,
      operatingEvents: req.body.operatingEvents || [],
      sensorReadings: readings,
      thresholdChecks: runThresholdChecks(readings),
      conflicts: detectConflicts(readings)
    });

    await Equipment.updateOne(
      { _id: equipment._id },
      {
        $push: {
          maintenanceHistory: {
            issueId: issue._id,
            action: "Issue reported",
            status: "OPEN"
          }
        }
      }
    );

    res.status(201).json(issue);

  } catch (e) {
    res.status(400).json({
      error: e.message
    });
  }
});


// ============================================================
// Analyze issue with Gemini AI service
// ============================================================

r.post("/:id/analyze", async (req, res) => {

  try {

    // --------------------------------------------------------
    // 1. Find issue
    // --------------------------------------------------------

    const issue = await Issue.findById(
      req.params.id
    ).populate("equipmentId");

    if (!issue) {
      return res.status(404).json({
        error: "Issue not found."
      });
    }


    // --------------------------------------------------------
    // 2. AI service URL
    // --------------------------------------------------------

    const aiServiceUrl =
      process.env.AI_SERVICE_URL ||
      "http://localhost:8002";


    console.log(
      "Calling AI service:",
      `${aiServiceUrl}/analyze`
    );


    // --------------------------------------------------------
    // 3. Send issue to FastAPI / Gemini
    // --------------------------------------------------------

    const ai = await axios.post(
      `${aiServiceUrl}/analyze`,
      {
        equipment: {
          type: issue.equipmentId.type,
          identifier: issue.equipmentId.identifier,
          maintenanceHistory:
            issue.equipmentId.maintenanceHistory
        },

        issue: {
          description: issue.description,
          operatingEvents: issue.operatingEvents,
          sensorReadings: issue.sensorReadings
        },

        thresholdChecks:
          issue.thresholdChecks,

        conflicts:
          issue.conflicts
      },
      {
        timeout: 60000
      }
    );


    // --------------------------------------------------------
    // 4. Get AI response
    // --------------------------------------------------------

    const analysis = ai.data;

    console.log(
      "AI analysis received successfully."
    );


    // --------------------------------------------------------
    // 5. Save AI analysis to issue
    // --------------------------------------------------------

    issue.aiAnalysis = analysis;

    await issue.save();


    // --------------------------------------------------------
    // 6. Create draft work order
    // --------------------------------------------------------
    //
    // Python returns:
    //
    // work_order_draft
    //
    // NOT:
    //
    // work_order
    //
    // --------------------------------------------------------

    if (analysis.work_order_draft) {

      const draft = analysis.work_order_draft;

      const workOrder = await WorkOrder.create({
        issueId: issue._id,

        equipmentId:
          issue.equipmentId._id,

        title:
          draft.title ||
          "Equipment maintenance inspection",

        description:
          draft.description ||
          "Inspect the reported equipment condition.",

        priority:
          analysis.priority || "MEDIUM",

        status: "DRAFT"
      });


      // Add MongoDB ID to response
      analysis.work_order_draft._id =
        workOrder._id.toString();


      // Save updated analysis
      issue.aiAnalysis = analysis;

      await issue.save();
    }


    // --------------------------------------------------------
    // 7. Return analysis to React
    // --------------------------------------------------------

    res.json(analysis);


  } catch (e) {

    // ========================================================
    // IMPORTANT DEBUGGING LOGGING
    // ========================================================

    console.error(
      "AI ANALYSIS ERROR:",
      e.message
    );


    // Axios received a response from FastAPI
    if (e.response) {

      console.error(
        "AI STATUS:",
        e.response.status
      );

      console.error(
        "AI RESPONSE:",
        e.response.data
      );
    }


    // Axios sent request but received no response
    if (e.request && !e.response) {

      console.error(
        "AI REQUEST WAS SENT BUT NO RESPONSE RECEIVED"
      );
    }


    // Axios configuration/request error
    if (!e.response && !e.request) {

      console.error(
        "AI REQUEST ERROR:",
        e
      );
    }


    // Return useful error to frontend
    res.status(502).json({
      error:
        e.response?.data?.detail ||
        e.response?.data?.error ||
        e.message ||
        "AI analysis service unavailable."
    });
  }
});


export default r;