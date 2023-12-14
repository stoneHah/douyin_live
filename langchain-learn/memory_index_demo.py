from langchain.chains import ConversationalRetrievalChain
from dotenv import load_dotenv
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from langchain.memory.chat_message_histories import RedisChatMessageHistory
from langchain.vectorstores import Pinecone
import pinecone

load_dotenv()

message_history = RedisChatMessageHistory(url='redis://127.0.0.1:6379/0', ttl=600, session_id='my-session')
memory = ConversationBufferWindowMemory(memory_key="chat_history", chat_memory=message_history,
                                        k=2, return_messages=True)

# initialize pinecone
pinecone.init(
    api_key="913f6bcc-e24d-4a5d-b21a-adcbb55f278a",  # find at app.pinecone.io
    environment="northamerica-northeast1-gcp"  # next to api key in console
)

index_name = "chatbot"
embeddings = OpenAIEmbeddings()
docsearch = Pinecone.from_existing_index(index_name=index_name, embedding=embeddings)

llm = ChatOpenAI(temperature=0.6)

qa = ConversationalRetrievalChain.from_llm(llm=llm,
                                           retriever=docsearch.as_retriever(search_kwargs={'k':1}),
                                           memory=memory,
                                           verbose=True)

while True:
    q = input("输入问题:")
    result = qa({"question": q})
    print(result)

