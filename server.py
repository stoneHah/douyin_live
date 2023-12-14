import asyncio
import os
import random
import string
import threading
from queue import Queue
from typing import Union, Dict, Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain import LLMChain, SerpAPIWrapper
from langchain.agents import initialize_agent, AgentType
from langchain.callbacks.manager import CallbackManager
from langchain.chat_models import ChatOpenAI
from langchain.memory import RedisChatMessageHistory, ConversationBufferWindowMemory
from langchain.prompts import SystemMessagePromptTemplate, ChatPromptTemplate
from langchain.schema import HumanMessage, BaseChatMessageHistory
from langchain.tools import Tool
from pydantic import BaseModel
from starlette.responses import JSONResponse

from custom_callback import StreamingLLMCallbackHandler, STOP_TOKEN, StreamTokenBuffer, AgentStreamingLLMCallbackHandler
from conversation import ConversationFactory, gen_chain
from sse_starlette.sse import EventSourceResponse
from custome_chain import CustomeConversationChain
from general_agent import GeneralChatGPT

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DCResponse(BaseModel):
    def __init__(self, code: str, msg: str, data: Dict[str, Any] = None):
        self.code = code
        self.msg = msg
        self.data = data or {}

    @staticmethod
    def ok(msg: str = "OK", data: Dict[str, Any] = None):
        return Response("200", msg, data)

    @staticmethod
    def error(code: str = "400", msg: str = "Error", data: Dict[str, Any] = None):
        return Response(code, msg, data)


# class CustomeConversationChain(LLMChain):
#
#     @classmethod
#     def from_llm(cls,chat_memory: BaseChatMessageHistory,system_prompt:str =None):
#

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(str(exc), status_code=500)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.post("/upload")
async def create_upload_file(file: UploadFile = File(...), conversion_id: Union[str, None] = None):
    if file is None:
        return Response.error(code=400, msg="No file provided")

    avaiable_file_type = ["pdf", "doc", "docx", "txt"]
    filename, ext = os.path.splitext(file.filename)
    if ext[1:] not in avaiable_file_type:
        return Response.error(code=400, msg="Invalid file type")

    random_name = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=8))
    file_path = os.path.join("upload_files", f"{filename}_{random_name}{ext}")
    with open(file_path, "wb") as out_file:
        content = await file.read()
        out_file.write(content)

    # conversion = Conversion(conversion_id)
    # # 索引文件
    # conversion.create_index_file(file_path)
    #
    # return Response.ok(data={"conversion_id": conversion.conversion_id})


class PromptRequest(BaseModel):
    system_prompt: str = None
    conversation_id: str
    prompt: str
    internet: bool = False


conversation_factory = ConversationFactory()
conversation_llm_chain = {}


def build_tools(internet: bool = False):
    tools = []
    if internet:
        search = SerpAPIWrapper()
        tools.append(Tool(
                name="Current Search",
                func=search.run,
                description="useful for when you need to answer questions about current events or the current state of the world"
            ))
    return tools

enter_special_char = "|!Enter!|"


def build_agent(promptRequest, memory):
    internet = promptRequest.internet
    print("接入互联网:", internet)

    if internet:
        stream_handler = AgentStreamingLLMCallbackHandler(answer_prefix_tokens=['Final', ' Answer', '",\n', '   ', ' "', 'action', '_input', '":', ' "'])
        llm = ChatOpenAI(streaming=True, model_name='gpt-3.5-turbo', verbose=True,
                         callback_manager=CallbackManager([stream_handler]),
                         temperature=0.6)

        tools = build_tools(internet)
        agent_chain = initialize_agent(tools, llm, agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, verbose=True,
                                       memory=memory,
                                       callback_manager=CallbackManager([stream_handler]))
    else:
        # llm
        stream_handler = StreamingLLMCallbackHandler()
        llm = ChatOpenAI(streaming=True, model_name='gpt-3.5-turbo',
                         callback_manager=CallbackManager([stream_handler]), verbose=True,
                         temperature=0.6)
        agent_chain = GeneralChatGPT.from_llm_and_tools(memory=memory,
                                                        llm=llm,
                                                        system_base_prompt=promptRequest.system_prompt,
                                                        verbose=True
                                                        )

    return agent_chain,stream_handler


@app.post("/chat")
async def chat_stream(request: Request, promptRequest: PromptRequest):

    #  memory
    message_history = RedisChatMessageHistory(url='redis://192.168.1.9:6379/0', session_id=promptRequest.conversation_id)
    memory = ConversationBufferWindowMemory(memory_key="chat_history", chat_memory=message_history,
                                            k=10,return_messages=True)

    agent_chain,stream_handler = build_agent(promptRequest, memory)


    def query():
        resp = agent_chain.run(input=promptRequest.prompt)
        # resp = llm_chain.predict(human_input=promptRequest.prompt)
        # resp = llm_chain([HumanMessage(content=str)])
        print(resp)

    t = threading.Thread(target=query)
    t.start()

    async def event_generator(stream_token_buffer: StreamTokenBuffer):
        for event,token in stream_token_buffer.stream_tokens():
            # If client closes connection, stop sending events
            if await request.is_disconnected():
                break

            yield {
                "event": event,
                "data": token.replace("\n",enter_special_char)
            }

    return EventSourceResponse(event_generator(stream_handler))


STREAM_DELAY = 1  # second
RETRY_TIMEOUT = 15000  # milisecond


# @app.get('/stream')
# async def message_stream(request: Request):
#     def new_messages():
#         # Add logic here to check for new messages
#         yield 'Hello World'
#
#     async def event_generator():
#         a = 1
#         while True:
#             # If client closes connection, stop sending events
#             if await request.is_disconnected():
#                 break
#
#             # Checks for new messages and return them to client if any
#             if new_messages():
#                 yield {
#                     "event": "new_message",
#                     "id": "message_id",
#                     "retry": RETRY_TIMEOUT,
#                     "data": "message_content"
#                 }
#
#             await asyncio.sleep(STREAM_DELAY)
#             a += 1
#             if a > 5:
#                 yield {
#                     "event": "end",
#                     "id": "message_id",
#                     "retry": RETRY_TIMEOUT,
#                     "data": "message_content"
#                 }
#                 break
#
#     return EventSourceResponse(event_generator())



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
