import os
import pickle
from typing import Dict, Set, List,TypedDict
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from pydantic import BaseModel,Field
from langgraph.graph import StateGraph,END,START
from langchain_core.retrievers import BaseRetriever
from langchain_core.messages import HumanMessage
from langchain.retrievers.multi_query import MultiQueryRetriever
from Agents.Query_Agent.prompts import retrieval_argumented_generation_system_prompt
from Agents.Query_Agent.utils.internal_rag_pipeline import retrieval_for_multiquery_ambigious_or_normal
from Agents.Query_Agent.utils.rag_state import RAG_State,llm

def rag_chain(state : RAG_State) -> RAG_State:

    data = retrieval_for_multiquery_ambigious_or_normal(state['input'])
    data = data.split(' ')
    context = ', '.join(data)

    print(f"FINAL CONTEXT : {context}")

    rag_result = llm.invoke([HumanMessage(retrieval_argumented_generation_system_prompt.format(query = state['input'], context = context))])

    print('LLM RESULT : ',rag_result.content)

    return {'output' : rag_result.content}


rag_graph = StateGraph(RAG_State)
rag_graph.add_node('rag_retrieval',rag_chain)
rag_graph.add_edge(START,'rag_retrieval')
rag_graph.add_edge('rag_retrieval',END)
ready_rag_graph = rag_graph.compile()

# query = {"input":'what is frontend developmeeeement is','output':None}

# output = ready_rag_graph.invoke(query)

# print(output['output'])