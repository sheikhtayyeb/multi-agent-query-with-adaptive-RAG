from langgraph.graph import END, StateGraph, START
from src.states.state import GraphState
from src.nodes.node import AgentNode
from src.tools.tool import Tools

class GraphBuilder:

    def __init__(self):
        self.graph = StateGraph(GraphState)
        self.agent_node = AgentNode()
        self.tool = Tools()
        
    def build_graph(self):

        # Define the nodes
        self.graph.add_node("web_search", self.tool.web_search)  # web search
        self.graph.add_node("retrieve", self.agent_node.retriever)  # retrieve
        self.graph.add_node("grade_documents", self.agent_node.grade_documents)  # grade documents
        self.graph.add_node("generate", self.agent_node.generate)  # generate
        self.graph.add_node("transform_query", self.agent_node.transform_query)  # transform_query

        # Build graph
        self.graph.add_conditional_edges(
            START,
            self.agent_node.route_question,
            {
                "web_search": "web_search",
                "vectorstore": "retrieve",
            },
                                    )
        self.graph.add_edge("web_search", "generate")
        self.graph.add_edge("retrieve", "grade_documents")
        self.graph.add_conditional_edges(
                    "grade_documents",
                    self.agent_node.decide_to_generate,
                    {
                        "transform_query": "transform_query",
                        "generate": "generate",
                    },
                                    )
        self.graph.add_edge("transform_query", "retrieve")
        self.graph.add_conditional_edges(
                        "generate",
                        self.agent_node.grade_generation_v_documents_and_question,
                        {
                            "not supported": "generate",
                            "useful": END,
                            "not useful": "transform_query",
                        },
                    )
        return self.graph.compile()