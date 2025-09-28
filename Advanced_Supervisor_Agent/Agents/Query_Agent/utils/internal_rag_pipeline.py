import os
import pickle
from typing import Dict, Set, List
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_core.messages import HumanMessage
from Agents.Query_Agent.utils.prompts import multiquery_or_ambigious_system_prompt, category_classification_system_prompt,multiquery_splitter_system_prompt
from Agents.Query_Agent.utils.rag_state import INDEX_DIR,BASE_DIR,EMBEDDINGS,CHUNK_SIZE,CHUNK_OVERLAP,llm,mqr
from Agents.Query_Agent.utils.rag_state import collection_classification, MultiQueryOutput, multi_or_ambigious_classification


def discover_collections(base_dir: str) -> List[str]:
    """Return sorted list of subfolder names under base_dir (each becomes a collection)."""
    os.makedirs(base_dir, exist_ok=True)
    names = [
        name for name in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, name)) and not name.startswith(".")
    ]
    return sorted(names)


def get_index_path(collection_name: str) -> str:
    return os.path.join(INDEX_DIR, f"{collection_name}_index")


def get_metadata_path(collection_name: str) -> str:
    return os.path.join(INDEX_DIR, f"{collection_name}_processed.pkl")


def load_processed_files(collection_name: str) -> Set[str]:
    path = get_metadata_path(collection_name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return set()


def save_processed_files(collection_name: str, processed_files: Set[str]):
    path = get_metadata_path(collection_name)
    with open(path, "wb") as f:
        pickle.dump(processed_files, f)


def split_docs(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return splitter.split_documents(docs)


def load_documents_from_folder(folder_path, file_names):
    """Load documents from the list of file names (supports .txt, .pdf, .docx)."""
    docs = []
    for file in file_names:
        file_path = os.path.join(folder_path, file)
        ext = file.lower().split(".")[-1]

        try:
            if ext == "txt":
                loader = TextLoader(file_path, encoding="utf-8")
            elif ext == "pdf":
                loader = PyPDFLoader(file_path)
            elif ext in ["docx", "doc"]:
                loader = Docx2txtLoader(file_path)
            else:
                print(f"⚠️ Skipping unsupported file type: {file}")
                continue

            docs.extend(loader.load())
        except Exception as e:
            print(f"❌ Failed to load {file}: {e}")
    return docs


def build_or_update_collection(collection_name: str):
    """Create or update FAISS index for a collection folder."""
    folder_path = os.path.join(BASE_DIR, collection_name)
    index_path = get_index_path(collection_name)

    os.makedirs(INDEX_DIR, exist_ok=True)
    os.makedirs(folder_path, exist_ok=True)

    processed_files = load_processed_files(collection_name)

    # detect new files (supported extensions)
    all_files = {
        f for f in os.listdir(folder_path)
        if f.lower().endswith((".txt", ".pdf", ".docx"))
    }
    new_files = all_files - processed_files

    vectordb = None
    if os.path.exists(index_path):
        # load existing FAISS index
        try:
            print(f"Loading existing FAISS index for collection: {collection_name}")
            vectordb = FAISS.load_local(index_path, EMBEDDINGS, allow_dangerous_deserialization=True)
        except Exception as e:
            print(f"⚠️ Failed to load existing index for {collection_name}: {e}. Will try to recreate if there are docs.")

    if new_files:
        print(f"📂 Found new files in {collection_name}: {new_files}")
        new_docs = load_documents_from_folder(folder_path, new_files)
        chunks = split_docs(new_docs)

        if chunks:
            if vectordb:
                vectordb.add_documents(chunks)
            else:
                vectordb = FAISS.from_documents(chunks, EMBEDDINGS)

            try:
                vectordb.save_local(index_path)
            except Exception as e:
                print(f"❌ Error saving index for {collection_name}: {e}")

            processed_files.update(new_files)
            save_processed_files(collection_name, processed_files)
        else:
            print(f"⚠️ No valid text chunks found in new files for {collection_name}")

    if vectordb is None:
        # No index and no new docs -> return None (safe handling by caller)
        print(f"⚠️ No documents for {collection_name}. Skipping index creation.")
        return None

    return vectordb


def query_collection(dbs, collection_name: str, query: str, k=3):
    """Safely query a collection. Returns list of Documents or empty list."""
    db = dbs.get(collection_name)
    if db is None:
        print(f"⚠️ No index found for '{collection_name}'. Add documents to '{os.path.join(BASE_DIR, collection_name)}' and re-run.")
        return []
    return db.similarity_search(query, k=k)


def main(query : str , sample_collection : str):

    # discover collection folders dynamically
    collections = discover_collections(BASE_DIR)

    if not collections:

        return f"ℹ️ No collections found in '{BASE_DIR}'. Create subfolders there (one per collection), then run again."
    else:
        
        print(f"Discovered collections: {collections}")

    dbs: Dict[str, FAISS] = {}

    print("\n🔍 Building/Updating FAISS Indexes...\n")

    for col in collections:

        dbs[col] = build_or_update_collection(col)

    print("\n✅ Summary of collections:")

    for col in collections:

        db = dbs.get(col)

        if db is None:

            print(f" - {col}: 0 documents indexed")

        else:

            try:

                count = db.index.ntotal

            except Exception:

                count = "unknown"

            print(f" - {col}: {count} documents indexed")

    if sample_collection:

        results = query_collection(dbs, sample_collection, query, k=3)

        print(f"......{len(results)} OF CHUNKS RETRIEVED FOR {query}")

        if results:

            for r in results:

                return  f"{r.page_content[:300].replace('\n', ' ')}"
            
        else:

            return f"\n⚠️ No results found for {sample_collection}."


#identifying collection to search relevant vector store


def retrival(query : str) :
    print(f"\n\nRETRIEVAL FUNCTION CALLED....\n\n")
    res= discover_collections(BASE_DIR)
    print(res)

    classification = llm.with_structured_output(collection_classification).invoke([HumanMessage(content = category_classification_system_prompt.format(res = res, query = query))])

    print(F'\nCLASSIFIED CATEGORY : {classification.collection_name}\n')

    result = main(query,classification.collection_name)

    print(f"\n🔎 Query Results ({result}):")

    return result



# Function to split queries using LLM
def split_multiquery_llm_and_return_output(query: str) -> List[str]:

    print(f"\n\MULTI QUERY SPLITTER FUNCTION CALLED....\n\n")

    structured_llm = llm.with_structured_output(MultiQueryOutput)

    multiple_query_list = structured_llm.invoke(
        [HumanMessage(content=multiquery_splitter_system_prompt.format(query=query))]
    )
    print(f"\n\nMULTI QUERY SPLITTED INTO -({multiple_query_list})\n\n")

    list_output = []
    for q in multiple_query_list.multiple_queries:
        print(f"\n\nsearching for query......'{q}'")
        output = retrival(q)
        list_output.append(output)
                
    print(f"\n\nMULTI QUERY OUTPUT -({list_output})\n\n")

    return list_output

#classifying into MULTIQUERY, AMBIGUOUS, NORMAL


def retrieval_for_multiquery_ambigious_or_normal(query : str) -> List:

    print(f"\n\retrieval_for_multiquery_ambigious_or_normal FUNCTION CALLED....\n\n")

    multiquery_ambigious_classification = llm.with_structured_output(multi_or_ambigious_classification).invoke([HumanMessage(content = multiquery_or_ambigious_system_prompt.format(query = query))])

    if multiquery_ambigious_classification.query_identification == 'MULTIQUERY':
        print('MULTIQUERY')

        multi_query_result = split_multiquery_llm_and_return_output(query)

        return multi_query_result

    elif multiquery_ambigious_classification.query_identification == 'AMBIGIOUS':

        print('AMBIGIOUS')

        rewritten_queries = mqr.llm_chain.invoke({"question": query})

        print(f"QUERIES GEERATED FOR AMBIGIOUS QUERY : {rewritten_queries}")

        ambiguous_retrieval_list =[]

        for query in rewritten_queries:
            
            ambiguous_retrieval_list.append(retrival(query))

        return ambiguous_retrieval_list

    elif multiquery_ambigious_classification.query_identification == 'NORMAL':

        result = retrival(query)

        return result

    else :
        return ['no data available']