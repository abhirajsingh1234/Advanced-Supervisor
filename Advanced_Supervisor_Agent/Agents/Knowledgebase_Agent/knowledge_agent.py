
from Agents.Knowledgebase_Agent.utils.knowledge_fetcher import data_fetcher
from typing import TypedDict
from langgraph.graph import START,END,StateGraph

class KnowledgeState(TypedDict):
    input : str
    output : str

def knowledge_agent(state : KnowledgeState)-> KnowledgeState:

    result = data_fetcher(state['input'])

    return { 'output' :result}

knowledge_graph = StateGraph(KnowledgeState)
knowledge_graph.add_node('knowledge_agent',knowledge_agent)

knowledge_graph.add_edge(START,'knowledge_agent')
knowledge_graph.add_edge('knowledge_agent',END)

knowledge_compiled_graph = knowledge_graph.compile()