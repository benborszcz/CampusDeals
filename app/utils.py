from elasticsearch import Elasticsearch
from .agent import Agent
import datetime
import json
import uuid
import config

def get_prompt_from_file(name):
    try:
        with open(f'app/prompts/{name}.txt', 'r') as file:
            contents = file.read()
            return contents
    except FileNotFoundError:
        return f'The file {name} does not exist.'


def transform_deal_structure(deal_structure_LLM):
    # Generate a unique deal_id
    deal_id = str(uuid.uuid4())

    # Get the current timestamp
    created_at = datetime.datetime.now().isoformat()

    # Create a copy of the deal_structure_LLM
    full_deal_structure = deal_structure_LLM.copy()

    # Add the deal_id and created_at to the full_deal_structure
    full_deal_structure["deal_id"] = deal_id
    full_deal_structure["created_at"] = created_at

    return full_deal_structure


# Set the username and password for your Elasticsearch instance
username = 'elastic'
password = config.ELASTICSEARCH_PASSWORD

# Connect to the local Elasticsearch instance using HTTPS and authentication
es = Elasticsearch(
    ["https://localhost:9200"],
    basic_auth=(username, password),
    verify_certs=False  # Bypass certificate verification (not recommended for production)
)

def index_deal(deal):
    """
    Index a new deal into Elasticsearch.
    """
    # Assuming deal is a dictionary that matches the Elasticsearch data structure
    response = es.index(index="deals", id=deal['deal_id'], body=deal)
    return response

def reset_elasticsearch():
    """
    Reset Elasticsearch.
    """
    # Delete the deals index
    es.indices.delete(index='deals', ignore=[400, 404])

    # Create the deals index
    es.indices.create(index='deals', ignore=400)

def remove_deal(deal_id):
    """
    Remove a deal from Elasticsearch.
    """
    # Assuming deal is a dictionary that matches the Elasticsearch data structure
    response = es.delete(index="deals", id=deal_id)
    return response

def search_deals(query):
    """
    Search for deals using Elasticsearch across all fields.
    """
    # Define a query_string query to search across all fields
    search_query = {
        "query": {
            "query_string": {
                "query": query,
                "fuzziness": "AUTO"
            }
        }
    }

    # Perform the search on the 'deals' index
    response = es.search(index="deals", body=search_query, min_score=0, from_=0, size=10)

    return response['hits']['hits']

def parse_deal_submission(text):
    """
    Use OpenAI's LLM to parse a deal submission text.
    """
    # Call OpenAI's API to parse the text and extract structured data
    agent = Agent("Deal Parser", "Parse a deal submission into structured data", get_prompt_from_file("deal_parser"))
    response = agent.complete_task(text)
    response = json.loads(response)
    return response