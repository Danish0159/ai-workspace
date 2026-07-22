import os

from dotenv import load_dotenv

load_dotenv()

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.checkpoint.memory import InMemorySaver

DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./documents")
api_key = os.getenv("OPENROUTER_API_KEY")

agent = None
document_uploaded = False


def process_documents():
    global agent, document_uploaded

    loader = PyPDFDirectoryLoader(DOCUMENTS_PATH)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splitted_docs = splitter.split_documents(documents=docs)

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )
    vector_store = InMemoryVectorStore.from_documents(
        documents=splitted_docs,
        embedding=embeddings,
    )

    llm = ChatOpenAI(
        model="openai/gpt-5",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
    )

    @tool
    def retrieve_context(query: str):
        """Retrieve documents relevant to a query from the knowledge base."""
        context = ""
        retrieved = vector_store.similarity_search(query=query, k=3)
        for doc in retrieved:
            context = doc.page_content + "\n\n"

        return context

    system_prompt = """You are a helpful assistant that answers questions using retrieved context. 
        My knowledge base consists of the details from the uploaded document. 
        ALWAYS use the `retrieve_context` tool for questions requiring external knowledge."""

    memory = InMemorySaver()

    agent = create_agent(
        model=llm,
        tools=[retrieve_context],
        system_prompt=system_prompt,
        checkpointer=memory,
    )
    document_uploaded = True


def chat(message: str) -> str:
    response = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        {"configurable": {"thread_id": 1}},
    )
    return response["messages"][-1].content
