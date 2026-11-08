import unittest

from benchmarks.fixtures.tool_schema_metadata import schema_shape, tool_schema_metadata


class ToolSchemaMetadataTests(unittest.TestCase):
    def test_openai_and_ollama_wrappers_produce_same_shape(self):
        schema = {
            "type": "object",
            "properties": {
                "cmd": {"type": "string", "description": "PRIVATE DESCRIPTION"},
                "timeout": {"type": "integer", "default": 20},
            },
            "required": ["cmd"],
            "additionalProperties": False,
            "examples": ["PRIVATE EXAMPLE"],
        }
        codex = tool_schema_metadata([{
            "type": "function", "name": "exec_command", "parameters": schema,
        }])
        ollama = tool_schema_metadata([{
            "type": "function", "function": {
                "name": "exec_command", "parameters": schema,
            },
        }])
        self.assertEqual(codex, ollama)
        self.assertEqual(codex, [{
            "type": "function",
            "name": "exec_command",
            "parameters": {
                "type": "object",
                "properties": {"cmd": {"type": "string"}, "timeout": {"type": "integer"}},
                "required": ["cmd"],
                "additional_properties": False,
            },
        }])
        serialized = str(codex)
        self.assertNotIn("PRIVATE DESCRIPTION", serialized)
        self.assertNotIn("PRIVATE EXAMPLE", serialized)
        self.assertNotIn("20", serialized)

    def test_nested_namespace_tools_keep_names_and_structure(self):
        summary = tool_schema_metadata([{
            "type": "namespace",
            "name": "multi_agent_v1",
            "tools": [{
                "type": "function",
                "name": "spawn_agent",
                "parameters": {"type": "object", "properties": {"task": {"type": "string"}}},
            }],
        }])
        self.assertEqual(summary[0]["name"], "multi_agent_v1")
        self.assertEqual(summary[0]["nested_tools"][0]["name"], "spawn_agent")
        self.assertEqual(
            summary[0]["nested_tools"][0]["parameters"]["properties"],
            {"task": {"type": "string"}},
        )

    def test_schema_recursion_is_bounded(self):
        schema = {"type": "object"}
        current = schema
        for index in range(10):
            child = {"type": "object"}
            current["properties"] = {f"level_{index}": child}
            current = child
        result = schema_shape(schema)
        for _ in range(5):
            result = next(iter(result["properties"].values()))
        self.assertTrue(result["truncated"])

    def test_nested_tool_recursion_and_tool_count_are_bounded(self):
        nested = {"name": "leaf", "type": "namespace", "tools": []}
        current = nested
        for index in range(10):
            child = {"name": f"level_{index}", "type": "namespace", "tools": []}
            current["tools"].append(child)
            current = child
        summaries = tool_schema_metadata([nested])
        current_summary = summaries[0]
        for _ in range(5):
            current_summary = current_summary["nested_tools"][0]
        self.assertTrue(current_summary["nested_tools_truncated"])

        oversized = tool_schema_metadata([{"name": f"tool_{i}"} for i in range(300)])
        self.assertEqual(len(oversized), 257)
        self.assertEqual(oversized[-1], {"truncated": True})

        def tool_tree(level):
            return {
                "name": f"node_{level}",
                "type": "namespace",
                "tools": [tool_tree(level + 1) for _ in range(6)] if level < 5 else [],
            }

        nested_result = tool_schema_metadata([tool_tree(0)])

        def count_tools(records):
            return sum(
                1 + count_tools(record.get("nested_tools", []))
                for record in records if isinstance(record, dict) and "name" in record
            )

        def has_truncation(records):
            return any(
                record.get("nested_tools_truncated")
                or record.get("truncated")
                or has_truncation(record.get("nested_tools", []))
                for record in records if isinstance(record, dict)
            )

        self.assertLessEqual(count_tools(nested_result), 256)
        self.assertTrue(has_truncation(nested_result))

    def test_branching_schema_uses_one_global_node_budget(self):
        def schema_tree(level):
            if level == 6:
                return {"type": "string"}
            return {
                "type": "object",
                "properties": {f"field_{index}": schema_tree(level + 1) for index in range(5)},
            }

        result = schema_shape(schema_tree(0))

        def count_nodes(shape):
            if not isinstance(shape, dict):
                return 0
            count = 1
            properties = shape.get("properties")
            if isinstance(properties, dict):
                count += sum(count_nodes(child) for child in properties.values())
            for key in ("items", "additional_properties"):
                count += count_nodes(shape.get(key))
            return count

        self.assertLessEqual(count_nodes(result), 2048)


if __name__ == "__main__":
    unittest.main(verbosity=2)
