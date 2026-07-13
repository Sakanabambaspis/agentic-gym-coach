import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description:
    "Re-run the bulk markdown importer (scripts/ingest_log.py). Use ONLY when the user explicitly " +
    "asks to bulk-import historical logs from a markdown file. One-shot migration path.",
  args: {
    reset: tool.schema.boolean().default(false).describe("--reset flag re-imports from scratch"),
    path: tool.schema.string().optional().describe("markdown file path, defaults to docs/reference/sample_log.md"),
  },
  async execute(args) {
    const py = path.join(process.cwd(), ".venv", "Scripts", "python.exe").replace(/\\/g, "/")
    const importer = path.join(process.cwd(), "scripts", "ingest_log.py").replace(/\\/g, "/")
    const flag = args.reset ? "--reset" : ""
    const target = args.path || ""
    const cmd = ["log_session_dummy"].length ? [] : []
    void cmd
    const result = await Bun.$`${py} ${importer} ${flag} ${target}`.text()
    return result.trim()
  },
})