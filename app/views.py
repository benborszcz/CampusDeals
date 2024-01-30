from flask import Flask, render_template, request, redirect, url_for, jsonify
from . import app
from wtforms.validators import Optional, DataRequired
from .forms import DealSubmissionForm
from .utils import index_deal, search_deals, parse_deal_submission, transform_deal_structure, reset_elasticsearch, is_elasticsearch_empty
import config
from geopy.geocoders import Nominatim  # Import Nominatim from Geopy


@app.route('/')
def index():
    """
    Home page that could show popular deals or a search bar.
    """ 
    # load all deals from firestore
    deals = db.collection('deals').stream()
    deal_list = [deal.to_dict() for deal in deals]
    # index all deals in elasticsearch
    if config.ELASTICSEARCH_SERVICE != 'bonsai' or is_elasticsearch_empty():
        reset_elasticsearch()
        for deal in deal_list:
            index_deal(deal)
    return render_template('index.html', popular_deals=deal_list)

from flask import request, jsonify
from . import app, db

geolocator = Nominatim(user_agent="CampusDeals")

@app.route('/submit-deal', methods=['POST', 'GET'])
def submit_deal():
    form = DealSubmissionForm()

    if request.method == 'POST':
        # Conditionally adjust validators based on "All Day" checkbox
        if 'all_day' in request.form and request.form['all_day'] == 'y':
            form.start_time.validators = [Optional()]
            form.end_time.validators = [Optional()]
        else:
            form.start_time.validators = [DataRequired()]
            form.end_time.validators = [DataRequired()]

    if form.validate_on_submit():
        # Parse the form data using OpenAI's LLM
        print(str(form.data))
        deal_data = transform_deal_structure(parse_deal_submission(str(form.data)))

        # Geocode the establishment location to get latitude and longitude
        location = deal_data.get('establishment_location')
        if location:
            location_info = geolocator.geocode(location)
            if location_info:
                deal_data['latitude'] = location_info.latitude
                deal_data['longitude'] = location_info.longitude

        # Add a new document to the Firestore collection with the specified deal_id
        db.collection('deals').document(deal_data['deal_id']).set(deal_data)

        # Index the new deal in Elasticsearch
        index_deal(deal_data)

        return redirect(url_for('index'))

    return render_template('submit_deal.html', form=form)

@app.route('/deals', methods=['GET'])
def get_deals():
    """
    Route to get all deals.
    """
    # Retrieve all documents from the Firestore collection
    deals = db.collection('deals').stream()
    deal_list = [deal.to_dict() for deal in deals]
    return jsonify(deal_list), 200

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    location = request.args.get('location')
    radius = request.args.get('radius', type=float, default=5.0)  # Default radius to 5.0 km

    if query:
        # Assuming search_deals returns a list of Elasticsearch documents
        hits = search_deals(query, location, radius)
        results = []

        # Calculate distance and filter results based on radius
        for hit in hits:
            deal_location = hit['_source'].get('location')  # Adjust this based on your deal data structure
            if deal_location:
                deal_latitude = deal_location.get('latitude')
                deal_longitude = deal_location.get('longitude')

                if deal_latitude is not None and deal_longitude is not None:
                    if location:
                        user_location = geolocator.geocode(location)
                        if user_location:
                            user_latitude = user_location.latitude
                            user_longitude = user_location.longitude

                            distance = geodesic((user_latitude, user_longitude), (deal_latitude, deal_longitude)).km
                            if distance <= radius:
                                results.append(hit['_source'])
                    else:
                        results.append(hit['_source'])

        return render_template('search_results.html', results=results)

    return redirect(url_for('index'))

@app.route('/deal_details/<deal_id>', methods=['GET'])
def deal_details(deal_id):
    """
    Route to get deal details.
    """
    # Retrieve the document from the Firestore collection
    deal = db.collection('deals').document(deal_id).get()
    print(deal.to_dict())
    return render_template('deal_details.html', deal=deal.to_dict())
