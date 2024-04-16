# elastic_utils.py
import json
import time
from elasticsearch import Elasticsearch
import config
import re
import firebase_admin
from firebase_admin import firestore, credentials


db = firestore.client()

"""
Private Functions
"""

"""
{
  "created_at": "2024-04-09T13:23:24.632520",
  "description": "Happy Hour at BrewDog Short North, 50% off draft beer and cocktails",
  "tags": [
    "Happy Hour",
    "Draft Beer",
    "Cocktails",
    "Bar",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday"
  ],
  "upvotes": 73,
  "deal_id": "e86c671a-d03a-406a-800c-c268c22d7cdb",
  "downvotes": 2,
  "title": "BrewDog Short North Bar, Happy Hour",
  "establishment": {
    "address": "1175 N High St., Columbus, OH",
    "latitude": 39.98633,
    "shortname": "BrewDog",
    "hours": {
      "Sun": "12:00-21:00",
      "Fri": "16:00-23:00",
      "Mon": "Closed",
      "Sat": "12:00-23:00",
      "Tue": "16:00-22:00",
      "Wed": "16:00-22:00",
      "Thu": "16:00-22:00"
    },
    "longitude": -83.0056,
    "name": "BrewDog Short North"
  },
  "deal_details": {
    "deal_type": "Percentage Off",
    "start_time": "15:00:00",
    "days_active": [
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday"
    ],
    "deal_name": "Happy Hour",
    "deal_description": "50% Off Draft Beer and Cocktails",
    "end_time": "18:00:00",
    "exclusions": "N/A",
    "deal_items": [
      {
        "pricing": {
          "discount": "50%",
          "price": "N/A"
        },
        "item_type": "Alcohol",
        "item": "Draft Beer"
      },
    ]
  }
}
"""

