from pathlib import Path

from jinja2 import Template
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.messages.ai import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from minitap.mobile_use.context import MobileUseContext
from minitap.mobile_use.graph.state import State
from minitap.mobile_use.services.llm import get_llm
from minitap.mobile_use.tools.index import EXECUTOR_WRAPPERS_TOOLS, get_tools_from_wrappers
from minitap.mobile_use.utils.decorators import wrap_with_callbacks
from minitap.mobile_use.utils.logger import get_logger

logger = get_logger(__name__)


class ExecutorNode:
    def __init__(self, ctx: MobileUseContext):
        self.ctx = ctx

    @wrap_with_callbacks(
        before=lambda: logger.info("Starting Executor Agent..."),
        on_success=lambda _: logger.success("Executor Agent"),
        on_failure=lambda _: logger.error("Executor Agent"),
    )
    async def __call__(self, state: State):
        structured_decisions = state.structured_decisions
        if not structured_decisions:
            logger.warning("No structured decisions found.")
            return state.sanitize_update(
                ctx=self.ctx,
                update={
                    "agents_thoughts": [
                        "No structured decisions found, I cannot execute anything."
                    ],
                },
            )

        if len(state.executor_messages) > 0 and isinstance(state.executor_messages[-1], AIMessage):
            if len(state.executor_messages[-1].tool_calls) > 0:  # type: ignore
                # A previous tool call raised an uncaught exception while retrigerring the executor
                return state.sanitize_update(
                    ctx=self.ctx,
                    update={
                        "executor_retrigger": False,
                        "executor_failed": True,
                        "executor_messages": [state.messages[-1]],
                    },
                )

        system_message = Template(
            Path(__file__).parent.joinpath("executor.md").read_text(encoding="utf-8")
        ).render(platform=self.ctx.device.mobile_platform.value)
        cortex_last_thought = (
            state.cortex_last_thought if state.cortex_last_thought else state.agents_thoughts[-1]
        )
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=cortex_last_thought),
            HumanMessage(content=structured_decisions),
            *state.executor_messages,
        ]

        llm = get_llm(ctx=self.ctx, name="executor")
        llm_bind_tools_kwargs = {
            "tools": get_tools_from_wrappers(self.ctx, EXECUTOR_WRAPPERS_TOOLS),
            "tool_choice": "auto",  # automatically select a tool call or none
        }

        # ChatGoogleGenerativeAI does not support the "parallel_tool_calls" keyword
        if not isinstance(llm, ChatGoogleGenerativeAI):
            llm_bind_tools_kwargs["parallel_tool_calls"] = False

        llm = llm.bind_tools(**llm_bind_tools_kwargs)
        response = await llm.ainvoke(messages)

        return state.sanitize_update(
            ctx=self.ctx,
            update={
                "cortex_last_thought": cortex_last_thought,
                "executor_messages": [response],
                "messages": [response],
            },
        )
