import json
import os
from azure.identity.aio import (
    AzureDeveloperCliCredential,
    ChainedTokenCredential,
    ManagedIdentityCredential,
    DefaultAzureCredential,
    get_bearer_token_provider,
)
from openai import AsyncAzureOpenAI
from quart import (
    Blueprint,
    Response,
    current_app,
    render_template,
    request,
    stream_with_context,
)
from langgraph import LangGraph
from msgraph.aio import GraphServiceClient  # Import Microsoft Graph SDK for M365 API access

bp = Blueprint("chat", __name__, template_folder="templates", static_folder="static")


@bp.before_app_serving
async def configure_openai():
    # Use ManagedIdentityCredential with the client_id for user-assigned managed identities
    user_assigned_managed_identity_credential = ManagedIdentityCredential(client_id=os.getenv("AZURE_CLIENT_ID"))

    # Use AzureDeveloperCliCredential with the current tenant.
    azure_dev_cli_credential = AzureDeveloperCliCredential(tenant_id=os.getenv("AZURE_TENANT_ID"), process_timeout=60)

    # Create a ChainedTokenCredential with ManagedIdentityCredential and AzureDeveloperCliCredential
    azure_credential = ChainedTokenCredential(user_assigned_managed_identity_credential, azure_dev_cli_credential)
    current_app.logger.info("Using Azure OpenAI with credential")

    # Get the token provider for Azure OpenAI based on the selected Azure credential
    token_provider = get_bearer_token_provider(azure_credential, "https://cognitiveservices.azure.com/.default")
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        raise ValueError("AZURE_OPENAI_ENDPOINT is required for Azure OpenAI")
    if not os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"):
        raise ValueError("AZURE_OPENAI_CHAT_DEPLOYMENT is required for Azure OpenAI")

    # Create the Asynchronous Azure OpenAI client
    bp.openai_client = AsyncAzureOpenAI(
        api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-02-15-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_ad_token_provider=token_provider,
    )
    # Set the model name to the Azure OpenAI model deployment name
    bp.openai_model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

    # Initialize LangGraph
    current_app.lang_graph = LangGraph()
    current_app.logger.info("LangGraph initialized")

    # Set up Graph API client (Microsoft 365 Copilot)
    current_app.graph_client = GraphServiceClient(credential=DefaultAzureCredential())
    current_app.logger.info("Graph API client initialized")


@bp.after_app_serving
async def shutdown_openai():
    await bp.openai_client.close()


@bp.get("/")
async def index():
    return await render_template("index.html")


@bp.post("/chat/stream")
async def chat_handler():
    request_messages = (await request.get_json())["messages"]
    user_message = request_messages[-1]["content"]  # Assuming the user's query is the last message

    @stream_with_context
    async def response_stream():
        response = None
        if should_route_to_openai(user_message):
            response = await route_to_openai(request_messages)
        else:
            response = await route_to_copilot(user_message)

        if response:
            yield json.dumps(response, ensure_ascii=False) + "\n"
        else:
            yield json.dumps({"error": "No response generated"}, ensure_ascii=False) + "\n"

    return Response(response_stream())


def should_route_to_openai(message):
    # Define logic to determine if the message should be routed to OpenAI or Microsoft 365 Copilot
    # For now, let's assume we route all non-calendar-related queries to OpenAI
    return not ("appointments" in message or "meetings" in message)


async def route_to_openai(messages):
    all_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
    ] + messages

    chat_coroutine = bp.openai_client.chat.completions.create(
        model=bp.openai_model,
        messages=all_messages,
        stream=True,
    )

    try:
        async for event in await chat_coroutine:
            event_dict = event.model_dump()
            if event_dict["choices"]:
                return event_dict["choices"][0]
    except Exception as e:
        current_app.logger.error(e)
        return {"error": str(e)}


async def route_to_copilot(message):
    # Query Microsoft 365 Graph API to fetch calendar data
    try:
        events = await current_app.graph_client.me.events.get()
        event_list = [{"subject": event["subject"], "start": event["start"]["dateTime"]} for event in events["value"]]

        return {"role": "assistant", "content": f"Here are your upcoming events: {event_list}"}
    except Exception as e:
        current_app.logger.error(f"Error calling Microsoft Graph API: {e}")
        return {"error": f"Error retrieving calendar data: {str(e)}"}
