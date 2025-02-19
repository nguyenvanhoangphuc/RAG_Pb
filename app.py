from uuid import uuid4
from langgraph.graph import StateGraph, END
from langchain_core.documents import Document

llm = ChatGroq(model="llama3-70b-8192", temperature=0)
prompt = ChatPromptTemplate.from_template(router_prompt_template)
question_router = prompt | llm.bind_tools(tools=[VectorStore, SearchEngine])

hallucination_grader_chain = (
    RunnableParallel(
        {
            "response": itemgetter("response"),
            "context": lambda x: "\n\n".join([c.page_content for c in x["context"]]),
        }
    )
    | hallucination_grader_prompt
    | llm.with_structured_output(HallucinationGrader, method="json_mode")
)

answer_grader_chain = answer_grader_prompt | llm.with_structured_output(
    AnswerGrader, method="json_mode"
)

# định nghĩa some function
class AgentSate(TypedDict):
    """The dictionary keeps track of the data required by the various nodes in the graph"""

    query: str
    chat_history:list[BaseMessage]
    generation: str
    documents: list[Document]


def retrieve_node(state: dict) -> dict[str, list[Document] | str]:
    """
    Retrieve relevent documents from the vectorstore

    query: str

    return list[Document]
    """
    query = state["query"]
    documents = retriever.invoke(input=query)
    return {"documents": documents}


def fallback_node(state: dict):
    """
    Fallback to this node when there is no tool call
    """
    query = state["query"]
    chat_history = state["chat_history"]
    generation = fallback_chain.invoke({"query": query, "chat_history": chat_history})
    return {"generation": generation}


def filter_documents_node(state: dict):
    filtered_docs = list()

    query = state["query"]
    documents = state["documents"]
    for i, doc in enumerate(documents, start=1):
        grade = grader_chain.invoke({"query": query, "context": doc})
        if grade.grade == "relevant":
            print(f"---CHUCK {i}: RELEVANT---")
            filtered_docs.append(doc)
        else:
            print(f"---CHUCK {i}: NOT RELEVANT---")
    return {"documents": filtered_docs}


def rag_node(state: dict):
    query = state["query"]
    documents = state["documents"]

    generation = rag_chain.invoke({"query": query, "context": documents})
    return {"generation": generation}


def web_search_node(state: dict):
    query = state["query"]
    results = tavily_search.invoke(query)
    documents = [
        Document(page_content=doc["content"], metadata={"source": doc["url"]})
        for doc in results
    ]
    return {"documents": documents}

def question_router_node(state: dict):
    query = state["query"]
    try:
        response = question_router.invoke({"query": query})
    except Exception:
        return "llm_fallback"

    if "tool_calls" not in response.additional_kwargs:
        print("---No tool called---")
        return "llm_fallback"

    if len(response.additional_kwargs["tool_calls"]) == 0:
        raise "Router could not decide route!"

    route = response.additional_kwargs["tool_calls"][0]["function"]["name"]
    if route == "VectorStore":
        print("---Routing to VectorStore---")
        return "VectorStore"
    elif route == "SearchEngine":
        print("---Routing to SearchEngine---")
        return "SearchEngine"

def should_generate(state: dict):
    filtered_docs = state["documents"]

    if not filtered_docs:
        print("---All retrived documents not relevant---")
        return "SearchEngine"
    else:
        print("---Some retrived documents are relevant---")
        return "generate"


def hallucination_and_answer_relevance_check(state: dict):
    llm_response = state["generation"]
    documents = state["documents"]
    query = state["query"]

    hallucination_grade = hallucination_grader_chain.invoke(
        {"response": llm_response, "context": documents}
    )
    if hallucination_grade.grade == "no":
        print("---Hallucination check passed---")
        answer_relevance_grade = answer_grader_chain.invoke(
            {"response": llm_response, "query": query}
        )
        if answer_relevance_grade.grade == "yes":
            print("---Answer is relevant to question---\n")
            return "useful"
        else:
            print("---Answer is not relevant to question---")
            return "not useful"
    print("---Hallucination check failed---")
    return "generate"

# định nghĩa workflow

workflow = StateGraph(AgentSate)
workflow.add_node("VectorStore", retrieve_node)
workflow.add_node("SearchEngine", web_search_node)
workflow.add_node("filter_docs", filter_documents_node)
workflow.add_node("fallback", fallback_node)
workflow.add_node("rag", rag_node)

workflow.set_conditional_entry_point(
    question_router_node,
    {
        "llm_fallback": "fallback",
        "VectorStore": "VectorStore",
        "SearchEngine": "SearchEngine",
    },
)

workflow.add_edge("VectorStore", "filter_docs")
workflow.add_edge("SearchEngine", "filter_docs")
workflow.add_conditional_edges(
    "filter_docs", should_generate, {"SearchEngine": "SearchEngine", "generate": "rag"}
)
workflow.add_conditional_edges(
    "rag",
    hallucination_and_answer_relevance_check,
    {"useful": END, "not useful": "SearchEngine", "generate": "rag"},
)

workflow.add_edge("fallback", END)

# định nghĩa app
app = workflow.compile(debug=False)

# giao diện
history = {}
session_id = str(uuid4())

if session_id not in history:
    history[session_id] = []

chat_history = history[session_id]

while True:
    query = input("Bạn: ")
    
    if query.lower() == "exit":
        print("Thoát chương trình.")
        break

    # Gọi mô hình với câu hỏi và lịch sử hội thoại
    try:
        result = app.invoke({"query": query, "chat_history": chat_history})
        
        # Tách câu trả lời và tài liệu truy xuất
        response = result["generation"]
        documents = result["documents"]
    except Exception:
        print("Câu hỏi này không thuộc trong chủ đề về y tế. Hãy đặt câu hỏi khác.")
        continue

    # Lưu vào lịch sử hội thoại
    chat_history.append({"human": query, "ai": response})

    print(f"AI: {response}")

    if documents:
        print("\nTài liệu liên quan:")
        for doc in documents:
            print(f"- {doc.page_content} (Nguồn: {doc.metadata['source']})")

    
    print("-" * 50)  # Dòng ngăn cách giữa các lần hỏi
