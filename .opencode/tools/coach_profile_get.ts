import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description:
    "Get the current user profile (goals, training age, schedule, equipment, priority muscles, preferences). " +
    "Returns {profile: null} when no profile exists — run onboarding and collect it with coach_profile_set.",
  args: {},
  async execute(args) {
    const py = path.join(process.cwd(), ".venv", "Scripts", "python.exe").replace(/\\/g, "/")
    const script = path.join(process.cwd(), "coach_tools.py").replace(/\\/g, "/")
    const result = await Bun.$`${py} ${script} profile_get ${JSON.stringify(args)}`.text()
    return result.trim()
  },
})
