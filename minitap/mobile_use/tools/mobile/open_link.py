from typing import Optional

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from minitap.mobile_use.context import MobileUseContext
from minitap.mobile_use.controllers.mobile_command_controller import (
    open_link as open_link_controller,
)
from minitap.mobile_use.graph.state import State
from minitap.mobile_use.tools.tool_wrapper import ExecutorMetadata, ToolWrapper
from typing_extensions import Annotated


def get_open_link_tool(ctx: MobileUseContext):
    @tool
    def open_link(
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        agent_thought: str,
        executor_metadata: Optional[ExecutorMetadata],
        url: str,
    ):
        """
        Open a link on a device (i.e. a deep link).
        """
        output = open_link_controller(ctx=ctx, url=url)
        has_failed = output is not None
        tool_message = ToolMessage(
            tool_call_id=tool_call_id,
            content=open_link_wrapper.on_failure_fn()
            if has_failed
            else open_link_wrapper.on_success_fn(url),
            additional_kwargs={"error": output} if has_failed else {},
        )
        return Command(
            update=open_link_wrapper.handle_executor_state_fields(
                ctx=ctx,
                state=state,
                executor_metadata=executor_metadata,
                tool_message=tool_message,
                is_failure=has_failed,
                updates={
                    "agents_thoughts": [agent_thought],
                    "messages": [tool_message],
                },
            ),
        )

    return open_link


open_link_wrapper = ToolWrapper(
    tool_fn_getter=get_open_link_tool,
    on_success_fn=lambda url: f"Link {url} opened successfully.",
    on_failure_fn=lambda: "Failed to open link.",
)
