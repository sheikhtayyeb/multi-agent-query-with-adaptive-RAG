from src.llms.llm import LLM
from src.states.state import GraphState
from src.db.doc_vectordb import SaveDocDB
from src.states.state import RouteQuery,GradeDocuments,GradeHallucinations,GradeAnswer

from langchain_classic import hub
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class AgentNode:
    def __init__(self,model_openai = "gpt-4o-mini",model_groq = "qwen/qwen3-32b"):
        model = LLM(model_openai,model_groq)
        self.llm_openai = model.llm_openai
        self.llm_groq = model.llm_groq
        print(self.llm_groq)

    def route_question(self,state:GraphState):
        """
        Route question to web search or RAG.

        Args:
            state (dict): The current graph state

        Returns:
            str: Next node to call
        """

        print("---ROUTE QUESTION---")
        structured_llm_router = self.llm_groq.with_structured_output(RouteQuery)

        # Prompt
        system = """You are an expert at routing a user question to a vectorstore or web search.
        The vectorstore contains documents related to langgraph.
        Use the vectorstore for questions on these topics. Otherwise, use web-search."""
        route_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "{question}"),
            ]
        )
        question_router = route_prompt | structured_llm_router

        question = state["question"]
        source = question_router.invoke({"question": question})

        if source.datasource == "web_search":
            print("---ROUTE QUESTION TO WEB SEARCH---")
            return "web_search"
        elif source.datasource == "vectorstore":
            print("---ROUTE QUESTION TO RAG---")
            return "vectorstore"

    def retriever(self,state:GraphState):
        """This vectordb retriever contains information related to langgraph"""
        vectordb_obj = SaveDocDB(embd_model="text-embedding-3-large",vector_dimensions=1024)
        vector_db = vectordb_obj.load_vectordb("./src/db/fiass_index")
        retriever = vector_db.as_retriever()

        # Retrieval
        question = state['question']
        documents = retriever.invoke(question)
        return {"documents": documents, "question": question}

    
    def generate(self,state:GraphState):
        """
        Generate answer

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation, that contains LLM generation
        """
        print("---GENERATE---")
        question = state["question"]
        documents = state["documents"]
        prompt = hub.pull("rlm/rag-prompt")

        # RAG generation
        rag_chain = prompt | self.llm_groq | StrOutputParser()
        generation = rag_chain.invoke({"context": documents, "question": question})
        return {"documents": documents, "question": question, "generation": generation}
    

    def grade_documents(self,state:GraphState):
        """
        Determines whether the retrieved documents are relevant to the question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates documents key with only filtered relevant documents
        """

        print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
        structured_llm_grader = self.llm_groq.with_structured_output(GradeDocuments)
        
        # Prompt
        system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
            If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
            It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
            Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
        grade_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
            ]
        )
        retrieval_grader = grade_prompt | structured_llm_grader
        question = state["question"]
        documents = state["documents"]

        # Score each doc
        filtered_docs = []
        for d in documents:
            score = retrieval_grader.invoke(
                {"question": question, "document": d.page_content}
            )
            grade = score.binary_score
            if grade == "yes":
                print("---GRADE: DOCUMENT RELEVANT---")
                filtered_docs.append(d)
            else:
                print("---GRADE: DOCUMENT NOT RELEVANT---")
                continue
        return {"documents": filtered_docs, "question": question}
    
    def decide_to_generate(self,state:GraphState):
        """
        Determines whether to generate an answer, or re-generate a question.

        Args:
            state (dict): The current graph state

        Returns:
            str: Binary decision for next node to call
        """

        print("---ASSESS GRADED DOCUMENTS---")
        state["question"]
        filtered_documents = state["documents"]

        if not filtered_documents:
            # All documents have been filtered check_relevance
            # We will re-generate a new query
            print(
                "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
            )
            return "transform_query"
        else:
            # We have relevant documents, so generate answer
            print("---DECISION: GENERATE---")
            return "generate"

    def transform_query(self,state:GraphState):
        """
        Transform the query to produce a better question.

        Args:
            state (dict): The current graph state
            
        Returns:
            state (dict): Updates question key with a re-phrased question
        """

        print("---TRANSFORM QUERY---")
        question = state["question"]
        documents = state["documents"]

        # Prompt
        system = """You a question re-writer that converts an input question to a better version that is optimized \n 
            for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning."""
        re_write_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                (
                    "human",
                    "Here is the initial question: \n\n {question} \n Formulate an improved question.",
                ),
            ]
        )

        # Re-write question
        question_rewriter = re_write_prompt | self.llm_groq | StrOutputParser()
        better_question = question_rewriter.invoke({"question": question})
        return {"documents": documents, "question": better_question}
    
    
    def grade_generation_v_documents_and_question(self,state:GraphState):
        """
        Determines whether the generation is grounded in the document and answers question.

        Args:
            state (dict): The current graph state

        Returns:
            str: Decision for next node to call
        """

        print("---CHECK HALLUCINATIONS---")
        question = state["question"]
        documents = state["documents"]
        generation = state["generation"]
        llm_grader_ques = self.llm_groq.with_structured_output(GradeHallucinations)
        llm_grader_ans = self.llm_groq.with_structured_output(GradeAnswer)

        # Question Prompt
        system = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n 
            Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts."""
        hallucination_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
            ]
        )

        # Answer Prompt
        system = """You are a grader assessing whether an answer addresses / resolves a question \n 
            Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question."""
        answer_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
            ]
        )

        hallucination_grader = hallucination_prompt | llm_grader_ques
        answer_grader = answer_prompt | llm_grader_ans

        score = hallucination_grader.invoke(
                  {"documents": documents, "generation": generation}
                                          )
        grade = score.binary_score

        # Check hallucination
        if grade == "yes":
            print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
            # Check question-answering
            print("---GRADE GENERATION vs QUESTION---")
            score = answer_grader.invoke({"question": question, "generation": generation})
            grade = score.binary_score
            if grade == "yes":
                print("---DECISION: GENERATION ADDRESSES QUESTION---")
                return "useful"
            else:
                print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
                return "not useful"
        else:
            print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
            return "not supported"
    
