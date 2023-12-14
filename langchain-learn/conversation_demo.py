from langchain import LLMChain, PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from dotenv import load_dotenv
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from langchain.memory.chat_message_histories import RedisChatMessageHistory

from custome_chain import CustomeConversationChain


load_dotenv()


#  memory
message_history = RedisChatMessageHistory(url='redis://192.168.1.9:6379/0',ttl=600, session_id='my-session3')
# llm
llm = ChatOpenAI(model='gpt-3.5-turbo-16k',temperature=0.6,verbose=True)

chain = CustomeConversationChain.from_llm(llm=llm, chat_memory=message_history,
                                             system_prompt="我想要你扮演一位python高级工程师",
                                          verbose=True)

while True:
    q = input('Enter:')
    predict = chain.run(human_input=q)
    print("==start==",predict,"==end==")