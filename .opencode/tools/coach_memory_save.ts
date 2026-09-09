import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description:
    "Save a long-term memory note (Tier 3). ONLY call this on an explicit user command ('save this', 'remember this') — never auto-write. " +
    "Args: {text, kind?, tags?}. kind one of: preference, lesson, milestone, observation (default observation).",
  args: {
    text: tool.schema.string().describe("The note content, in the user's words where possible."),
    kind: tool.schema.string().optional().describe("preference | lesson | milestone | observation"),
    tags: tool.schema.array(tool.schema.string()).optional(),
  },
  async execute(args) {
    const py = path.join(process.cwd(), ".venv", "Scripts", "python.exe").replace(/\\/g, "/")
    const script = path.join(process.cwd(), "coach_tools.py").replace(/\\/g, "/")
    const result = await Bun.$`${py} ${script} memory_save ${JSON.stringify(args)}`.text()
    return result.trim()
  },
})
