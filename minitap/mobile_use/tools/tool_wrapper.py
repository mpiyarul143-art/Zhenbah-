from typing import Callable, Optional

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from minitap.mobile_use.context import MobileUseContext
from minitap.mobile_use.graph.state import State


class ExecutorMetadata(BaseModel):
    retrigger: bool


class ToolWrapper(BaseModel):
    tool_fn_getter: Callable[[MobileUseContext], BaseTool]
    on_success_fn: Callable[..., str]
    on_failure_fn: Callable[..., str]

    def handle_executor_state_fields(
        self,
        ctx: MobileUseContext,
        state: State,
        executor_metadata: Optional[ExecutorMetadata],
        is_failure: bool,
        tool_message: ToolMessage,
        updates: dict,
    ):
        if executor_metadata is None:
            return state.sanitize_update(ctx=ctx, update=updates)
        updates["executor_retrigger"] = executor_metadata.retrigger
        updates["executor_messages"] = [tool_message]
        updates["executor_failed"] = is_failure
        return state.sanitize_update(ctx=ctx, update=updates)
