from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List, Dict, TypedDict
from contextlib import AsyncExitStack
import json
import asyncio

load_dotenv()

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

class MCP_ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}
        self.available_prompts: List[dict] = []
        self.prompt_to_session: Dict[str, ClientSession] = {}


    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.sessions.append(session)

            # List available tools for this session
            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to {server_name} with tools:", [t.name for t in tools])

            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })

            # List available prompts for this session (not every server offers prompts)
            try:
                prompts_response = await session.list_prompts()
                if prompts_response and prompts_response.prompts:
                    for prompt in prompts_response.prompts:
                        self.prompt_to_session[prompt.name] = session
                        self.available_prompts.append({
                            "name": prompt.name,
                            "description": prompt.description,
                            "arguments": prompt.arguments
                        })
            except Exception:
                pass
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self):
        """Connect to all configured MCP servers."""
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)

            servers = data.get("mcpServers", {})

            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise

    async def process_query(self, query):
        messages = [{'role':'user', 'content':query}]
        response = self.anthropic.messages.create(max_tokens = 2024,
                                      model = 'claude-sonnet-4-6',
                                      tools = self.available_tools,
                                      messages = messages)
        process_query = True
        while process_query:
            assistant_content = []
            for content in response.content:
                if content.type =='text':
                    print(content.text)
                    assistant_content.append(content)
                    if(len(response.content) == 1):
                        process_query= False
                elif content.type == 'tool_use':
                    assistant_content.append(content)
                    messages.append({'role':'assistant', 'content':assistant_content})
                    tool_id = content.id
                    tool_args = content.input
                    tool_name = content.name


                    print(f"Calling tool {tool_name} with args {tool_args}")

                    # Call a tool
                    session = self.tool_to_session[tool_name]
                    result = await session.call_tool(tool_name, arguments=tool_args)
                    messages.append({"role": "user",
                                      "content": [
                                          {
                                              "type": "tool_result",
                                              "tool_use_id":tool_id,
                                              "content": result.content
                                          }
                                      ]
                                    })
                    response = self.anthropic.messages.create(max_tokens = 2024,
                                      model = 'claude-sonnet-4-6',
                                      tools = self.available_tools,
                                      messages = messages)

                    if(len(response.content) == 1 and response.content[0].type == "text"):
                        print(response.content[0].text)
                        process_query= False

    async def get_resource(self, resource_uri):
        """Read a resource (e.g. papers://folders, papers://<topic>) from whichever
        connected server exposes it, and feed its content into a query."""
        if not self.sessions:
            print("Not connected to any MCP server.")
            return

        for candidate_session in self.sessions:
            try:
                result = await candidate_session.read_resource(uri=resource_uri)
                if result and result.contents:
                    content_text = result.contents[0].text
                    print(f"\nResource: {resource_uri}\n")
                    print(content_text)
                    return
            except Exception:
                continue

        print(f"Resource {resource_uri} not found.")

    async def list_prompts(self):
        """List all available prompts."""
        if not self.available_prompts:
            print("No prompts available.")
            return

        print("\nAvailable prompts:")
        for prompt in self.available_prompts:
            print(f"- {prompt['name']}: {prompt['description']}")
            if prompt['arguments']:
                print(f"  Arguments:")
                for arg in prompt['arguments']:
                    arg_name = arg.name if hasattr(arg, 'name') else arg.get('name', '')
                    print(f"    - {arg_name}")

    async def execute_prompt(self, prompt_name, args):
        """Execute a prompt with the given arguments."""
        session = self.prompt_to_session.get(prompt_name)
        if not session:
            print(f"Prompt '{prompt_name}' not found.")
            return

        try:
            result = await session.get_prompt(prompt_name, arguments=args)
            if result and result.messages:
                prompt_content = result.messages[0].content

                # Extract text from content (handles different content types)
                if isinstance(prompt_content, str):
                    text = prompt_content
                elif hasattr(prompt_content, 'text'):
                    text = prompt_content.text
                else:
                    text = " ".join(item.text if hasattr(item, 'text') else str(item)
                                     for item in prompt_content)

                print(f"\nExecuting prompt '{prompt_name}'...")
                await self.process_query(text)
        except Exception as e:
            print(f"Error executing prompt '{prompt_name}': {e}")

    async def chat_loop(self):
        """Run an interactive chat loop supporting:
        - plain queries (sent to the LLM)
        - @folders / @<topic>  -> reads an MCP resource
        - /prompts             -> lists available prompt templates
        - /prompt <name> <arg1=value1> <arg2=value2>  -> runs a prompt template
        """
        print("\nMCP Chatbot Started!")
        print("Type your queries, '@folders'/'@<topic>', '/prompts', '/prompt <name> <arg=value>', or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if not query:
                    continue

                if query.lower() == 'quit':
                    break

                if query.startswith('@'):
                    topic = query[1:]
                    if topic == "folders":
                        resource_uri = "papers://folders"
                    else:
                        resource_uri = f"papers://{topic}"
                    await self.get_resource(resource_uri)
                    continue

                if query.startswith('/prompts'):
                    await self.list_prompts()
                    continue

                if query.startswith('/prompt'):
                    parts = query.split()
                    if len(parts) < 2:
                        print("Usage: /prompt <name> <arg1=value1> <arg2=value2>")
                        continue

                    prompt_name = parts[1]
                    args = {}
                    for part in parts[2:]:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            args[key] = value

                    await self.execute_prompt(prompt_name, args)
                    continue

                await self.process_query(query)
                print("\n")

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()


async def main():
    chatbot = MCP_ChatBot()
    try:
        # the mcp clients and sessions are not initialized using "with"
        # like in the previous lesson
        # so the cleanup should be manually handled
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
