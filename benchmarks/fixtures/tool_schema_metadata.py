"""Content-free shape summaries for OpenAI and Ollama function tool schemas."""

from __future__ import annotations

from typing import Any

_MAX_DEPTH = 5
_MAX_PROPERTIES = 128
_MAX_TOOLS = 256
_MAX_SCHEMA_NODES = 2048


def schema_shape(
    schema: Any, depth: int = 0, _budget: list[int] | None = None
) -> dict[str, Any] | None:
    """Keep structural keys/types only; discard descriptions, values, and constraints."""
    if not isinstance(schema, dict):
        return None
    if _budget is None:
        _budget = [_MAX_SCHEMA_NODES]
    if _budget[0] <= 0:
        return {"truncated": True}
    _budget[0] -= 1
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
            property_shapes = {}
            for key in shown:
                if _budget[0] <= 0:
                    shape["truncated"] = True
                    break
                property_shapes[key] = schema_shape(properties[key], depth + 1, _budget)
            shape["properties"] = property_shapes
            if len(keys) > len(shown):
                shape["truncated"] = True
    items = schema.get("items")
    if isinstance(items, dict):
        shape["items"] = (
            schema_shape(items, depth + 1, _budget)
            if depth < _MAX_DEPTH else {"truncated": True}
        )
    additional = schema.get("additionalProperties")
    if isinstance(additional, bool):
        shape["additional_properties"] = additional
    elif isinstance(additional, dict):
        shape["additional_properties"] = (
            schema_shape(additional, depth + 1, _budget)
            if depth < _MAX_DEPTH else {"truncated": True}
        )
    return shape


def tool_schema_metadata(
    tools: Any,
    source: str | None = None,
    depth: int = 0,
    _tool_budget: list[int] | None = None,
    _schema_budget: list[int] | None = None,
) -> list[dict[str, Any]]:
    """Summarize tool schemas from either Responses or Ollama chat request shape."""
    if not isinstance(tools, list):
        return []
    if _tool_budget is None:
        _tool_budget = [_MAX_TOOLS]
    if _schema_budget is None:
        _schema_budget = [_MAX_SCHEMA_NODES]
    summaries = []
    for tool in tools:
        if _tool_budget[0] <= 0:
            summaries.append({"truncated": True})
            break
        _tool_budget[0] -= 1
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
        parameter_shape = schema_shape(parameters, _budget=_schema_budget)
        if parameter_shape is not None:
            record["parameters"] = parameter_shape
        nested = tool.get("tools")
        if isinstance(nested, list):
            if depth >= _MAX_DEPTH:
                record["nested_tools"] = []
                record["nested_tools_truncated"] = True
            else:
                record["nested_tools"] = tool_schema_metadata(
                    nested,
                    depth=depth + 1,
                    _tool_budget=_tool_budget,
                    _schema_budget=_schema_budget,
                )
        if source is not None:
            record["source"] = source
        summaries.append(record)
    return summaries
