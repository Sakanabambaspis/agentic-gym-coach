import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description:
    "List recent training sessions (default 10, max 100). Returns id, date, phase, pre_recovery_score, post_feedback.",
  args: {
    limit: tool.schema.number().int().min(1).max(100).default(10),
  },
  async execute(args) {
    const py = path.join(process.cwd(), ".venv", "Scripts", "python.exe").replace(/\\/g, "/")
    const script = path.join(process.cwd(), "coach_tools.py").replace(/\\/g, "/")
    const result = await Bun.$`${py} ${script} sessions ${JSON.stringify(args)}`.text()
    return result.trim()
  },
})