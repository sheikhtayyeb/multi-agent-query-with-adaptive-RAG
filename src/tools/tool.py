from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_classic.schema import Document
from src.states.state import GraphState
from langchain_tavily import TavilySearch

class Tools:
    def __init__(self):
        pass

    def web_search(self,state:GraphState):
        """
        Web search based on the re-phrased question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates documents key with appended web results
        """

        print("---WEB SEARCH---")
        # web_search_tool = TavilySearchResults(k=3)
        web_search_tool = TavilySearch(max_results =5)
        question = state["question"]

        # Web search
        docs = web_search_tool.invoke({"query": question})
        web_results = "\n".join([d["content"] for d in docs["results"]])
        web_results = Document(page_content=web_results)

        return {"documents": web_results, "question": question}
    
    