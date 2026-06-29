import asyncio
import json
import subprocess
from typing import Dict, Any, List

class LocalFileSystemMCPClient:
    """A lightweight MCP client that talks to a local filesystem MCP server."""
    def __init__(self, target_directory: str):
        self.target_directory = target_directory
        self.process = None

    async def connect(self):
        # We start the standard node filesystem MCP server via subprocess stdio
        # This requires node and the mcp server package installed globally/locally
        self.process = await asyncio.create_subprocess_exec(
            "npx", "-y", "@modelcontextprotocol/server-filesystem", self.target_directory,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )

    async def _send_rpc_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Formats and transmits an official JSON-RPC 2.0 MCP packet."""
        request_packet = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        # Write to process stdin
        self.process.stdin.write(json.dumps(request_packet).encode() + b"\n")
        await self.process.stdin.drain()
        
        # Read from process stdout
        response_line = await self.process.stdout.readline()
        return json.loads(response_line.decode())

    async def list_files(self) -> List[Dict[str, Any]]:
        """Queries the MCP server resources/list endpoint."""
        response = await self._send_rpc_request("resources/list")
        return response.get("result", {}).get("resources", [])

    async def read_file_context(self, file_uri: str) -> str:
        """Queries the MCP server to read content securely."""
        response = await self._send_rpc_request("resources/read", {"uri": file_uri})
        contents = response.get("result", {}).get("contents", [])
        if contents:
            return contents[0].get("text", "")
        return ""

    async def disconnect(self):
        if self.process:
            self.process.terminate()
            await self.process.wait()