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

"""
Deal Structure
{
  "deal_id": "Unique Deal ID",
  "title": "Quick Deal Title",
  "description": "Description of the deal that people can tell everything from",
  "establishment": {
    "name": "Name",
    "type": "Type",
  },
  "deal_details": {
    "deal_type": "Type",
    "deal_items": [
        {
            "item": "Item Name",
            "item_type": "Type of Item",
            "pricing": {"price": "# if price deal like $1 wells else N/A", "discout": "# if deal like 50% off or $2 off else N/A"}
        },
    ],
    "start_time": "HH:MM:SS" or "Open",
    "end_time": "HH:MM:SS" or "Close",
    "days_active": ["Weekday 1", "Weekday 2", "etc"],
    "exclusions": "any exclusions, if none put N/A",
  },
  "tags": ["tag1", "tag2", "etc"],
  "created_at": "2022-01-01T00:00:00.000Z",
  "upvotes": 0,
  "downvotes": 0,
}
"""

def transform_deal_structure(deal_structure_LLM, establishments_list):
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

    full_deal_establishment = next((establishment for establishment in establishments_list if establishment["name"] == full_deal_structure["establishment"]["name"]), None)
    establishment_hours = full_deal_establishment['hours'][full_deal_structure["deal_details"]["days_active"][0][:3]]
    print(establishment_hours)
    if full_deal_structure["deal_details"]["start_time"] == "Open":
        full_deal_structure["deal_details"]["start_time"] = establishment_hours.split("-")[0]
    
    print(full_deal_structure["deal_details"]["days_active"][0])
    if full_deal_structure["deal_details"]["end_time"] == "Close":
        full_deal_structure["deal_details"]["end_time"] = establishment_hours.split("-")[1]

    # If time is in format HH:MM, add seconds
    if len(full_deal_structure["deal_details"]["start_time"]) == 5:
        full_deal_structure["deal_details"]["start_time"] += ":00"
    if len(full_deal_structure["deal_details"]["end_time"]) == 5:
        full_deal_structure["deal_details"]["end_time"] += ":00"

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

def search_deals(query, days, distance, user_lat, user_lng):
    """
    Search for deals using Elasticsearch across all fields.
    """
    # Sets up day elements for filter by day
    dayElements = ""
    if days:
        for day in days:
            if day != days[len(days)-1]:
                dayElements += day + ", "
            else:
                dayElements += day
    # If day filter is not specified, search across all days
    else:
        dayElements = "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday"

    # base query structure using dayElements
    search_query = {
        "query": {
            "bool": {
                "must": [],
                "filter": [
                    {
                        "match": {
                            "deal_details.days_active": dayElements
                        }
                    }
                ]
            }
        }
    }

    # Retrieve nearby establishments if distance filtering is applied
    if distance and user_lat and user_lng:
        nearby_establishments = get_nearby_establishments(user_lat, user_lng, distance)
        if not nearby_establishments: 
            return []

        # Add filter for establishment names if there are any nearby
        search_query["query"]["bool"]["filter"].append({
            "terms": {
                "establishment_name.keyword": nearby_establishments
            }
        })

    # Add string query if present
    if query:
        search_query["query"]["bool"]["must"].append({
            "query_string": {
                "query": query,
                "fuzziness": "AUTO"
            }
        })

    # Perform the search on the 'deals' index
    response = es.search(index="deals", body=search_query, from_=0, size=10)

    return response['hits']['hits']

def parse_deal_submission(text, establishments_list):
    """
    Use OpenAI's LLM to parse a deal submission text.
    """
    # Call OpenAI's API to parse the text and extract structured data
    agent = Agent("Deal Parser", "Parse a deal submission into structured data", get_prompt_from_file("deal_parser").replace("{{establishments_list}}", str(establishments_list)))
    response = agent.complete_task(text)
    response = json.loads(response)
    return response

from . import db
from math import radians, cos, sin, asin, sqrt

def get_nearby_establishments(user_lat, user_lng, distance):
    # load all establishments from firestore
    establishments = db.collection('establishments').stream()
    establishments_list = [establishment.to_dict() for establishment in establishments]
    nearby_establishments = []

    for est in establishments_list:
        est_lat = est['latitude']
        est_lng = est['longitude']
        
        # only return establishments within distance of user's coordinates
        if haversine(user_lat, user_lng, est_lat, est_lng) <= distance:
            nearby_establishments.append(est['name'])

    return nearby_establishments

def haversine(lat1, lng1, lat2, lng2):
    """
    Calculate the distance in miles between two sets of coordinates on Earth
    """
    # Convert decimal degrees to radians 
    lat1, lng1, lat2, lng2 = map(float, [lat1, lng1, lat2, lng2])
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])

    # Haversine formula 
    dlon = lng2 - lng1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 3956 # Radius of earth in miles
    return c * r