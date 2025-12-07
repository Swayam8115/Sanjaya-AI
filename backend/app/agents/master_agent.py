# from langgraph.graph import StateGraph, END
# from pydantic import BaseModel
# import json 
# from app.utils.schemas import RouterOutput, SynthOutput
# from app.utils.prompts import MASTER_AGENT_ROUTER_PROMPT, SYNTH_PROMPT
# from app.agents import (
#     iqvia_agent, patents_agent,
#     clinical_agent, internal_agent, web_agent,
#     report_agent
# )
# from app.config.settings import settings
# from openai import OpenAI

# client = OpenAI(
#     api_key=settings.GOOGLE_API_KEY,
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
# )


# # Master State

# class MasterState(BaseModel):
#     data: dict = {
#         "selected_agents": [],
#         "results": {},
#         "routing_reason": ""
#     }


# # Router Node (structured output INLINE)
# async def router_node(state: MasterState, config):
#     user_query = config["configurable"]["user_query"]
#     schema = RouterOutput.model_json_schema()

#     completion = client.chat.completions.create(
#         model="gemini-2.5-flash",
#         messages=[
#             {"role": "system", "content": MASTER_AGENT_ROUTER_PROMPT},
#             {"role": "user", "content": user_query}
#         ],
#         response_format={
#             "type": "json_schema",
#             "json_schema": {
#                 "name": "RouterOutput",
#                 "schema": schema
#             }
#         }
#     )

#     raw = completion.choices[0].message.content
#     parsed = json.loads(raw)
#     result = RouterOutput.model_validate(parsed)

#     state.data["selected_agents"] = result.selected_agents
#     state.data["routing_reason"] = result.reason
#     return state


# # Worker Node Factory

# def make_node(agent, key):

#     async def node(state: MasterState, config):
#         user_query = config["configurable"]["user_query"]
#         out = await agent.run(user_query)
#         state.data["results"][key] = out
#         return state

#     return node



# # Synthesizer Node (structured output INLINE)

# async def synth_node(state: MasterState, config):
#     user_query = config["configurable"]["user_query"]

#     schema = SynthOutput.model_json_schema()

#     completion = client.chat.completions.create(
#         model="gemini-2.5-flash",
#         messages=[
#             {"role": "system", "content": SYNTH_PROMPT},
#             {
#                 "role": "user",
#                 "content": f"User query:\n{user_query}\nAgent outputs:\n{state.results}"
#             }
#         ],
#         response_format={
#             "type": "json_schema",
#             "json_schema": {
#                 "name": "SynthOutput",
#                 "schema": schema
#             }
#         }
#     )

#     raw = completion.choices[0].message.content
#     parsed = json.loads(raw)
#     result = SynthOutput.model_validate(parsed)

#     state.data["results"]["SYNTHESIZED"] = {
#         "summary": result.final_summary,
#         "recommendations": result.recommendations,
#         "tables": [t.model_dump() for t in result.tables],
#         "charts": [c.model_dump() for c in result.charts]
#     }

#     return state


# # ---------------------------------------------------
# # Report Node
# # ---------------------------------------------------
# async def report_node(state: MasterState, config):
#     user_query = config["configurable"]["user_query"]
#     ctx = state.data["results"]["SYNTHESIZED"]
#     state.data["results"]["REPORT"] = await report_agent.run(user_query, ctx)
#     return state


# # ---------------------------------------------------
# # BUILD GRAPH
# # ---------------------------------------------------
# graph = StateGraph(MasterState)

# graph.add_node("router", router_node)
# graph.add_node("synth", synth_node)
# graph.add_node("report", report_node)

# worker_nodes = {
#     "IQVIA Insights Agent": ("IQVIA", iqvia_agent),
#     "Patent Landscape Agent": ("PATENTS", patents_agent),
#     "Clinical Trials Agent": ("CLINICAL", clinical_agent),
#     "Internal Knowledge Agent": ("INTERNAL", internal_agent),
#     "Web Intelligence Agent": ("WEB", web_agent),
# }

# # Create worker nodes
# for agent_name, (key, agent) in worker_nodes.items():
#     graph.add_node(f"call_{key.lower()}", make_node(agent, key))


# # Router → selected agents
# def choose_agents(state: MasterState):
#     return state.data["selected_agents"]


# graph.add_conditional_edges(
#     "router",
#     choose_agents,
#     {name: f"call_{key.lower()}" for name, (key, _) in worker_nodes.items()}
# )

# # Worker → synth
# for _, (key, _) in worker_nodes.items():
#     graph.add_edge(f"call_{key.lower()}", "synth")

# # Synth → report → END
# graph.add_edge("synth", "report")
# graph.add_edge("report", END)

