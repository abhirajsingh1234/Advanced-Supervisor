from Agents.Complaint_Agent.utils.mail_sending_agent import communication_agent
from typing import TypedDict
from langgraph.graph import START,END,StateGraph
from langgraph.checkpoint.memory import MemorySaver
from Agents.Communication_Agent.utils.mail_sending_agent import communication_agent

checkpointer = MemorySaver()

class ComplaintState(TypedDict):
    input : str
    output : str

def communicator_agent(state : ComplaintState )-> ComplaintState:

    print('complaint_agent',state['input'])

    result = communication_agent(state['input'])

    print('agent_output', result)

    return {'output' : str(result) }

communication_graph = StateGraph(ComplaintState)
communication_graph.add_node('complaint_agent',communicator_agent)

communication_graph.add_edge(START,'complaint_agent')
communication_graph.add_edge('complaint_agent',END)

compiled_communication_graph = communication_graph.compile()