import shutil
import time
import gc
from pathlib import Path
from typing import List
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

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
    del vectordb
    gc.collect()
    return

def get_document_count(persist_directory: str, collection_name: str, embedding_model):
    """
    Kiểm tra và trả về số lượng tài liệu trong index.
    """
    vectordb = Chroma(
        persist_directory=persist_directory, 
        collection_name=collection_name, 
        embedding_function=embedding_model
    )
    count = vectordb._collection.count()
    del vectordb
    gc.collect()
    return count

# ======================= CHẠY CHƯƠNG TRÌNH ======================= #
if __name__ == "__main__":
    collection_name = "my_collection"
    persist_directory = "./chroma_db"  # Giữ nguyên thư mục để cập nhật dễ dàng

    # 🔹 Danh sách tài liệu ban đầu
    docs = [
        Document(page_content="This is the content of document 1.", metadata={"source": "doc1"}),
        Document(page_content="Content of document 2 is here.", metadata={"source": "doc2"}),
        Document(page_content="Document 3 contains different content.", metadata={"source": "doc3"})
    ]

    # 🔹 Khởi tạo embedding model
    embed_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")

    print("🛠 Creating the index for the first time...")
    create_or_update_index(
        collection_name=collection_name,
        embedding_model=embed_model,
        persist_directory=persist_directory,
        all_docs=docs,
        clear_persist_folder=True  # Xóa dữ liệu cũ nếu có, tạo lại từ đầu
    )

    time.sleep(2)  # Chờ một chút để đảm bảo dữ liệu được lưu

    # 🔹 Kiểm tra số lượng tài liệu sau khi tạo index lần đầu
    initial_count = get_document_count(persist_directory, collection_name, embed_model)
    print(f"\n📊 Total documents after first indexing: {initial_count}")

    # 🔹 Danh sách tài liệu mới để cập nhật
    new_docs = [
        Document(page_content="Updated content for document A.", metadata={"source": "docA"}),
        Document(page_content="This is a completely new document B.", metadata={"source": "docB"}),
        Document(page_content="Another fresh document C.", metadata={"source": "docC"})
    ]

    print("\n🔄 Updating the index with new documents...")
    create_or_update_index(
        collection_name=collection_name,
        embedding_model=embed_model,
        persist_directory=persist_directory,
        all_docs=new_docs,
        clear_persist_folder=True  # Không xóa dữ liệu cũ, chỉ cập nhật thêm
    )

    # 🔹 Kiểm tra số lượng tài liệu sau khi cập nhật
    updated_count = get_document_count(persist_directory, collection_name, embed_model)
    print(f"\n📊 Total documents after update: {updated_count}")

    print("\n✅ Index has been created and updated successfully!")
