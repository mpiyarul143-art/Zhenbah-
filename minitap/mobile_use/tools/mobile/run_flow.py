from typing import Optional
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from minitap.mobile_use.context import MobileUseContext
from minitap.mobile_use.controllers.mobile_command_controller import run_flow as run_flow_controller
from minitap.mobile_use.graph.state import State
from minitap.mobile_use.tools.tool_wrapper import ExecutorMetadata, ToolWrapper
from typing_extensions import Annotated


def get_run_flow_tool(ctx: MobileUseContext):
    @tool
    def run_flow(
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        agent_thought: str,
        flow_steps: list,
        executor_metadata: Optional[ExecutorMetadata],
        dry_run: bool = False,
    ):
        """
        Run a flow i.e, a sequence of commands.
        """
        output = run_flow_controller(ctx=ctx, flow_steps=flow_steps, dry_run=dry_run)
        has_failed = output is not None
        tool_message = ToolMessage(
            tool_call_id=tool_call_id,
            content=run_flow_wrapper.on_failure_fn()
            if has_failed
            else run_flow_wrapper.on_success_fn(),
            additional_kwargs={"error": output} if has_failed else {},
        )
        return Command(
            update=run_flow_wrapper.handle_executor_state_fields(
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

    return run_flow


run_flow_wrapper = ToolWrapper(
    tool_fn_getter=get_run_flow_tool,
    on_success_fn=lambda: "Flow run successfully.",
    on_failure_fn=lambda: "Failed to run flow.",
)
