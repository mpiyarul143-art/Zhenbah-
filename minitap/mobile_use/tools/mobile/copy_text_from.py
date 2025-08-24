from typing import Optional

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.types import Command
from minitap.mobile_use.controllers.mobile_command_controller import SelectorRequest
from minitap.mobile_use.controllers.mobile_command_controller import (
    copy_text_from as copy_text_from_controller,
)
from minitap.mobile_use.tools.tool_wrapper import ExecutorMetadata, ToolWrapper
from pydantic import Field
from typing_extensions import Annotated
from minitap.mobile_use.context import MobileUseContext
from minitap.mobile_use.graph.state import State
from langgraph.prebuilt import InjectedState


def get_copy_text_from_tool(ctx: MobileUseContext):
    @tool
    def copy_text_from(
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[State, InjectedState],
        agent_thought: str,
        executor_metadata: Optional[ExecutorMetadata],
        selector_request: SelectorRequest = Field(
            ..., description="The selector to copy text from"
        ),
    ):
        """
        Copies text from a UI element identified by the given selector and stores it in memory.

        The copied text can be:
        - Pasted later using `pasteText`
        - Accessed in JavaScript via `maestro.copiedText`

        Example Usage:
            - launchApp
            - copyTextFrom: { id: "someId" }
            - tapOn: { id: "searchFieldId" }
            - pasteText

        See the Selectors documentation for supported selector types.
        """
        output = copy_text_from_controller(ctx=ctx, selector_request=selector_request)
        has_failed = output is not None
        tool_message = ToolMessage(
            tool_call_id=tool_call_id,
            content=copy_text_from_wrapper.on_failure_fn(selector_request)
            if has_failed
            else copy_text_from_wrapper.on_success_fn(selector_request),
            additional_kwargs={"error": output} if has_failed else {},
        )
        return Command(
            update=copy_text_from_wrapper.handle_executor_state_fields(
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

    return copy_text_from


copy_text_from_wrapper = ToolWrapper(
    tool_fn_getter=get_copy_text_from_tool,
    on_success_fn=lambda selector_request: (
        f'Text copied successfully from selector "{selector_request}".'
    ),
    on_failure_fn=lambda selector_request: f"Failed to copy text from selector {selector_request}.",
)
