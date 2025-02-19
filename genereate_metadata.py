import os
from dotenv import load_dotenv, find_dotenv
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq.chat_models import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Literal
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from IPython.core.display import Markdown
from langchain_core.runnables import RunnableParallel
from langchain_core.messages import HumanMessage, AIMessage
import warnings
import dotenv

# Load environment variables
dotenv.load_dotenv(find_dotenv())

GROQ_API_KEY = os.getenv("GROQQ_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

os.environ["GROQ_API_KEY"] = GROQ_API_KEY
os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"]=LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"]="advanced-rag"
os.environ["TAVILY_API_KEY"]=TAVILY_API_KEY

warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from langchain.output_parsers import JsonOutputKeyToolsParser

# Định nghĩa mô hình đầu ra
class MetadataExtractor(BaseModel):
    category: Optional[str] = Field(
        None, description="法律の分野 (null nếu không có thông tin)"
    )
    keywords: List[str] = Field(
        default=[], description="重要なキーワードのリスト"
    )
    applicable_entities: List[str] = Field(
        default=[], description="適用対象となる機関や団体"
    )
    reference_articles: List[str] = Field(
        default=[], description="関連する他の条文のリスト"
    )

# Tạo prompt template
metadata_extraction_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """
        あなたはAI言語モデルアシスタントです。
        プロンプト（Metadata抽出用）
        以下の法律文書から、指定されたメタデータを抽出し、JSON形式で出力してください。
        必ずすべての項目を埋めてください。情報が不明な場合は「不明」や適切な推測を行ってください。
        """),
        ("human", "法律文書: {document}")
    ]
)

llm = ChatGroq(model="llama3-70b-8192", temperature=0)
# Kết hợp với LLM và định dạng output JSON
metadata_extractor_chain = metadata_extraction_prompt | llm.with_structured_output(
    MetadataExtractor
)


# Load full document from json file
import json

with open("./full_corpus_110225_metadata_final.json", "r", encoding="utf-8") as f:
    docs = json.load(f)

print(len(docs))

from tqdm import tqdm

try:
    for doc in tqdm(docs):
        print(len(doc["metadata"]))
        if len(doc["metadata"]) > 10:
            print("Skip")
            continue
        result = metadata_extractor_chain.invoke({"document": doc["content"]})
        if result.category:
            doc["metadata"]["category"] = result.category
        if result.keywords:
            doc["metadata"]["keywords"] = result.keywords
        if result.applicable_entities:
            doc["metadata"]["applicable_entities"] = result.applicable_entities
        if result.reference_articles:
            doc["metadata"]["reference_articles"] = result.reference_articles
except:
    pass

with open("./full_corpus_110225_metadata_final.json", "w", encoding="utf-8") as f:
    json.dump(docs, f, ensure_ascii=False, indent=2)