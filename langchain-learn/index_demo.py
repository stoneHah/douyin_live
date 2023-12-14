from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI

load_dotenv()

from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.llms import OpenAI

from langchain.document_loaders import TextLoader
from langchain.indexes import VectorstoreIndexCreator


loader = TextLoader('./state_of_the_union.txt',encoding="utf-8")

index = VectorstoreIndexCreator().from_loaders([loader])

query = "What did the president say about Ketanji Brown Jackson"
res = index.query(query)
print(res)

res = index.query_with_sources(query)
print(res)


# llm = ChatOpenAI(temperature=0.6)
#
# qa = ConversationalRetrievalChain.from_llm(llm, vectorstoreindex.vectorstore.as_retriever())
#
# chat_history = []
# query = "What did the president say about Ketanji Brown Jackson"
# result = qa({"question": query, "chat_history": chat_history})
