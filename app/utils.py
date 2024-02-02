from elasticsearch import Elasticsearch
from .agent import Agent
import datetime
import json
import uuid
import config
import re

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

    # Add the upvotes and downvotes to the full_deal_structure
    full_deal_structure["upvotes"] = 0
    full_deal_structure["downvotes"] = 0

    return full_deal_structure


# Determine which Elasticsearch service to use
elasticsearch_service = config.ELASTICSEARCH_SERVICE

if elasticsearch_service == 'bonsai':
    # Retrieve the Bonsai URL from the config
    bonsai = config.ELASTICSEARCH_BONSAI_URL
    # Use regular expressions to extract the authentication credentials (username and password)
    auth = re.search('https://(.*)@', bonsai).group(1).split(':')
    # Extract the host by removing the authentication part from the Bonsai URL
    host = bonsai.replace('https://%s:%s@' % (auth[0], auth[1]), '')
    # Optionally extract the port if it's included in the BONSAI_URL
    match = re.search('(:\d+)', host)
    if match:
        port = int(match.group(0).split(':')[1])
        host = host.replace(match.group(0), '')
    else:
        port = 443  # Default to port 443 for HTTPS if no port is specified
    # Set up the Elasticsearch connection configuration for Bonsai
    es_header = [{
        'host': host,
        'port': port,
        'use_ssl': True,
        'http_auth': (auth[0], auth[1])
    }]
else:
    # Configuration for local Elasticsearch instance
    local_url = config.ELASTICSEARCH_LOCAL_URL
    parsed_url = re.search('http://(.+?):(\d+)', local_url)
    host = parsed_url.group(1)
    port = int(parsed_url.group(2))
    # Set up the Elasticsearch connection configuration for local
    es_header = [{
        'host': host,
        'port': port,
        'use_ssl': False,  # Assuming local is not using SSL
        'http_auth': (config.ELASTICSEARCH_LOCAL_USERNAME, config.ELASTICSEARCH_LOCAL_PASSWORD) if config.ELASTICSEARCH_LOCAL_PASSWORD else None
    }]

# Instantiate the new Elasticsearch connection
es = Elasticsearch(es_header)

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

def is_elasticsearch_empty():
    """
    Check if Elasticsearch is empty.
    """
    # Get the count of documents in the 'deals' index
    response = es.count(index='deals')
    count = response['count']

    # Return True if the count is 0, indicating that Elasticsearch is empty
    return count == 0

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
    response = es.search(index="deals", body=search_query, from_=0, size=10)

    return response['hits']['hits']

def search_deals_day(days):
    """
    Search for deals using Elasticsearch by day.
    """
    # Set up elements for search_query
    elements = "";
    for day in days:
        if day != days[len(days)-1]:
            elements += day + ", ";
        else:
            elements += day;

    # Define a query_string to filter deals based on day
    search_query = {
        "query" : {
            "bool" : {
                "must" : [
                {
                    "match" : {
                        "deal_details.days_active": elements
                    }
                }
                ]
            }
        }
    }

    # Perform the search on the 'deals' index
    response = es.search(index="deals", body=search_query, from_=0, size=10)

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
