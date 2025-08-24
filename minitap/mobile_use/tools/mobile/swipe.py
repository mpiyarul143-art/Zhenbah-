from typing import Optional

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from minitap.mobile_use.context import MobileUseContext
from minitap.mobile_use.controllers.mobile_command_controller import SwipeRequest
from minitap.mobile_use.controllers.mobile_command_controller import swipe as swipe_controller
from minitap.mobile_use.graph.state import State
from minitap.mobile_use.tools.tool_wrapper import ExecutorMetadata, ToolWrapper
from typing_extensions import Annotated


def get_swipe_tool(ctx: MobileUseContext):
    @tool
    def swipe(
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        agent_thought: str,
        executor_metadata: Optional[ExecutorMetadata],
        swipe_request: SwipeRequest,
    ):
        """
        Swipes on the screen.
        """
        output = swipe_controller(ctx=ctx, swipe_request=swipe_request)
        has_failed = output is not None
        tool_message = ToolMessage(
            tool_call_id=tool_call_id,
            content=swipe_wrapper.on_failure_fn() if has_failed else swipe_wrapper.on_success_fn(),
            additional_kwargs={"error": output} if has_failed else {},
        )
        return Command(
            update=swipe_wrapper.handle_executor_state_fields(
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

    return swipe


swipe_wrapper = ToolWrapper(
    tool_fn_getter=get_swipe_tool,
    on_success_fn=lambda: "Swipe is successful.",
    on_failure_fn=lambda: "Failed to swipe.",
)
