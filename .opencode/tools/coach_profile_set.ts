import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description:
    "Create or update the user profile (validated, versioned — a new row is appended, goal changes are audited). " +
    "Args: the full UserProfile object: {display_name?, goals: [{kind, physique_target?, target_muscles?, metric?, deadline?, notes?}], " +
    "training_age?, days_per_week?, session_length_min?, equipment_access?, priority_muscles?, liked_exercises?, disliked_exercises?}. " +
    "goal.kind one of: hypertrophy, strength, powerlifting, general_fitness, fat_loss, rehab_support. " +
    "physique_target one of: ripped, athletic, bulky. training_age one of: novice, intermediate, advanced. " +
    "equipment_access one of: full_gym, home, minimal. Echo the profile to the user for confirmation after setting.",
  args: {
    profile: tool.schema.record(tool.schema.string(), tool.schema.any()),
  },
  async execute(args) {
    const py = path.join(process.cwd(), ".venv", "Scripts", "python.exe").replace(/\\/g, "/")
    const script = path.join(process.cwd(), "coach_tools.py").replace(/\\/g, "/")
    const result = await Bun.$`${py} ${script} profile_set ${JSON.stringify(args.profile)}`.text()
    return result.trim()
  },
})
