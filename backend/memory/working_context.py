"""

"""

from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, FOAF
from pydantic import BaseModel
from instructor import patch
from anthropic import Anthropic
from openai import OpenAI
import os

# CLIENT = patch(Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")))
CLIENT = patch(OpenAI())


class UserProfile(BaseModel):
    def __init__(self, name):
        """
        Initialize a UserProfile.

        Args:
            name (str): The name of the user.
        """
        self.name = name
        self.graph = Graph()
        self.graph.add()

    def update_relation(self, entity1, relation, entity2):
        """
        Update a relation in the user profile.

        Args:
            entity1 (str): The name of the first entity in the relation.
            relation (str): The relation between the entities.
            entity2 (str): The name of the second entity in the relation.
        """
        self.graph.add((entity1, relation, entity2))

    def get_relations(self, entity):
        """
        Get all relations for a given entity from the user profile.

        Args:
            entity (str): The name of the entity to retrieve relations for.

        Returns:
            list: A list of tuples representing the relations for the entity.
        """
        return [(e1, r, e2) for e1, r, e2 in self.graph if e1 == entity or e2 == entity]

    def __str__(self):
        return f"UserProfile(name={self.name}, attributes={self.attributes})"


class WorkingContext:
    def __init__(self, filename=None):
        """
        Initialize a WorkingContext.

        Args:
            filename (str, optional): The filename to load the graph from. If not provided, an empty graph is created.
        """
        self.graph = Graph() if not filename else self.load_graph(filename)
        self.ns = Namespace("http://pearllabs.ai/")

        if filename:
            self.load_graph(filename)

    def add_user_profile(self, user_profile):
        """
        Add a user profile to the graph.

        Args:
            user_profile (UserProfile): The user profile to add.
        """
        subject = URIRef(self.ns[user_profile.name])
        self.graph.add((subject, RDF.type, FOAF.Person))
        self.graph.add((subject, FOAF.name, Literal(user_profile.name)))

        for attribute, value in user_profile.attributes.items():
            self.graph.add((subject, self.ns[attribute], Literal(value)))

    def get_user_profile(self, name):
        """
        Get the user profile for a specific person.

        Args:
            name (str): The name of the person.

        Returns:
            UserProfile: The user profile for the specified person, or None if not found.
        """
        subject = URIRef(self.ns[name])
        if (subject, RDF.type, FOAF.Person) not in self.graph:
            return None

        user_profile = UserProfile(name)

        for s, p, o in self.graph.triples((subject, None, None)):
            if p == FOAF.name:
                continue
            elif p == RDF.type:
                continue
            else:
                attribute = str(p).replace(str(self.ns), "")
                user_profile.update_attribute(attribute, str(o))

        return user_profile

    def save_graph(self, filename):
        """
        Save the graph to a file.

        Args:
            filename (str): The filename to save the graph to.
        """
        self.graph.serialize(destination=filename, format="turtle")
        print(f"Graph saved to {filename}")

    def load_graph(self, filename):
        """
        Load the graph from a file.

        Args:
            filename (str): The filename to load the graph from.
        """
        self.graph.parse(filename, format="turtle")
        print(f"Graph loaded from {filename}")


if __name__ == "__main__":
    # Code to test the WorkingContext class
    user_profile = UserProfile("Alice")
    user_profile.update_attribute("age", 30)
    user_profile.update_attribute("city", "New York")
    user_profile.update_attribute("occupation", "Software Engineer")

    context = WorkingContext()
    context.add_user_profile(user_profile)
    context.save_graph("user_profiles.ttl")

    context2 = WorkingContext("user_profiles.ttl")
    retrieved_profile = context2.get_user_profile("Alice")
    print(retrieved_profile.attributes)
    # Output: {'age': '30', 'city': 'New York', 'occupation': 'Software Engineer'}
