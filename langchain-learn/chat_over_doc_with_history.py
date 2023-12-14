from dotenv import load_dotenv
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS

load_dotenv()

from langchain.document_loaders import TextLoader
loader = TextLoader("./state_of_the_union.txt",encoding="utf-8")
documents = loader.load()

text_splitter = CharacterTextSplitter(chunk_size=256, chunk_overlap=0)
documents = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(documents, embeddings)

from langchain.memory import ConversationBufferMemory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
qa = ConversationalRetrievalChain.from_llm(OpenAI(temperature=0), vectorstore.as_retriever(),
                                           memory=memory,
                                           verbose=True)

while True:
    query = input("Enter:")
    # query = "What did the president say about Ketanji Brown Jackson"
    result = qa({"question": query})
    print(result["answer"])


