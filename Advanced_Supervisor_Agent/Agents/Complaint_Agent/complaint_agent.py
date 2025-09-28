from Agents.Complaint_Agent.utils.mail_sending_agent import communication_agent
from typing import TypedDict
from langgraph.graph import START,END,StateGraph
from langgraph.checkpoint.memory import MemorySaver
from Agents.Complaint_Agent.utils.mail_sending_agent import communication_agent

checkpointer = MemorySaver()

class ComplaintState(TypedDict):
    input : str
    output : str

def complaint_agent(state : ComplaintState )-> ComplaintState:

    print('complaint_agent',state['input'])

    result = communication_agent(state['input'])

    print('agent_output', result)

    return {'output' : str(result) }

complaint_graph = StateGraph(ComplaintState)
complaint_graph.add_node('complaint_agent',communication_agent)

complaint_graph.add_edge(START,'complaint_agent')
complaint_graph.add_edge('complaint_agent',END)

complaint_compiled_graph = complaint_graph.compile()