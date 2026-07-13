import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description:
    "Compute the heuristic recovery score (0-100) for a given date. " +
    "0-59 = should rest, 60-84 = may train light, 85+ = may train. " +
    "Considers pain events, 7-day set volume, back-to-back training days, days since last session.",
  args: {
    date: tool.schema.string().describe("YYYY-MM-DD. Defaults to today if omitted."),
  },
  async execute(args) {
    const py = path.join(process.cwd(), ".venv", "Scripts", "python.exe").replace(/\\/g, "/")
    const script = path.join(process.cwd(), "coach_tools.py").replace(/\\/g, "/")
    const result = await Bun.$`${py} ${script} recovery ${JSON.stringify(args)}`.text()
    return result.trim()
  },
})