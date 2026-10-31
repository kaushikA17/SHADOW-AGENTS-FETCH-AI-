"""Run GRID as an independent Agentverse / A2A agent."""

import os
from dotenv import load_dotenv

load_dotenv()

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from uagents_adapter import SingleA2AAdapter

from grid import handle_text


GRID_SEED = os.getenv("GRID_AGENT_SEED")

if not GRID_SEED:
    raise RuntimeError(
        "GRID_AGENT_SEED is missing. Add it to the GRID-AGENT .env file."
    )


class GridExecutor(AgentExecutor):

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        user_message = context.get_user_input()
        response = handle_text(user_message)

        await event_queue.enqueue_event(
            new_agent_text_message(response)
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise Exception("Cancel not supported")


grid = SingleA2AAdapter(
    agent_executor=GridExecutor(),
    name="grid-supplier-agent",
    description=(
        "SIMULATED supplier agent for hotel linen (bedsheets, towels, pillows, blankets). "
        "Provides quotations, negotiates within fixed limits, validates purchase orders, "
        "and reports simulated order status."
    ),
    port=8201,
    a2a_port=9998,
    mailbox=True,
    seed=GRID_SEED,
)


if __name__ == "__main__":
    print("Starting GRID Supplier Agent...")
    grid.run()