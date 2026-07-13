import { tool } from "@opencode-ai/plugin"
import path from "path"

const LOCATIONS = "left_elbow, right_elbow, left_knee, right_knee, lower_back, none"
const STATES = "active, resolving, resolved, chronic_baseline"

export default tool({
  description:
    "Insert / update an injury_status row. Use ONLY when the user explicitly reports a new injury or state change. " +
    `location one of: ${LOCATIONS}. ` +
    `status one of: ${STATES}.`,
  args: {
    location: tool.schema.string().describe(`Pain location. One of: ${LOCATIONS}`),
    status: tool.schema.string().describe(`Injury state. One of: ${STATES}`),
    severity: tool.schema.number().int().min(0).max(10).describe("Pain severity 0-10"),
    contraindicated_exercises: tool.schema.array(tool.schema.string()).default([])
      .describe("Canonical exercise names to ban while this injury is active/resolving"),
    safe_alternatives: tool.schema.array(tool.schema.string()).default([])
      .describe("Canonical exercise names that are tendon-friendly alternatives"),
  },
  async execute(args) {
    const py = path.join(process.cwd(), ".venv", "Scripts", "python.exe").replace(/\\/g, "/")
    const script = path.join(process.cwd(), "coach_tools.py").replace(/\\/g, "/")
    const result = await Bun.$`${py} ${script} injuries_seed ${JSON.stringify(args)}`.text()
    return result.trim()
  },
})