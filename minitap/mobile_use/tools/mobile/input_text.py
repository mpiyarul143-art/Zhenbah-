from typing import Optional

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.types import Command
from minitap.mobile_use.controllers.mobile_command_controller import (
    input_text as input_text_controller,
)
from minitap.mobile_use.tools.tool_wrapper import ExecutorMetadata, ToolWrapper
from typing_extensions import Annotated
from minitap.mobile_use.graph.state import State
from langgraph.prebuilt import InjectedState
from minitap.mobile_use.context import MobileUseContext


def get_input_text_tool(ctx: MobileUseContext):
    @tool
    def input_text(
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        agent_thought: str,
        executor_metadata: Optional[ExecutorMetadata],
        text: str,
    ):
        """
        Inputs the specified text into the UI (works even if no field is focused).

        Example:
            - inputText: "Hello World"

        Notes:
        - Unicode not supported on Android.

        Random Input Options:
            - inputRandomEmail
            - inputRandomPersonName
            - inputRandomNumber (with optional 'length', default 8)
            - inputRandomText (with optional 'length', default 8)

        Tip:
            Use `copyTextFrom` to reuse generated inputs in later steps.
        """
        output = input_text_controller(ctx=ctx, text=text)
        has_failed = output is not None
        tool_message = ToolMessage(
            tool_call_id=tool_call_id,
            content=input_text_wrapper.on_failure_fn(text)
            if has_failed
            else input_text_wrapper.on_success_fn(text),
            additional_kwargs={"error": output} if has_failed else {},
        )
        return Command(
            update=input_text_wrapper.handle_executor_state_fields(
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

    return input_text


input_text_wrapper = ToolWrapper(
    tool_fn_getter=get_input_text_tool,
    on_success_fn=lambda text: f"Successfully typed {text}",
    on_failure_fn=lambda text: f"Failed to input text {text}",
)
