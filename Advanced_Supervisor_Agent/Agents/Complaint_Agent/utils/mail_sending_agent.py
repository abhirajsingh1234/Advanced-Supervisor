from langgraph.graph import StateGraph,add_messages
from typing import TypedDict,Annotated,List,Optional
from langchain.tools import tool
from langchain_openai import ChatOpenAI
import pyodbc
from langchain_core.messages import HumanMessage,AIMessage,RemoveMessage,BaseMessage,ToolMessage
from pydantic import Field,BaseModel
import requests
from Agents.Complaint_Agent.utils.mail_sending_tool import mail_send
import os
from langgraph.types import interrupt,Command
from langgraph.graph import START,END
from langgraph.checkpoint.memory import MemorySaver
import time
import uuid
from Agents.Complaint_Agent.utils.Prompts import mail_sys_prompt

checkpointer = MemorySaver()
llm = ChatOpenAI(model = 'gpt-4o-mini',api_key ="  ",temperature =0.5)

class FetchToolInput(TypedDict):
    send_to : List[str] = Field(description="abhirajsingh.rajpurohit@idolizesolutions.com")
    cc_mail: List[str] = Field(default = None, description="currently null")
    subject : str = Field(description="create a formal subject according to the given message")
    body : str = Field(description="create a formal mail body from the given message")
    flag : bool = Field(description="True if user really is complaining, else False")


def communication_agent(input_message):
    """
    Input:
         input_message : mail id to whom mail needs to be sent, the status about the document download process along with the document name and webtop id.

    Output:
         str : string data saying that the email was sent or there was an issue in sending the mail.
    """
    try:
       print(f"reached here : {input_message['input']}")
       result = llm.with_structured_output(FetchToolInput).invoke([HumanMessage(content = mail_sys_prompt.format(input_message = input_message['input']))])
       print(result)
       
       if result['flag']:

         mail_send(result["send_to"],result["cc_mail"],result["subject"],result["body"],[])

       else : 

         return {'output':f"internal error occured while sending the mail  please try again..."}
          
       print('done')
       return  {'output' : f"escalated a mail to support team :- subject -'{result['subject']}' and body -'{result['body']}' has been successfully sent to mail id '{result['send_to'][0]}'"}

   
    except Exception as e :
      return {'output':f"internal error occured while sending the mail {e}"}
    

# communication_agent('document has been successfully downloaded for webtop id 23423fdd , send a mail to abhirajsingh.rajpurohit@idolizesolutions.com')

