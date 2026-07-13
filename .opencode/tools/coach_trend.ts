import { tool } from "@opencode-ai/plugin"
import path from "path"

const MUSCLES = [
  "side_delt", "rear_delt", "upper_chest", "mid_back", "lats",
  "biceps", "triceps", "quads", "hamstrings", "glutes",
  "core", "calves", "serratus",
].join(", ")

export default tool({
  description:
    "Get 4-week (default) trend for a muscle group: effective volume (with form_quality<3 50% discount " +
    "applied), average RPE, Epley 1RM estimate, stall detection, session count in window.",
  args: {
    muscle: tool.schema.string().describe(`One of: ${MUSCLES}`),
    window_days: tool.schema.number().int().min(1).max(365).default(28),
    end_date: tool.schema.string().optional().describe("YYYY-MM-DD anchor; defaults to today"),
  },
  async execute(args) {
    const py = path.join(process.cwd(), ".venv", "Scripts", "python.exe").replace(/\\/g, "/")
    const script = path.join(process.cwd(), "coach_tools.py").replace(/\\/g, "/")
    const result = await Bun.$`${py} ${script} trend ${JSON.stringify(args)}`.text()
    return result.trim()
  },
})