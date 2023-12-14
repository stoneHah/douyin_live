from dotenv import load_dotenv

load_dotenv()

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import TextLoader


loader = TextLoader('../../xiaoshutong.txt', encoding="utf-8")

documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings()

db = FAISS.from_documents(docs, embeddings)

query = "今日简史这本书的主题是什么？"
docs = db.similarity_search("hello")

print(docs[0].page_content)
