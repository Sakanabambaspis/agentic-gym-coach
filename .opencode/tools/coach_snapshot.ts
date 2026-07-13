import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description:
    "Generate / refresh the current 4-week phase snapshot. " +
    "Returns phase, specialization 1RMs, tendon summary, and a templated insight / next-phase adjustment.",
  args: {},
  async execute() {
    const py = path.join(process.cwd(), ".venv", "Scripts", "python.exe").replace(/\\/g, "/")
    const script = path.join(process.cwd(), "coach_tools.py").replace(/\\/g, "/")
    const result = await Bun.$`${py} ${script} snapshot {}`.text()
    return result.trim()
  },
})