from flask import Flask, render_template, request, redirect, url_for, jsonify
from . import app
from flask_wtf.csrf import generate_csrf
from wtforms.validators import Optional, DataRequired
from .forms import DealSubmissionForm
from .utils import index_deal, search_deals, parse_deal_submission, transform_deal_structure, reset_elasticsearch, is_elasticsearch_empty
import config
from firebase_admin import firestore
from datetime import datetime
from .auth import login_required
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired


class CommentForm(FlaskForm):
    comment = TextAreaField('Comment', validators=[DataRequired()])
    submit_comment = SubmitField('Submit Comment')

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

    for deal in deal_list:
        deal['upvotes'] = deal['upvotes'] if 'upvotes' in deal else 0
        deal['downvotes'] = deal['downvotes'] if 'downvotes' in deal else 0

    deal_list = sorted(deal_list, key=lambda k: k['upvotes'] - k['downvotes'], reverse=True)

    return render_template('index.html', popular_deals=deal_list)

from flask import request, jsonify
from . import app, db
from urllib.parse import urlencode
import requests
import logging
logging.basicConfig(level=logging.DEBUG)

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

        # Construct the address for geocoding and make a request to Google Maps Geocode API
        full_address = f"{form.street_address.data}, {form.city.data}, {form.state.data}, {form.zip_code.data}"
        encoded_address = urlencode({'address': full_address})
        api_key = config.GOOGLE_MAPS_API_KEY
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?{encoded_address}&key={api_key}"

        # Perform the geocoding request
        response = requests.get(geocode_url)
        if response.status_code == 200:
            geocode_data = response.json()
            if geocode_data['status'] == 'OK':
                # Extract the latitude and longitude
                latitude = geocode_data['results'][0]['geometry']['location']['lat']
                longitude = geocode_data['results'][0]['geometry']['location']['lng']

                # Add latitude and longitude before parsing data
                deal_data = form.data.copy()
                deal_data['latitude'] = latitude
                deal_data['longitude'] = longitude

                # Parse the form data and transform the deal structure
                deal_to_save = transform_deal_structure(parse_deal_submission(str(deal_data)))

                # Save the deal to Firestore and index in Elasticsearch
                db.collection('deals').document(deal_to_save['deal_id']).set(deal_to_save)
                index_deal(deal_to_save)

                # Redirect to the index page after successful deal submission
                return redirect(url_for('index'))
    else:
        logging.debug(f"Form validation errors: {form.errors}")

    # Render the deal submission form for GET requests or failed validations
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
    days = request.args.getlist('day')
    distance = request.args.get('distance')
    userLat = request.args.get('userLat')
    userLong = request.args.get('userLon')
    if query or days or distance:
        
        hits = search_deals(query, days, distance, userLat, userLong)
        results = []
        print(hits)
        for hit in hits:
            hit['_source']['_score'] = hit['_score']
            results.append(hit['_source'])

        deals = db.collection('deals').stream()
        deal_list = [deal.to_dict() for deal in deals]
        deal_results = [deal for deal in deal_list if deal['deal_id'] in [result['deal_id'] for result in results]]

        # Add score to each deal
        for deal in deal_results:
            for result in results:
                if deal['deal_id'] == result['deal_id']:
                    deal['_score'] = result['_score']
        
        for result in deal_results:
            print(f"Deal: {result['title']}, Score: {result['_score']}")

        return render_template('search_results.html', results=deal_results)
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


@app.route('/deal/<deal_id>/upvote', methods=['POST'])
def upvote_deal(deal_id):
    deal_ref = db.collection('deals').document(deal_id)
    deal_ref.update({"upvotes": firestore.Increment(1)})
    return jsonify(success=True), 200

@app.route('/deal/<deal_id>/downvote', methods=['POST'])
def downvote_deal(deal_id):
    deal_ref = db.collection('deals').document(deal_id)
    deal_ref.update({"downvotes": firestore.Increment(1)})
    return jsonify(success=True), 200

@app.route('/daily-deals')
def daily_deals():
    # Get the current day of the week (e.g., 'Monday', 'Tuesday', etc.)
    current_day = datetime.now().strftime('%A')

    # Retrieve all documents from the Firestore collection
    deals = db.collection('deals').stream()
    all_deals = [deal.to_dict() for deal in deals]

    # Debugging output
    print(f"Current day: {current_day}")
    print(f"Firestore All Deals: {all_deals}")

    # Filter deals for the current day (case-insensitive)
    daily_deals = [
        deal for deal in all_deals
        if current_day.lower() in map(str.lower, deal.get('deal_details', {}).get('days_active', []))
    ]

    # Debugging output
    print(f"Filtered Daily Deals: {daily_deals}")

    # Sort deals based on votes or other criteria if needed
    daily_deals = sorted(daily_deals, key=lambda k: k.get('upvotes', 0) - k.get('downvotes', 0), reverse=True)

    # Render the 'daily_deals.html' template
    return render_template('daily_deals.html', daily_deals=daily_deals)


@app.route('/view-comments/<deal_id>', methods=['GET', 'POST'])
def view_comments(deal_id):
    deal = db.collection('deals').document(deal_id).get().to_dict()
    comments = deal.get('comments', [])

    comment_form = CommentForm()

    if comment_form.validate_on_submit():
        # Handle comment submission logic here
        new_comment = comment_form.comment.data
        # Add the new comment to the deal document in Firestore
        db.collection('deals').document(deal_id).update({
            'comments': firestore.ArrayUnion([new_comment])
        })
        return redirect(url_for('view_comments', deal_id=deal_id))

    return render_template('view_comments.html', deal_name=deal.get('title', 'Unknown Deal'), deal_id=deal_id, comments=comments, comment_form=comment_form, current_user=current_user)

@app.route('/deal/<deal_id>/comments/add', methods=['POST'])
@login_required
def add_comment(deal_id):
    comment_text = request.form.get('comment')

    # Retrieve the document from the Firestore collection
    deal_ref = db.collection('deals').document(deal_id)
    deal = deal_ref.get().to_dict()  # Convert to dictionary

    # Retrieve existing comments from the deal document
    comments = deal.get('comments', [])

    # Add the new comment
    new_comment = {
    'user_id': current_user.id,
    'username': current_user.username,
    'text': comment_text,
    'time': datetime.now().isoformat()
    }
    comments.append(new_comment)
    # Update the deal document with the new comments
    deal_ref.update({"comments": comments})
    return redirect(url_for('view_comments', deal_id=deal_id))