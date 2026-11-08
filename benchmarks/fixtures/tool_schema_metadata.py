"""Content-free shape summaries for OpenAI and Ollama function tool schemas."""

from __future__ import annotations

from typing import Any

_MAX_DEPTH = 5
_MAX_PROPERTIES = 128
_MAX_TOOLS = 256


def schema_shape(schema: Any, depth: int = 0) -> dict[str, Any] | None:
    """Keep structural keys/types only; discard descriptions, values, and constraints."""
    if not isinstance(schema, dict):
        return None
    shape: dict[str, Any] = {}
    schema_type = schema.get("type")
    if isinstance(schema_type, str):
        shape["type"] = schema_type
    required = schema.get("required")
    if isinstance(required, list):
        shape["required"] = sorted(item for item in required if isinstance(item, str))[:_MAX_PROPERTIES]
    properties = schema.get("properties")
    if isinstance(properties, dict):
        keys = sorted(key for key in properties if isinstance(key, str))
        shown = keys[:_MAX_PROPERTIES]
        if depth >= _MAX_DEPTH:
            shape["properties"] = shown
            shape["truncated"] = bool(len(keys) > len(shown) or keys)
        else:
            shape["properties"] = {
                key: schema_shape(properties[key], depth + 1) for key in shown
            }
            if len(keys) > len(shown):
                shape["truncated"] = True
    items = schema.get("items")
    if isinstance(items, dict):
        shape["items"] = schema_shape(items, depth + 1) if depth < _MAX_DEPTH else {"truncated": True}
    additional = schema.get("additionalProperties")
    if isinstance(additional, bool):
        shape["additional_properties"] = additional
    elif isinstance(additional, dict):
        shape["additional_properties"] = (
            schema_shape(additional, depth + 1) if depth < _MAX_DEPTH else {"truncated": True}
        )
    return shape


def tool_schema_metadata(
    tools: Any, source: str | None = None, depth: int = 0
) -> list[dict[str, Any]]:
    """Summarize tool schemas from either Responses or Ollama chat request shape."""
    if not isinstance(tools, list):
        return []
    summaries = []
    for tool in tools[:_MAX_TOOLS]:
        if not isinstance(tool, dict):
            continue
        function = tool.get("function")
        function = function if isinstance(function, dict) else tool
        record: dict[str, Any] = {}
        kind = tool.get("type")
        if isinstance(kind, str):
            record["type"] = kind
        name = function.get("name")
        if isinstance(name, str):
            record["name"] = name
        parameters = function.get("parameters")
        parameter_shape = schema_shape(parameters)
        if parameter_shape is not None:
            record["parameters"] = parameter_shape
        nested = tool.get("tools")
        if isinstance(nested, list):
            if depth >= _MAX_DEPTH:
                record["nested_tools"] = []
                record["nested_tools_truncated"] = True
            else:
                record["nested_tools"] = tool_schema_metadata(nested, depth=depth + 1)
        if source is not None:
            record["source"] = source
        summaries.append(record)
    if len(tools) > _MAX_TOOLS:
        summaries.append({"truncated": True})
    return summaries
