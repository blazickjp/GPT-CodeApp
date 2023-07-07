import openai
import enum
import asyncio

from pydantic import Field
from typing import List

from openai_function_call import OpenAISchema
from pprint import pprint


class QueryType(str, enum.Enum):
    """
    Enumeration representing the types of queries that can be asked to a question answer system.
    """

    # When i call it anything beyond 'merge multiple responses' the accuracy drops significantly.
    SINGLE_QUESTION = "SINGLE"
    MERGE_MULTIPLE_RESPONSES = "MERGE_MULTIPLE_RESPONSES"


class Model(enum.Enum):
    """
    Enumeration representing the models that can be used to answer questions.
    """

    GPT4 = "gpt-4-0613"
    GPT3_5: str = "gpt-3.5-turbo-0613"


class ComputeQuery(OpenAISchema):
    """
    Models a computation of a query, assume this can be some RAG system like llamaindex
    """

    query: str
    response: str = "..."

    @classmethod
    def from_query(cls, query: str) -> "ComputeQuery":
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant answering my questions.",
            }
        ]
        messages.append({"role": "user", "content": query})
        completion = openai.ChatCompletion.create(
            model=Model.GPT3_5.value,
            temperature=0,
            messages=messages,
            max_tokens=1000,
        )
        return cls(query=query, response=completion.choices[0].message["content"])


class MergedResponses(OpenAISchema):
    """
    Models a merged response of multiple queries.
    Currently we just concatinate them but we can do much more complex things.
    """

    responses: List[ComputeQuery]


class Query(OpenAISchema):
    """
    Class representing a single question in a question answer subquery.
    Can be either a single question or a multi question merge.
    """

    id: int = Field(..., description="Unique id of the query")
    question: str = Field(
        ...,
        description="The question we are asking from our question answer system. If we are asking multiple questions"
        ", this question is asked by also providing the answers to the sub questions",
    )
    dependencies: List[int] = Field(
        default_factory=list,
        description="List of children questions which need to be answered before we can ask the main question."
        " Use a subquery to answer known unknowns to increase confidence in the final answer, when we"
        " need to ask multiple questions to get the answer. Dependencies may only be other queries.",
    )
    node_type: QueryType = Field(
        default=QueryType.SINGLE_QUESTION,
        description="Type of question we are asking, either a single question or a multi question merge"
        " when there are multiple questions",
    )

    async def execute(self, dependency_func):
        print("Executing", f"{self.question}")
        print("Executing with", len(self.dependencies), "dependancies")

        if self.node_type == QueryType.SINGLE_QUESTION:
            resp = ComputeQuery.from_query(
                query=self.question,
            )
            pprint(resp.dict())
            return resp

        sub_queries = dependency_func(self.dependencies)
        computed_queries = await asyncio.gather(
            *[q.execute(dependency_func=dependency_func) for q in sub_queries]
        )
        sub_answers = MergedResponses(responses=computed_queries)
        merged_query = f"{self.question}\nContext: {sub_answers.json()}"
        resp = ComputeQuery(
            query=merged_query,
        )
        pprint(resp.dict())
        return resp


class QueryPlan(OpenAISchema):
    """
    Container class representing a tree of questions to ask a question answer system.
    Make sure every question is included in the tree and every question is only asked a single time.
    """

    query_graph: List[Query] = Field(
        ..., description="The original question we are asking"
    )

    async def execute(self):
        # this should be done with a topological sort, but this is easier to understand
        original_question = self.query_graph[-1]
        print(f"Executing query plan from `{original_question.question}`")
        return await original_question.execute(dependency_func=self.dependencies)

    def dependencies(self, idz: List[int]) -> List[Query]:
        """
        Returns the dependencies of the query with the given id.
        """
        return [q for q in self.query_graph if q.id in idz]


Query.update_forward_refs()
QueryPlan.update_forward_refs()


def query_planner(question: str) -> QueryPlan:
    """
    Function that takes a question and returns a query plan.

    Args:
        question (str): The question we are asking

    Returns:
        QueryPlan: The query plan to answer the question
    """
    messages = [
        {
            "role": "system",
            "content": "You are a world class query planning algorithm capable of breaking questions up in to its"
            " dependent sub-queries such that the answers can be used to inform the parent question. Do"
            " not answer the questions, simply provide correct compute graph with good specific"
            " questions to ask and relevant dependencies. Before you call the function, think step by"
            " step to get a better understanding the problem.",
        },
        {
            "role": "user",
            "content": f"Consider: {question}\nGenerate the correct query plan.",
        },
    ]

    completion = openai.ChatCompletion.create(
        model=Model.GPT4.value,
        temperature=0,
        functions=[QueryPlan.openai_schema],
        function_call={"name": QueryPlan.openai_schema["name"]},
        messages=messages,
        max_tokens=1000,
    )
    root = QueryPlan.from_response(completion)
    return root


if __name__ == "__main__":
    plan = query_planner(
        "What is the difference in populations of Canada and Sydney Crosby's home country?",
    )
    pprint(plan.dict())
    asyncio.run(plan.execute())