# graph.set_entry_point("router")

# master_chain = graph.compile()

# # ---------------------------------------------------
# # Public Run Function
# # ---------------------------------------------------
# async def run_master_agent(query: str):
#     state = MasterState()
#     final = await master_chain.ainvoke(
#         state,
#         config={"configurable": {"user_query": query}}  
#     )
#     return final


from langgraph.graph import StateGraph, END
from pydantic import BaseModel
import json
from app.utils.schemas import RouterOutput, SynthOutput
from app.utils.prompts import MASTER_AGENT_ROUTER_PROMPT, SYNTH_PROMPT
from app.agents import (
    iqvia_agent, patents_agent,
    clinical_agent, internal_agent, web_agent,
    report_agent
)
from app.config.settings import settings
from openai import OpenAI


client = OpenAI(
    api_key=settings.GOOGLE_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


# ---------------------------------------------------------------------
# MASTER STATE — only store simple top-level keys
# ---------------------------------------------------------------------
class MasterState(BaseModel):
    selected_agents: list = []
    routing_reason: str = ""
    results: dict = {}  # safe when workers run sequentially


# ---------------------------------------------------------------------
# ROUTER NODE — selects agents
# ---------------------------------------------------------------------
async def router_node(state: MasterState, config):
    user_query = config["configurable"]["user_query"]
    schema = RouterOutput.model_json_schema()

    completion = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content": MASTER_AGENT_ROUTER_PROMPT},
            {"role": "user", "content": user_query}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "RouterOutput", "schema": schema}
        }
    )

    parsed = json.loads(completion.choices[0].message.content)
    result = RouterOutput.model_validate(parsed)

    state.selected_agents = result.selected_agents
    state.routing_reason = result.reason
    return state


# ---------------------------------------------------------------------
# WORKER EXECUTION NODE — sequential execution (NO MERGE PROBLEMS)
# ---------------------------------------------------------------------
worker_map = {
    "IQVIA Insights Agent": ("IQVIA", iqvia_agent),
    "Patent Landscape Agent": ("PATENTS", patents_agent),
    "Clinical Trials Agent": ("CLINICAL", clinical_agent),
    "Internal Knowledge Agent": ("INTERNAL", internal_agent),
    "Web Intelligence Agent": ("WEB", web_agent),
}

async def run_workers_node(state: MasterState, config):
    user_query = config["configurable"]["user_query"]

    for agent_name in state.selected_agents:
        key, agent = worker_map[agent_name]
        print(agent_name, "CALLED")
        output = await agent.run(user_query)
        state.results[key] = output

    return state


# ---------------------------------------------------------------------
# SYNTH NODE
# ---------------------------------------------------------------------
async def synth_node(state: MasterState, config):

    user_query = config["configurable"]["user_query"]
    schema = SynthOutput.model_json_schema()

    completion = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content": SYNTH_PROMPT},
            {"role": "user", "content": f"User query:\n{user_query}\n\nAgent outputs:\n{state.results}"}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "SynthOutput", "schema": schema}
        }
    )

    parsed = json.loads(completion.choices[0].message.content)
    result = SynthOutput.model_validate(parsed)

    state.results["SYNTHESIZED"] = {
        "summary": result.final_summary,
        "recommendations": result.recommendations,
        "tables": [t.model_dump() for t in result.tables],
        "charts": [c.model_dump() for c in result.charts]
    }

    return state


# ---------------------------------------------------------------------
# REPORT NODE
# ---------------------------------------------------------------------
async def report_node(state: MasterState, config):
    user_query = config["configurable"]["user_query"]
    ctx = state.results["SYNTHESIZED"]

    print("Generating final report...")

    pdf = await report_agent.run(user_query, ctx)
    state.results["REPORT"] = pdf
    return state


# ---------------------------------------------------------------------
# BUILD GRAPH (SEQUENTIAL — SAFE)
# ---------------------------------------------------------------------
graph = StateGraph(MasterState)

graph.add_node("router", router_node)
graph.add_node("run_workers", run_workers_node)
graph.add_node("synth", synth_node)
graph.add_node("report", report_node)

graph.set_entry_point("router")

graph.add_edge("router", "run_workers")
graph.add_edge("run_workers", "synth")
graph.add_edge("synth", "report")
graph.add_edge("report", END)

master_chain = graph.compile()


# ---------------------------------------------------------------------
# PUBLIC ENTRY FUNCTION
# ---------------------------------------------------------------------
async def run_master_agent(query: str):
    state = MasterState()
    final = await master_chain.ainvoke(
        state,
        config={"configurable": {"user_query": query}}
    )
    return final

