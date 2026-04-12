import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from tools.ldong_code import get_ldong_code
from tools.area_based_list import get_area_based_list
from tools.location_based_list import get_location_based_list
from tools.search_keyword import search_medical_by_keyword
from tools.sync_list import get_medical_sync_list
from tools.detail_common import get_detail_common
from tools.detail_intro import get_detail_intro
from tools.detail_mdcl_tursm import get_detail_medical

port = int(os.environ.get("PORT", 8000))

mcp = FastMCP(
    "visitkorea-medicaltourism",
    host="0.0.0.0",
    port=port,
    stateless_http=True,
)

mcp.tool()(get_ldong_code)
mcp.tool()(get_area_based_list)
mcp.tool()(get_location_based_list)
mcp.tool()(search_medical_by_keyword)
mcp.tool()(get_medical_sync_list)
mcp.tool()(get_detail_common)
mcp.tool()(get_detail_intro)
mcp.tool()(get_detail_medical)


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_request: Request) -> JSONResponse:
    """Lightweight liveness probe for production health checks."""
    return JSONResponse({"status": "ok", "server": "visitkorea-medicaltourism"})


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
