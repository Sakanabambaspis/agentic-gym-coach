import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description:
    "Log a new training session to the canonical DuckDB store. Args: date (YYYY-MM-DD), " +
    "exercises (array of {name, sets, reps[], rpe?, weight_kg?, tempo?, form_quality?, pain_flag?, notes?}), " +
    "phase?, post_feedback?. The skill canonicalizes exercise names and raises anomaly_flags " +
    "for pain/form issues automatically.",
  args: {
    payload: tool
      .schema
      .object({
        date: tool.schema.string().describe("YYYY-MM-DD"),
        exercises: tool
          .schema
          .array(
            tool.schema.object({
              name: tool.schema.string(),
              sets: tool.schema.number().min(1),
              reps: tool.schema.array(tool.schema.number().nullable()).default([]),
              rpe: tool.schema.array(tool.schema.number().nullable()).default([]),
              weight_kg: tool.schema.array(tool.schema.number().nullable()).default([]),
              form_quality: tool.schema.number().min(1).max(5).default(5),
              pain_flag: tool.schema.boolean().default(false),
              tempo: tool.schema.string().optional(),
              notes: tool.schema.string().optional(),
            }),
          )
          .min(1),
        phase: tool.schema.string().optional(),
        post_feedback: tool.schema.string().optional(),
      })
      .describe("Session payload"),
  },
  async execute(args) {
    const py = path.join(process.cwd(), ".venv", "Scripts", "python.exe").replace(/\\/g, "/")
    const script = path.join(process.cwd(), "coach_tools.py").replace(/\\/g, "/")
    const result = await Bun.$`${py} ${script} log_session ${JSON.stringify(args.payload)}`.text()
    return result.trim()
  },
})