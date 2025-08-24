from langchain_core.messages.ai import AIMessage
from minitap.mobile_use.graph.state import State
from minitap.mobile_use.utils.decorators import wrap_with_callbacks
from minitap.mobile_use.utils.logger import get_logger

logger = get_logger(__name__)


@wrap_with_callbacks(
    before=lambda: logger.info("Starting Executor Context Cleaner..."),
    on_success=lambda _: logger.success("Executor Context Cleaner"),
    on_failure=lambda _: logger.error("Executor Context Cleaner"),
)
async def executor_context_cleaner_node(state: State):
    """Clears the executor context."""
    update: dict = {
        "executor_failed": False,
        "executor_retrigger": False,
    }
    if len(state.executor_messages) > 0 and isinstance(state.executor_messages[-1], AIMessage):
        last_executor_message = state.executor_messages[-1]
        if len(last_executor_message.tool_calls) > 0:
            # A previous tool call raised an uncaught exception -> sanitize the executor messages
            tool_error_message = state.messages[-1]
            logger.error("Tool call failed with error: " + str(tool_error_message.content))
            update["executor_messages"] = [tool_error_message]
    return update
