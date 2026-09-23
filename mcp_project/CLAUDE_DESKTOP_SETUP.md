# Lesson 8: Connecting Claude Desktop to these MCP servers

Claude Desktop (and other MCP-compliant apps) can connect to the same
servers built in this project — `research`, `fetch`, and `filesystem` —
without needing the custom `mcp_chatbot.py` client or an Anthropic API key.

## Config location (macOS)

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

In the app: **Settings → Developer → Edit Config** opens this same file.

## `mcpServers` block

```json
{
  "mcpServers": {
    "research": {
      "command": "uv",
      "args": ["--directory", "/Users/kuldeeppurohit/mcp-server/mcp_project", "run", "research_server.py"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/kuldeeppurohit/mcp-server/mcp_project"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["--with", "mcp<2", "mcp-server-fetch"]
    }
  }
}
```

Merge this into the existing config's top level (alongside any other keys
the app already has) rather than replacing the whole file.

**Why the absolute `--directory` path for `research`:** Claude Desktop
launches the server from its own working directory, not this project's, so
`research_server.py` needs an explicit path to find itself and its `papers/`
output folder.

## Applying changes

Fully quit Claude Desktop (Cmd+Q, not just close the window) and reopen it
so it picks up the new config and starts the servers. Connected servers'
tools then show up in the chat's tool/attachment menu.
