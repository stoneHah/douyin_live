from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI

load_dotenv()

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.document_loaders import TextLoader
import pinecone


loader = TextLoader('../../xiaoshutong.txt', encoding="utf-8")

documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings()

# initialize pinecone
pinecone.init(
    api_key="913f6bcc-e24d-4a5d-b21a-adcbb55f278a",  # find at app.pinecone.io
    environment="northamerica-northeast1-gcp"  # next to api key in console
)

index_name = "chatbot"

docsearch = Pinecone.from_documents(docs, embeddings, index_name=index_name)

query = "今日简史这本书的主题是什么？"
docs = docsearch.similarity_search(query)

print(docs[0].page_content)
