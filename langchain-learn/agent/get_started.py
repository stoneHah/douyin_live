from typing import Dict, Any, List, Optional, Union
from uuid import UUID

from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from dotenv import load_dotenv
from langchain.schema import BaseMessage, AgentFinish, AgentAction

load_dotenv()

class MyCallback(BaseCallbackHandler):

    def on_chain_end(self, outputs: Dict[str, Any], *, run_id: UUID, parent_run_id: Optional[UUID] = None,
                     **kwargs: Any) -> Any:
        return super().on_chain_end(outputs, run_id=run_id, parent_run_id=parent_run_id, **kwargs)

    def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], *, run_id: UUID,
                       parent_run_id: Optional[UUID] = None, **kwargs: Any) -> Any:
        return super().on_chain_error(error, run_id=run_id, parent_run_id=parent_run_id, **kwargs)

    def on_agent_action(self, action: AgentAction, *, run_id: UUID, parent_run_id: Optional[UUID] = None,
                        **kwargs: Any) -> Any:
        print("on_agent_action:tool=",action.tool,"tool_input=",action.tool_input)
        return super().on_agent_action(action, run_id=run_id, parent_run_id=parent_run_id, **kwargs)

    def on_agent_finish(self, finish: AgentFinish, *, run_id: UUID, parent_run_id: Optional[UUID] = None,
                        **kwargs: Any) -> Any:
        print("on_agent_finish:final=", finish.return_values)
        return super().on_agent_finish(finish, run_id=run_id, parent_run_id=parent_run_id, **kwargs)


llm = ChatOpenAI(temperature=0)
tools = load_tools(["llm-math"], llm=llm)

agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

my_callback = MyCallback()
agent.run("3*2=?",callbacks=[my_callback])