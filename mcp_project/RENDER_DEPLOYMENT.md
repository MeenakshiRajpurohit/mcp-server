# Lesson 9 (optional): Deploying the remote server to Render

The `research` MCP server (SSE transport) is deployed as a live web service.

## Live URL

```
https://mcp-server-2avy.onrender.com/sse
```

Point any MCP client (Inspector, a chatbot's `sse_client`) at this URL to use
the `search_papers` / `extract_info` tools without running anything locally.

Quick test via the Inspector's CLI mode:

```
npx @modelcontextprotocol/inspector --cli https://mcp-server-2avy.onrender.com/sse --method tools/list
```

## Render service configuration

- **Repo:** this repo (`mcp-server`)
- **Root Directory:** `mcp_project` — required; without this Render builds
  from the repo root and can't find `research_server_remote.py`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python research_server_remote.py`
- **Instance Type:** Free

## Code changes needed for deployment

`research_server_remote.py` binds to Render's dynamic port instead of a
hardcoded one:

```python
mcp = FastMCP("research", host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))
```

`mcp_project/requirements.txt` was added alongside the `uv`-managed
`pyproject.toml`/`uv.lock`, since Render's native Python build uses `pip`.

## Note on free tier

Render's free instances spin down after inactivity and take a few seconds to
wake on the next request — expect a cold-start delay if it hasn't been hit
recently.
