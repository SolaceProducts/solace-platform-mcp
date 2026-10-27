import json
import os

import httpx
import pytest
from fastmcp import FastMCP

import solace_event_portal_designer_mcp.server as server
from solace_event_portal_designer_mcp.server import ROUTE_MAPS, customize_components


@pytest.fixture(scope="module")
def tool_names():
    spec_path = os.path.join(os.path.dirname(server.__file__), "data", "ep-designer.json")
    with open(spec_path) as f:
        spec = json.load(f)
    props = spec["components"]["schemas"]["InvalidStateReference"]["properties"]
    props["inboundInvalidStateReferences"]["items"] = {"type": "object"}
    props["outboundInvalidStateReferences"]["items"] = {"type": "object"}

    mcp = FastMCP.from_openapi(
        openapi_spec=spec,
        client=httpx.AsyncClient(base_url="http://localhost"),
        route_maps=ROUTE_MAPS,
        mcp_component_fn=customize_components,
    )
    return {tool.name for tool in mcp._tool_manager._tools.values()}


class TestRouteMaps:

    @pytest.mark.parametrize("entity", ["Application", "Event", "Schema", "Enum"])
    def test_exposes_entity_version_crud(self, tool_names, entity):
        # GET /schemaVersions/{versionId} and GET /enumVersions/{versionId} use a different
        # path parameter name than their PATCH/DELETE counterparts, so they must still be matched.
        for op in ["get{}Versions", "get{}Version", "create{}Version", "update{}Version", "delete{}Version"]:
            assert op.format(entity) in tool_names

    def test_exposes_enum_crud(self, tool_names):
        assert {"getEnums", "getEnum", "createEnum", "updateEnum", "deleteEnum"} <= tool_names

    def test_excludes_unlisted_routes(self, tool_names):
        assert "updateSchemaVersionState" not in tool_names
        assert "getTopicDomains" not in tool_names
