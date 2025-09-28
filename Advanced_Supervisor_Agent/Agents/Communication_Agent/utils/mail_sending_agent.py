from langgraph.graph import StateGraph,add_messages
from typing import TypedDict,Annotated,List,Optional
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from langchain_core.messages import HumanMessage,AIMessage,RemoveMessage,BaseMessage,ToolMessage
from pydantic import Field,BaseModel

from Agents.Communication_Agent.utils.mail_sending_tool import mail_send
from langgraph.types import interrupt,Command
from langgraph.graph import START,END
from langgraph.checkpoint.memory import MemorySaver
from Agents.Communication_Agent.utils.sql_query import execute_sql_query
from Agents.Communication_Agent.utils.prompts import mail_sys_prompt

checkpointer = MemorySaver()
llm = ChatOpenAI(model = 'gpt-4o-mini',api_key =" ",temperature =0.5)

class FetchToolInput(TypedDict):
    send_to : List[str] = Field(description="extract the mail id from message to whom the mail needs to be sent")
    cc_mail: List[str] = Field(default = None, description="currently null")
    subject : str = Field(description="create a formal subject according to the given message")
    body : str = Field(description="create a formal mail body from the given message")
    include_attachment : bool = Field(description = "True if user explicitly says to send document in the mail, else False")
    file_path : List[str] = Field(default = None, description = "file path only included if include_attachment is True else None")

doc_name_extraction_message = """
system role: Extract ONLY the document name from the given input.
- Return only the raw document name text.
- Do not add quotes, explanations, or extra words.
- If multiple possible names exist, return the most relevant one only.
- Example: 
   Input: 'download me the vm summary for application id 123'
   Output: vm summary
"""


input_message = "send a mail to abhiraj.rajpurohit@idolizesolutions.com and inform that the document is downloaded"
@tool
def communication_agent( input_message : str ):
    """
    Input:
         input_message : mail id to whom mail needs to be sent, the status about the document download process along with the document name and webtop id.

    Output:
         str : string data saying that the email was sent or there was an issue in sending the mail.
    """
    try:
       document_name = llm.invoke([doc_name_extraction_message,input_message])
       print(document_name.content)
       extensions = execute_sql_query(f"select file_extension from [Doc_Repository].[dbo].[Document_List_Master]  where Process_ID = 'D000' and Doc_Name = '{document_name.content}'")
       print('EXTENSION IS : ',extensions)
       input_message = input_message + ' ,Extension : ' + extensions
       result = llm.with_structured_output(FetchToolInput).invoke([HumanMessage(content = mail_sys_prompt.format(input_message = input_message))])
       print(result)
 
       if result['include_attachment']:
         mail_send(result["send_to"],result["cc_mail"],result["subject"],result["body"],result["file_path"])
       else : 
         mail_send(result["send_to"],result["cc_mail"],result["subject"],result["body"],[])
          
       status = 202
       print(status)
       if int(status) == 202:
           return  f"email with subject '{result['subject']}' and body '{result['body']}' has been successfully sent to mail id '{result['send_to']}'"
       else :
           return f"there was an error sending mail to {result["send_to"]}"
   
    except Exception as e :
      return f"internal error occured while sending the mail {e}"
    

# communication_agent('document has been successfully downloaded for webtop id 23423fdd , send a mail to abhirajsingh.rajpurohit@idolizesolutions.com')