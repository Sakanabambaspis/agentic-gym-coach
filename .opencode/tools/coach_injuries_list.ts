import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description:
    "Read the current injury_status table. Returns pain_location, state, exercises_to_avoid, notes, started_on. " +
    "Coach calls this on first interaction of a session.",
  args: {},
  async execute() {
    const py = path.join(process.cwd(), ".venv", "Scripts", "python.exe").replace(/\\/g, "/")
    const script = path.join(process.cwd(), "coach_tools.py").replace(/\\/g, "/")
    const result = await Bun.$`${py} ${script} injuries_list {}`.text()
    return result.trim()
  },
})