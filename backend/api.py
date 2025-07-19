# api.py – Lead tools + RAG search tool
from livekit.agents.llm.tool_context import ToolContext, function_tool
import enum, logging
from typing import Annotated
from db_driver import DatabaseDriver
from rag_utils import retrieve_relevant_snippets

log = logging.getLogger("assistant")
DB  = DatabaseDriver()

class Lead(enum.Enum):
    NAME  = "name"
    EMAIL = "email"
    INT   = "interest"

class AssistantFnc(ToolContext):
    def __init__(self):
        super().__init__([])
        self._lead = {Lead.NAME: "", Lead.EMAIL: "", Lead.INT: ""}

    # ---------- lead‑capture helpers ------------------------------------------
    @function_tool(description="Save the visitor lead information.")
    async def save_lead(
        self,
        name:  Annotated[str, ""],
        email: Annotated[str, ""],
        interest: Annotated[str, ""]
    ):
        self._lead = {Lead.NAME: name, Lead.EMAIL: email, Lead.INT: interest}
        # write to DB if desired
        log.info("Lead saved: %s", self._lead)
        return "Thanks! Your info has been saved."

    # ---------- RAG search tool ----------------------------------------------
    @function_tool(description="Search Sunset17 site for answers.")
    async def sunset17_search(
        self,
        query: Annotated[str, "User question about Sunset17 services or prices"]
    ):
        snippets, urls = retrieve_relevant_snippets(query)
        if not snippets:
            return ""   # agent will say fallback line
        return "\n\n".join(
            f"Source: {u}\n{s}" for s, u in zip(snippets, urls)
        )
