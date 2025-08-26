from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from minitap.mobile_use.agents.hopper.hopper import HopperOutput, hopper
from minitap.mobile_use.context import MobileUseContext
from minitap.mobile_use.controllers.platform_specific_commands_controller import (
    list_packages as list_packages_command,
)
from minitap.mobile_use.graph.state import State
from minitap.mobile_use.tools.tool_wrapper import ToolWrapper
from typing_extensions import Annotated


def get_list_packages_tool(ctx: MobileUseContext):
    @tool
    async def list_packages(
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        agent_thought: str,
    ) -> Command:
        """
        Lists all the applications on the device.
        Outputs the full package names list (android) or bundle ids list (IOS).
        """
        output: str = list_packages_command(ctx=ctx)

        try:
            hopper_output: HopperOutput = await hopper(
                ctx=ctx,
                initial_goal=state.initial_goal,
                messages=state.messages,
                data=output,
            )
            tool_message = ToolMessage(
                tool_call_id=tool_call_id,
                content=list_packages_wrapper.on_success_fn()
                + ": "
                + hopper_output.step
                + ": "
                + hopper_output.output,
                status="success",
            )
        except Exception as e:
            print("Failed to extract insights from data: " + str(e))
            tool_message = ToolMessage(
                tool_call_id=tool_call_id,
                content=list_packages_wrapper.on_failure_fn(),
                additional_kwargs={"output": output},
                status="error",
            )

        return Command(
            update=state.sanitize_update(
                ctx=ctx,
                update={
                    "agents_thoughts": [agent_thought],
                    "executor_messages": [tool_message],
                },
            ),
        )

    return list_packages


list_packages_wrapper = ToolWrapper(
    tool_fn_getter=get_list_packages_tool,
    on_success_fn=lambda: "Packages listed successfully.",
    on_failure_fn=lambda: "Failed to list packages.",
)
