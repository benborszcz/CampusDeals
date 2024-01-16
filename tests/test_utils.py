import pytest
import json
from app.utils import index_deal, search_deals, parse_deal_submission, transform_deal_structure, remove_deal, reset_elasticsearch
import json
import os
import time

# Get data for testing
mock_deal = {
    "deal_id": "test_deal_123",
    "title": "Test Deal",
    "description": "A test deal description.",
}

def test_index_deal():
    """
    Test indexing a deal in Elasticsearch.
    """
    # Index the deal in Elasticsearch
    response = index_deal(mock_deal)
    assert response['result'] == 'created' or response['result'] == 'updated'
    time.sleep(1)
    # Remove the deal from Elasticsearch
    remove_deal(mock_deal['deal_id'])

def test_search_deals():
    """
    Test searching for deals in Elasticsearch.
    """
    # Index the deal in Elasticsearch
    response = index_deal(mock_deal)
    assert response['result'] == 'created' or response['result'] == 'updated'
    time.sleep(1)
    # Get the Elasticsearch search response
    response = search_deals("Test Deal")
    print(response)
    assert mock_deal['deal_id'] == response[0]['_source']['deal_id']
    time.sleep(1)
    # Remove the deal from Elasticsearch
    remove_deal(mock_deal['deal_id'])

def test_parse_deal_submission_1():
    """
    Test parsing a deal submission with OpenAI's LLM.
    """
    # Get the OpenAI API response
    response = parse_deal_submission("50% off all drinks at Joe's Bar this Friday night!")
    print(response)
    assert response

def test_parse_deal_submission_2():
    """
    Test parsing a deal submission with OpenAI's LLM.
    """
    # Get the OpenAI API response
    response = parse_deal_submission("Midway Madness Wednesday 2pm-6pm, $1 wells, $1 bombs")
    print(response)
    assert response

def test_parse_deal_submission_3():
    """
    Test parsing a deal submission with OpenAI's LLM.
    """
    # Get the OpenAI API response
    response = parse_deal_submission("Eupouria Happy Hour 4pm-7pm, $2 off all drinks, $5 appetizers")
    print(response)
    assert response

def test_parse_deal_submission_4():
    """
    Test parsing a deal submission with OpenAI's LLM.
    """
    # Get the OpenAI API response
    response = parse_deal_submission("Out-R-Inn $2 Double Wells Thursdays All Night")
    print(response)
    assert response

def test_parse_index_search():
    """
    Test parsing a deal submission, indexing it, and searching for it.
    """
    # Reset Elasticsearch
    reset_elasticsearch()

    # Get the OpenAI API response
    response = parse_deal_submission("50% off all drinks at Joe's Bar this Friday night!")
    print(response)
    assert response

    # Transform the deal structure
    deal = transform_deal_structure(response)
    print(deal)
    # Index the deal in Elasticsearch
    index_deal(deal)
    time.sleep(1)
    # Get the Elasticsearch search response
    response = search_deals("Joe's")
    print(response)
    
    assert deal['deal_id'] == response[0]['_source']['deal_id']
    time.sleep(1)
    # Remove the deal from Elasticsearch
    remove_deal(deal['deal_id'])