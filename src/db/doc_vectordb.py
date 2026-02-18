from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools.retriever import create_retriever_tool

class SaveDocDB:
    def __init__(self,embd_model="text-embedding-3-large",vector_dimensions=1024):
        self.embd_model = OpenAIEmbeddings(model = embd_model,dimensions=vector_dimensions)

    def doc_list(self,urls):
        docs = [WebBaseLoader(url).load() for url in urls]
        doc_list= [item for sublist in docs for item in sublist ]
        return  doc_list
        
    
    def doc_splits(self,chunk_size,chunk_overlap,doc_list):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        doc_splits = text_splitter.split_documents(doc_list)
        return doc_splits

    def save_vectordb(self,doc_splits,path):
        vectordb = FAISS.from_documents(
                        documents = doc_splits,
                        embedding = self.embd_model
                    )
        vectordb.save_local(path)

    
    def retiever_vectordb(self,vectordb,name,description):
        retriever = vectordb.as_retriever()
        retriever_tool = create_retriever_tool(
                                        retriever,
                                        name,
                                        description
                                      )
        return retriever_tool

    
    def load_vectordb(self,path):
        return FAISS.load_local(path,
                          embeddings=self.embd_model,
                          allow_dangerous_deserialization=True)





