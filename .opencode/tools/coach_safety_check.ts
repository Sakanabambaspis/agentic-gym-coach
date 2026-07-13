import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description:
    "Check whether an exercise is contraindicated against the user's current injury_status. " +
    "Deterministic — if safe=false, never suggest that exercise; offer alternatives verbatim.",
  args: {
    exercise: tool.schema.string().describe("Exercise name to check (canonical or raw log alias)"),
  },
  async execute(args) {
    const py = path.join(process.cwd(), ".venv", "Scripts", "python.exe").replace(/\\/g, "/")
    const script = path.join(process.cwd(), "coach_tools.py").replace(/\\/g, "/")
    const result = await Bun.$`${py} ${script} safety_check ${JSON.stringify(args)}`.text()
    return result.trim()
  },
})