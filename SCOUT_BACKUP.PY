import os
import asyncio
import requests
import uvicorn

from starlette.applications import Starlette

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentProvider,
    AgentSkill,
)

from a2a.helpers import new_text_message

from agentverse_sdk.a2a import init as agentverse_init


# ==========================================
# 1. LOAD CREDENTIALS
# ==========================================

AGENT_URI = os.environ.get("AGENT_URI")
ASI_API_KEY = os.environ.get("ASI_ONE_API_KEY")

if not AGENT_URI:
    raise ValueError("AGENT_URI is missing!")

if not ASI_API_KEY:
    raise ValueError("ASI_ONE_API_KEY is missing!")

# ==========================================
# 2. CONNECT TO AGENTVERSE
# ==========================================

agentverse_init(AGENT_URI, mailbox=True)


# ==========================================
# 3. CONNECT TO ASI:ONE AI
# ==========================================

def ask_scout_ai(user_message):

    response = requests.post(
        "https://api.asi1.ai/v1/chat/completions",

        headers={
            "Authorization": f"Bearer {ASI_API_KEY}",
            "Content-Type": "application/json"
        },

        json={
            "model": "asi1",

            "messages": [
                {
                    "role": "system",
                    "content": """
                    You are Scout, an AI procurement assistant
                    designed for hotels and hospitality businesses.

                    Your responsibilities:

                    1. Analyse inventory information.
                    2. Identify stock shortages.
                    3. Calculate procurement requirements.
                    4. Assist with supplier comparisons.
                    5. Explain procurement recommendations.

                    IMPORTANT RULES:

                    - Show calculations clearly.
                    - Never invent inventory data.
                    - Never invent supplier offers.
                    - Never claim to have contacted suppliers
                      unless supplier integration actually exists.
                    - Never make purchases.
                    - Require human approval before procurement.
                    - Clearly identify missing information.
                    """
                },

                {
                    "role": "user",
                    "content": user_message
                }
            ]
        },

        timeout=60
    )

    response.raise_for_status()

    result = response.json()

    return result["choices"][0]["message"]["content"]


# ==========================================
# 4. SCOUT AGENT EXECUTOR
# ==========================================

class ScoutExecutor(AgentExecutor):

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue
    ) -> None:

        user_message = context.get_user_input()

        try:

            ai_response = await asyncio.to_thread(
                ask_scout_ai,
                user_message
            )

            response = (
                "SCOUT PROCUREMENT AI\n\n"
                + ai_response
            )

        except requests.exceptions.RequestException as error:

            response = (
                "SCOUT AI CONNECTION ERROR\n\n"
                "Unable to communicate with ASI:One.\n"
                "Please check your API connection.\n\n"
                f"Error: {error}"
            )

        except Exception as error:

            response = (
                "SCOUT ERROR\n\n"
                f"Something went wrong: {error}"
            )

        await event_queue.enqueue_event(
            new_text_message(response)
        )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue
    ) -> None:

        raise Exception("Cancellation is not supported yet.")


# ==========================================
# 5. DEFINE SCOUT CAPABILITIES
# ==========================================

if __name__ == "__main__":

    skill = AgentSkill(
        id="procurement_assistant",

        name="AI Procurement Assistant",

        description=(
            "AI-powered hospitality inventory analysis "
            "and procurement assistance."
        ),

        tags=[
            "AI",
            "procurement",
            "inventory",
            "hospitality",
            "supplier management"
        ],

        examples=[
            "Check my inventory",
            "Calculate my inventory shortage",
            "How do you manage suppliers?",
            "Explain your procurement workflow"
        ],
    )

    agent_card = AgentCard(

        name="Scout Procurement AI",

        description=(
            "An AI procurement assistant for hospitality "
            "inventory analysis and supplier coordination."
        ),

        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                protocol_version="0.3",
                url="http://localhost:9999"
            )
        ],

        version="1.0.0",

        default_input_modes=["text"],

        default_output_modes=["text"],

        capabilities=AgentCapabilities(
            streaming=True,
            extended_agent_card=True
        ),

        skills=[skill],

        provider=AgentProvider(
            organization="Scout",
            url="https://agentverse.ai/"
        ),
    )


    # ======================================
    # 6. CREATE A2A REQUEST HANDLER
    # ======================================

    request_handler = DefaultRequestHandler(

        agent_card=agent_card,

        agent_executor=ScoutExecutor(),

        task_store=InMemoryTaskStore(),
    )


    # ======================================
    # 7. CREATE SERVER ROUTES
    # ======================================

    routes = create_agent_card_routes(agent_card)

    routes.extend(
        create_jsonrpc_routes(
            request_handler,
            rpc_url="/"
        )
    )

    app = Starlette(routes=routes)


    # ======================================
    # 8. START SCOUT
    # ======================================

    print("===================================")
    print("SCOUT PROCUREMENT AI IS STARTING")
    print("ASI:ONE AI CONNECTION ENABLED")
    print("AGENTVERSE A2A CONNECTION ENABLED")
    print("SERVER: http://localhost:9999")
    print("===================================")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9999
    )