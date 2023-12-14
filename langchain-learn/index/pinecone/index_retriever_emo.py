from dotenv import load_dotenv

load_dotenv()

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
import pinecone


# initialize pinecone
pinecone.init(
    api_key="913f6bcc-e24d-4a5d-b21a-adcbb55f278a",  # find at app.pinecone.io
    environment="northamerica-northeast1-gcp"  # next to api key in console
)

index_name = "chatbot"
embeddings = OpenAIEmbeddings()
docsearch = Pinecone.from_existing_index(index_name=index_name, embedding=embeddings)

query = "今日简史这本书的主题是什么？"
docs = docsearch.similarity_search("hello")

print(docs[0].page_content)
