import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description:
    "Search long-term memory notes (case-insensitive substring + any-tag match). " +
    "Args: {query?, tags?, limit?}. Use before personalizing advice or answering 'what do you remember about...' questions.",
  args: {
    query: tool.schema.string().optional().describe("Substring to match in note text."),
    tags: tool.schema.array(tool.schema.string()).optional().describe("Notes matching ANY tag are returned."),
    limit: tool.schema.number().optional().describe("Max notes (default 20)."),
  },
  async execute(args) {
    const py = path.join(process.cwd(), ".venv", "Scripts", "python.exe").replace(/\\/g, "/")
    const script = path.join(process.cwd(), "coach_tools.py").replace(/\\/g, "/")
    const result = await Bun.$`${py} ${script} memory_search ${JSON.stringify(args)}`.text()
    return result.trim()
  },
})
