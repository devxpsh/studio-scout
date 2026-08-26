"""
Studio Scout — Phase 03
Nested tool-call tracer.

AgentTool runs each sub-agent in its own internal Runner and only
returns final merged text to the parent -- nested tool calls (e.g.
parallel_search inside location_grounding_agent) never reach the
outer event stream that demo_trace.py inspects.

These callbacks print the same evidence directly at the point each
sub-agent's own tool actually fires, so runtime tool invocation stays
demonstrable even when it happens inside a nested AgentTool call.
"""

import json


def trace_before_tool(tool, args, tool_context):
    print("=" * 60)
    print(f"NESTED TOOL CALL — {tool.name}")
    print("=" * 60)
    print(f"  args : {json.dumps(args, indent=2, default=str)}")
    print()
    return None  # do not override the call, just observe it


def trace_after_tool(tool, args, tool_context, tool_response):
    print("=" * 60)
    print(f"NESTED TOOL RESPONSE — {tool.name}")
    print("=" * 60)
    print(json.dumps(tool_response, indent=2, default=str)[:2000])
    print()
    return None  # do not override the response, just observe it