def _reset_index(es: Elasticsearch):
    # Delete the index if it exists
    index_name = 'deals'
    es.indices.delete(index=index_name, ignore=[400, 404])

    index_body = {
        "settings": {
            "analysis": {
                "filter": {
                    "english_stemmer": {
                        "type": "stemmer",
                        "language": "english"
                    }
                },
                "analyzer": {
                    "english_analyzer": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "english_stemmer"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "deal_id": {
                    "type": "keyword"
                },
                "title": {
                    "type": "text",
                    "analyzer": "english_analyzer"
                },
                "description": {
                    "type": "text",
                    "analyzer": "english_analyzer"
                },
                "tags": {
                    "type": "keyword"
                },
                "establishment": {
                    "type": "nested",
                    "properties": {
                        "name": {
                            "type": "text",
                            "analyzer": "english_analyzer"
                        },
                        "shortname": {
                            "type": "text",
                            "analyzer": "english_analyzer"
                        },
                    }
                },
                "deal_details": {
                    "type": "nested",
                    "properties": {
                        "deal_name": {
                            "type": "text",
                            "analyzer": "english_analyzer"
                        },
                        "deal_description": {
                            "type": "text",
                            "analyzer": "english_analyzer"
                        },
                        "deal_type": {
                            "type": "text",
                            "analyzer": "english_analyzer"
                        },
                        "start_time": {
                            "type": "text"
                        },
                        "end_time": {
                            "type": "text"
                        },
                        "days_active": {
                            "type": "keyword"
                        },
                        "exclusions": {
                            "type": "text",
                            "analyzer": "english_analyzer"
                        },
                        "deal_items": {
                            "type": "nested",
                            "properties": {
                                "item": {
                                    "type": "text",
                                    "analyzer": "english_analyzer"
                                },
                                "item_type": {
                                    "type": "text",
                                    "analyzer": "english_analyzer"
                                },
                                "pricing": {
                                    "type": "nested",
                                    "properties": {
                                        "price": {
                                            "type": "text"
                                        },
                                        "discount": {
                                            "type": "text"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    # Create the index with the specified settings and mappings
    index_name = 'deals'
    es.indices.create(index=index_name, body=index_body, ignore=400)

# Search using elasticsearch
def _search_es(es: Elasticsearch, query: str):
    # Search for the query
    results = es.search(index='deals', body=query, size=30)

    return results

# Analyze incoming natural language query and create optimal search query format for elasticsearch
def _analyze_query(query: str, days: list = None, distance: str = None, user_lat: str = None, user_lng: str = None):
    # Enhanced search query to better handle natural language queries
    abbreviations = {
        'mon': 'monday',
        'tue': 'tuesday',
        'wed': 'wednesday',
        'thu': 'thursday',
        'fri': 'friday',
        'sat': 'saturday',
        'sun': 'sunday'
    }

    query = query.strip()
    query = query.lower()

    # remove apostrophes
    query = query.replace("'", "")

    if query in ['*', 'all', 'everything', '', None]:
        return {
            "query": {
                "match_all": {}
            }
        }

    day_of_week = abbreviations.get(query, query)
    days_full = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    search_query = {}

    if day_of_week in days_full:
        # Adjust the search query to filter for the specific day within the nested 'deal_details.days_active'
        search_query = {
            "query": {
                "nested": {
                    "path": "deal_details",
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "match": {
                                        "deal_details.days_active": day_of_week
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
    else:
        # Default search query
        search_query = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^3", "description^2", "deal_details.deal_name^3", "deal_details.deal_description^2", "tags^2"],
                                "type": "best_fields",
                                "tie_breaker": 0.3,
                                "fuzziness": "AUTO",
                                "analyzer": "english_analyzer"
                            }
                        },
                        {
                            "nested": {
                                "path": "establishment",
                                "query": {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["establishment.name^2", "establishment.shortname"],
                                        "fuzziness": "AUTO"
                                    }
                                },
                                "score_mode": "avg"
                            }
                        },
                        {
                            "nested": {
                                "path": "deal_details.deal_items",
                                "query": {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["deal_details.deal_items.item"],
                                        "fuzziness": "AUTO"
                                    }
                                },
                                "score_mode": "avg"
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "description": {},
                    "deal_details.deal_name": {},
                    "deal_details.deal_description": {},
                    "comments": {},
                    "establishment.name": {},
                    "establishment.address": {},
                    "deal_details.deal_items.item": {}
                }
            }
        }
            
    print(json.dumps(search_query, indent=2))
    return search_query

def _modify_deal_dict(deal_dict: dict):
    # Modify the deal dictionary recursively
    def lowercase_dict(d):
        if isinstance(d, dict):
            return {lowercase_dict(k): lowercase_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [lowercase_dict(item) for item in d]
        elif isinstance(d, str):
            return d.lower()
        return d
    # Modify the deal dictionary
    deal_dict = lowercase_dict(deal_dict)

    slimmed_dict = {
        'deal_id': deal_dict['deal_id'],
        'title': deal_dict['title'],
        'description': deal_dict['description'],
        'tags': deal_dict['tags'],
        'establishment': {
            'name': deal_dict['establishment']['name'],
            'shortname': deal_dict['establishment']['shortname'],
        },
        'deal_details': {
            'deal_name': deal_dict['deal_details']['deal_name'],
            'deal_description': deal_dict['deal_details']['deal_description'],
            'deal_type': deal_dict['deal_details']['deal_type'],
            'start_time': deal_dict['deal_details']['start_time'],
            'end_time': deal_dict['deal_details']['end_time'],
            'days_active': deal_dict['deal_details']['days_active'],
            'exclusions': deal_dict['deal_details']['exclusions'],
            'deal_items': deal_dict['deal_details']['deal_items']
        }
    }
    return slimmed_dict

def _index_deal(es: Elasticsearch, deal_dict: dict):
    # Modify the deal dictionary
    deal_dict = _modify_deal_dict(deal_dict)
    # Index the deal
    es.index(index='deals', body=deal_dict, id=deal_dict['deal_id'])

def _index_all_deals(es: Elasticsearch, deals: list):
    # Index all deals
    for deal in deals:
        # Convert deal to dictionary
        deal_dict = deal
        # Make deal_dict all lowercase
        deal_dict = {k: v.lower() if isinstance(v, str) else v for k, v in deal_dict.items()}
        # Index the deal
        _index_deal(es, deal_dict)

def _check_if_index_exists(es: Elasticsearch):
    # Check if the index exists
    index_name = 'deals'
    return es.indices.exists(index=index_name)

def _setup_es():
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
    es = None
    try:
        es = Elasticsearch(es_header)
    except Exception as e:
        while True:
            print(f"Error: {e}")
            print("Retrying Elasticsearch connection in 1 second...")
            time.sleep(1)
            try:
                es = Elasticsearch(es_header)
                break
            except Exception as e:
                continue
    return es

def _get_length_of_index(es: Elasticsearch):
    # Get the length of the index
    index_name = 'deals'
    return es.count(index=index_name)['count']

def _sanitize_input(input_string):
    """
    Sanitize input string by removing potentially harmful characters and Elasticsearch query syntax.
    """
    # Check if the query contains the word "kernel" and ban it
    if 'kernel' in input_string.lower():
        # Redirect to the search results page with a message indicating no valid searches
        print("No valid searches found.")
        return ""
    if "/foo" in input_string:
        return ""
    if "ls -al /" in input_string:
        return ""
    if "/" in input_string:
        return ""
    if "&" in input_string:
        return ""
    # Remove characters that could be used in XSS attacks
    sanitized_string = re.sub(r'[<>"\'\\]', '', input_string)
    # Remove characters that could cause parsing errors in Elasticsearch queries
    sanitized_string = re.sub(r'[$\[\]{}()]', '', sanitized_string)
    return sanitized_string

"""
Public Functions
"""

# Search for a query
def search_deals(query: str, days: list = None, distance: str = None, user_lat: str = None, user_lng: str = None):
    if days == None:
        days = []
    if distance == None:
        distance = ""
    if user_lat == None:
        user_lat = ""
    if user_lng == None:
        user_lng = ""
    
    # Sanitize the query
    query = _sanitize_input(query)
    # Set up the Elasticsearch connection
    es = _setup_es()
    # Analyze query
    search_query = _analyze_query(query, [], distance, user_lat, user_lng)
    # Search for query
    results = _search_es(es, search_query)
    # Lowercase days
    days = [day.lower() for day in days]
    # Filter by days
    if days != []:
        results['hits']['hits'] = [result for result in results['hits']['hits'] if any(day in result['_source']['deal_details']['days_active'] for day in days)]
    # Filter by distance
    if distance != "" and user_lat != "" and user_lng != "":
        nearby_establishments = _get_nearby_establishments(float(user_lat), float(user_lng), float(distance))
        print(f"Nearby Estabs: {nearby_establishments}")
        new_results = []
        for result in results['hits']['hits']:
            print(f"Result: {result['_source']['establishment']['name']}")
            if result['_source']['establishment']['name'] in nearby_establishments:
                new_results.append(result)
        results['hits']['hits'] = new_results
    for i, result in enumerate(results['hits']['hits']):
        print(f"Result #{i}: {result['_source']['title']}, Score: {result['_score']}")
    return results

# Reset the index
def reset_index(deals: list = None):
    # Set up the Elasticsearch connection
    es = _setup_es()
    # Reset the index
    _reset_index(es)
    # Index all deals
    if deals:
        _index_all_deals(es, deals)
    return True

# Check if the index is up to date
def check_index(deals: list):
    # Set up the Elasticsearch connection
    es = _setup_es()
    # Check if the index exists
    if not _check_if_index_exists(es):
        return False
    # Get the length of the index
    index_length = _get_length_of_index(es)
    # Compare the length of the index with the length of the deals list
    return index_length == len(deals)
        

def _get_nearby_establishments(user_lat, user_lng, distance):
    # load all establishments from firestore
    establishments = db.collection('establishments').stream()
    establishments_list = [establishment.to_dict() for establishment in establishments]
    nearby_establishments = []

    for est in establishments_list:
        est_lat = float(est['latitude'])
        est_lng = float(est['longitude'])
        
        # only return establishments within distance of user's coordinates
        print(f"{_haversine(user_lat, user_lng, est_lat, est_lng)} <= {float(distance)}")
        if float(_haversine(user_lat, user_lng, est_lat, est_lng)) <= float(distance):
            nearby_establishments.append(est['name'].lower())

    return nearby_establishments

from math import radians, cos, sin, asin, sqrt
def _haversine(lat1, lng1, lat2, lng2):
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