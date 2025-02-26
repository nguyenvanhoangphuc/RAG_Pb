from pathlib import Path
import shutil

def create_or_update_index(collection_name: str, embedding_model, persist_directory: str, 
                           all_docs: List[Document], clear_persist_folder: bool = False):
    """
    Tạo hoặc cập nhật index vector.
    - Nếu `clear_persist_folder=True`, sẽ xóa thư mục lưu trữ trước khi tạo lại từ đầu.
    - Nếu `clear_persist_folder=False`, sẽ giữ dữ liệu cũ và chỉ cập nhật tài liệu mới.
    """
    pf = Path(persist_directory)
    if clear_persist_folder:
        if pf.exists() and pf.is_dir():
            print(f"Deleting the content of: {pf}")
            shutil.rmtree(pf)
        pf.mkdir(parents=True, exist_ok=True)
        print(f"Recreated the directory at: {pf}")

    print("\nGenerating and persisting the embeddings..")
    print("Persist Directory:", persist_directory)
    
    vectordb = Chroma.from_documents(
        collection_name=collection_name,
        documents=all_docs, 
        embedding=embedding_model, 
        persist_directory=persist_directory
    )
    vectordb.persist()
    
    # Đóng connection để tránh lỗi "readonly database"
    # del vectordb
    # gc.collect()
    return vectordb

def sematic_reference(state):
    """
    Thực hiện embedding giữa các câu trong cùng một điều rồi lấy ra các câu có embedding gần nhau nhất, 
    sau đó đưa cho LLM để đánh giá có phải là câu liên quan trực tiếp không.
    Sử dụng ChromaDB để lấy ra các câu có embedding gần nhau nhất.
    """
    print("---SEMANTIC REFERENCE---")
    for key, value in state.items():
        print(key, value)

    questions = state["questions"]
    # tạo ra một list chứa các câu trong cùng một điều
    question_same_dieu_dict = {}
    for question in questions:
        # print("question", question)
        # print('question["question_content"]', question["question_content"])
        # print('question["question_content"].metadata', question["question_content"].metadata)
        dieu_id = question["question_content"].metadata["article_title"] + "_" + question["question_content"].metadata["article_number"]
        if dieu_id in question_same_dieu_dict:
            question_same_dieu_dict[dieu_id].append(question)
        else:
            question_same_dieu_dict[dieu_id] = [question]

    embed_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
    sematic_reference_dict = {}
    # duyệt qua từng điều trong question_same_dieu_dict
    for dieu, value in question_same_dieu_dict.items(): 
        print("dieu", dieu)
        print("value", value)
        new_value = [val["question_content"] for val in value]
        vectordb = create_or_update_index(
            collection_name="same_dieu",
            embedding_model=embed_model,
            persist_directory="./same_dieu_db",
            all_docs=new_value,
            clear_persist_folder=True  # Xóa dữ liệu cũ nếu có, tạo lại từ đầu
        )
        retriever_dieu = vectordb.as_retriever(search_kwargs={"k": 6})
        # Duyệt qua từng câu trong value để tìm các câu có embedding gần nhau nhất
        for question in value:
            # print("question", question)
            docs = retriever_dieu.get_relevant_documents(question["question_content"].page_content)
            # print("docs", docs)
            # print('question["question_content"]', question["question_content"])
            # loại chính question ra khỏi docs
            docs = [doc for doc in docs if doc.page_content != question["question_content"].page_content]
            id_question = question["question_content"].page_content
            sematic_reference_dict[id_question] = docs

    for question in questions:
        id_question = question["question_content"].page_content
        question["sematic_reference"] = sematic_reference_dict[id_question]

    state["questions"] = questions
    return state

reference_graph_state_sematic = sematic_reference(graph_state)