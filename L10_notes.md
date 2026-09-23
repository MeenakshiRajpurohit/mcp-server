# Lesson 10: The Road Ahead

Wrap-up lesson — no code, just where MCP is heading. Notes from the video.

## Authentication: OAuth 2.1

- Added in the March spec update as the standard way for clients to
  authenticate with **remote** servers.
- Flow: client requests → server requires user auth → token exchange →
  client makes authenticated requests to the server (and onward to the data
  source).
- Optional but strongly recommended for remote servers. Not needed for
  stdio servers (like `research_server.py` in this repo), which just use
  local environment variables instead.

## Client-side primitives: roots and sampling

So far this project only built **server**-side primitives (tools, resources,
prompts). MCP also defines primitives the **client** exposes to a server:

- **Roots** — a URI (often a filesystem path, but can be any URI including
  HTTP) that a client tells a server to scope its work to. Keeps a server
  focused and limits what it can touch — a security/scoping mechanism.
- **Sampling** — lets a *server* request LLM inference *from the client*,
  reversing the usual direction. Example: a server holding sensitive logs
  can ask the client's LLM to analyze them directly, instead of shipping
  all that raw data into the client's context window (better for both
  privacy and context-window budget).

## Composability: clients that are also servers

A single component can be both an MCP client and an MCP server at once.
This lets you build multi-agent architectures — an "agent" that serves
data to an application (as a server) while also calling out to other
specialized agents (as a client): e.g. a coding agent, a research agent,
and an analysis agent that all speak MCP to each other.

## Coming: the unified registry

A standardized way to discover, version, and verify MCP servers (similar
to npm/PyPI, but for MCP servers) — addressing both trust (avoiding
malicious servers) and dynamic discovery (an agent finding and installing
the right server on the fly via a well-known `mcp.json` file, similar to
OAuth's well-known discovery pattern).

## Other things in progress

- Smoother stateful/stateless transitions as more clients adopt Streamable
  HTTP.
- Tool/name collision handling as more servers get combined in one client.
- Broader adoption of sampling.
- Auth/authorization at scale beyond the initial OAuth 2.1 addition.

---

This wraps the DeepLearning.AI "MCP: Build Rich-Context AI Apps with
Anthropic" course. See the rest of this repo for the working code from
each lesson: local servers/clients (L3–L7), Claude Desktop integration
(L8), and a real deployed remote server (L9) — live at
`https://mcp-server-2avy.onrender.com/sse`.
