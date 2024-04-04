from itertools import groupby
from operator import itemgetter
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
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
from profanity import profanity
from .moderation import Moderator
import json
import uuid



class CommentForm(FlaskForm):
    comment = TextAreaField('Comment', validators=[DataRequired()])
    submit_comment = SubmitField('Submit Comment')

@app.route('/')
def index():
    """
    Home page that could show popular deals or a search bar.
    """
    # load all deals from firestore
    deals = db.collection(config.DEAL_COLLECTION).stream()
    deal_list = [deal.to_dict() for deal in deals]

    # load all establishments from firestore
    establishments = db.collection('establishments').stream()
    establishment_list = [establishment.to_dict() for establishment in establishments]

    # link deals to establishments
    for deal in deal_list:
        for establishment in establishment_list:
            if deal['establishment']['name'] == establishment['name'] or deal['establishment']['name'] in establishment['shortname']:
                deal['establishment'] = establishment

    # index all deals in elasticsearch
    if config.ELASTICSEARCH_SERVICE != 'bonsai' or is_elasticsearch_empty():
        reset_elasticsearch()
        for deal in deal_list:
            index_deal(deal)

    for deal in deal_list:
        deal['upvotes'] = deal['upvotes'] if 'upvotes' in deal else 0
        deal['downvotes'] = deal['downvotes'] if 'downvotes' in deal else 0
        deal['url'] = url_for('deal_details', deal_id=deal['deal_id']) # Assuming url_for is defined elsewhere
        deal['lat'] = deal['establishment']['latitude']
        deal['lng'] = deal['establishment']['longitude']
    deal_list = sorted(deal_list, key=lambda k: k['upvotes'] - k['downvotes'], reverse=True)

    # Function to slightly adjust coordinates
    def adjust_coords(lat, lng, count):
        # Define how much to adjust. These values can be very small.
        lat_adj = -0.00000
        lng_adj = -0.00007
        return lat + (lat_adj * count), lng + (lng_adj * count)

    # Group deals by their coordinates
    sorted_deals = sorted(deal_list, key=itemgetter('lat', 'lng'))
    for _, group in groupby(sorted_deals, key=itemgetter('lat', 'lng')):
        duplicates = list(group)
        if len(duplicates) > 1:
            for i, deal in enumerate(duplicates):
                # Adjust coordinates starting from the second item
                if i > 0:
                    print(f"Adjusting coordinates for {deal['title']}")
                    deal['lat'], deal['lng'] = adjust_coords(deal['lat'], deal['lng'], i)

    return render_template('index.html', popular_deals=deal_list, deals_json=json.dumps(deal_list))

from flask import request, jsonify
from . import app, db

@app.route('/submit-deal', methods=['POST', 'GET'])
def submit_deal():

    # load all establishments from firestore
    establishments = db.collection('establishments').stream()
    establishment_list = [establishment.to_dict() for establishment in establishments]

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
        moderator = Moderator()

        # Moderation check
        print('Moderating text')
        if moderator.moderate_text(str(form.data)):
            flash('Your deal contains profanity and cannot be posted.', 'error')
            print('Your deal contains profanity and cannot be posted.')
            return render_template('submit_deal.html', form=form, popup="Your deal contains profanity and cannot be posted.")

        # Transform the parsed data into a structure suitable for Firestore
        deal_data = transform_deal_structure(parse_deal_submission(str(form.data), establishment_list), establishment_list)

        # load all deals from firestore
        deals = db.collection(config.DEAL_COLLECTION).stream()
        deal_list = [deal.to_dict() for deal in deals]

        # Duplicate check
        print('Checking for duplicates')
        sim_list, details = moderator.check_duplicate_time_logic(deal_data, deal_list)
        if len(sim_list) > 0:
            flash('Your deal is a duplicate and cannot be posted.', 'error')
            print('Your deal is a duplicate and cannot be posted.')
            return render_template('submit_deal.html', form=form, popup="Your deal is a duplicate and cannot be posted.")


        # Add a new document to the Firestore collection with the specified deal_id
        db.collection(config.DEAL_COLLECTION).document(deal_data['deal_id']).set(deal_data)
        # Index the new deal in Elasticsearch
        index_deal(deal_data)
        return redirect(url_for('index'))

    return render_template('submit_deal.html', form=form, popup=None)

@app.route('/deals', methods=['GET'])
def get_deals():
    """
    Route to get all deals.
    """
    # Retrieve all documents from the Firestore collection
    deals = db.collection(config.DEAL_COLLECTION).stream()
    deal_list = [deal.to_dict() for deal in deals]
    return jsonify(deal_list), 200

@app.route('/establishments', methods=['GET'])
def establishments():
    """
    Route to get all establishments.
    """
    # Retrieve all documents from the Firestore collection
    establishments = db.collection('establishments').stream()
    establishment_list = [establishment.to_dict() for establishment in establishments]
    # Convert establishments.hours to normalized time (non-military time)

    return render_template('establishments.html', establishments=establishment_list)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    days = request.args.getlist('day')
    distance = request.args.get('distance')
    userLat = request.args.get('userLat')
    userLng = request.args.get('userLng')
    if query or days or distance:
        # Assuming search_deals returns a list of Firestore documents
        hits = search_deals(query, days, distance, userLat, userLng)
        results = []
        print(hits)
        for hit in hits:
            hit['_source']['_score'] = hit['_score']
            results.append(hit['_source'])

        deals = db.collection(config.DEAL_COLLECTION).stream()
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

@app.route('/establishment_details/<establishment_name>', methods=['GET'])
def establishment_details(establishment_name):
    """
    Route to get establishment details.
    """
    # Retrieve the document from the Firestore collection
    establishment = db.collection('establishments').document(establishment_name).get()
    establishment_dict = establishment.to_dict()

    # load all deals from firestore
    deals = db.collection(config.DEAL_COLLECTION).stream()
    deal_list = [deal.to_dict() for deal in deals]

    # link deals to establishment
    for deal in deal_list:
        if deal['establishment']['name'] == establishment_dict['name'] or deal['establishment']['name'] in establishment_dict['shortname']:
            deal['establishment'] = establishment_dict

    for day, hours in establishment_dict['hours'].items():
        if hours:
            if hours == 'Closed' or hours == 'Varies':
                establishment_dict['hours'][day] = hours
                continue
            start_time = hours.split('-')[0]
            if start_time == '24:00':
                start_time = '00:00'
            end_time = hours.split('-')[1]
            if end_time == '24:00':
                end_time = '00:00'
            start_time = datetime.strptime(start_time, '%H:%M').strftime('%I:%M %p')
            end_time = datetime.strptime(end_time, '%H:%M').strftime('%I:%M %p')
            print(f"Start time: {start_time}, End time: {end_time}")
            establishment_dict['hours'][day] = f"{start_time} - {end_time}"

    # put the hours in a list for easier iteration in the template called hours_list, also sort them by day of the week, the structure is a list of tuples with the day of the week[0] and the hours[1]
    establishment_dict['hours_list'] = sorted(establishment_dict['hours'].items(), key=lambda x: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].index(x[0]))

    print(establishment_dict['hours_list'])

    # create list of deals for the establishment
    deal_list = [deal for deal in deal_list if deal['establishment']['name'] == establishment_dict['name'] or deal['establishment']['name'] in establishment_dict['shortname']]

    return render_template('estab_details.html', establishment=establishment_dict, deals=deal_list)

@app.route('/deal_details/<deal_id>', methods=['GET'])
def deal_details(deal_id):
    """
    Route to get deal details.
    """
    # Retrieve the document from the Firestore collection
    deal = db.collection(config.DEAL_COLLECTION).document(deal_id).get()
    deal_dict = deal.to_dict()

    # load all establishments from firestore
    establishments = db.collection('establishments').stream()
    establishment_list = [establishment.to_dict() for establishment in establishments]

    # link deal to establishment
    for establishment in establishment_list:
        if deal_dict['establishment']['name'] == establishment['name'] or deal_dict['establishment']['name'] in establishment['shortname']:
            deal_dict['establishment'] = establishment

    return render_template('deal_details.html', deal=deal_dict, deals_json=json.dumps([deal_dict]))


@app.route('/deal/<deal_id>/upvote', methods=['POST'])
@login_required
def upvote_deal(deal_id):
    deal_ref = db.collection(config.DEAL_COLLECTION).document(deal_id)
    deal_ref.update({"upvotes": firestore.Increment(1)})
    return jsonify(success=True), 200

@login_required
@app.route('/deal/<deal_id>/downvote', methods=['POST'])
def downvote_deal(deal_id):
    deal_ref = db.collection(config.DEAL_COLLECTION).document(deal_id)
    deal_ref.update({"downvotes": firestore.Increment(1)})
    return jsonify(success=True), 200

@app.route('/daily-deals')
def daily_deals():
    # Get the current day of the week (e.g., 'Monday', 'Tuesday', etc.)
    current_day = datetime.now().strftime('%A')

    # Retrieve all documents from the Firestore collection
    deals = db.collection(config.DEAL_COLLECTION).stream()
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
def view_and_add_comments(deal_id):
    deal_ref = db.collection(config.DEAL_COLLECTION).document(deal_id)
    comments_ref = deal_ref.collection("comments").stream()
    deal = deal_ref.get().to_dict()
    comment_form = CommentForm()

    # Handle new comments
    if comment_form.validate_on_submit() and current_user.is_authenticated:
        new_comment_text = comment_form.comment.data

        # Check for profanity using the profanity library
        if profanity.contains_profanity(new_comment_text):
            flash('Your comment contains profanity and cannot be posted.', 'error')
            return redirect(url_for('view_and_add_comments', deal_id=deal_id))

        new_comment = {
            'comment_id': str(uuid.uuid4()),
            'user_id': current_user.id,
            'username': current_user.username,
            'text': new_comment_text,
            'time': datetime.now().isoformat(),
            'upvotes': 0,
            'downvotes': 0
        }

        # Add new comment document to comments collection
        deal_ref.collection("comments").document(new_comment['comment_id']).set(new_comment)

        flash('Comment added successfully!', 'success')
        return redirect(url_for('view_and_add_comments', deal_id=deal_id))

    # Put comments into array for template
    comments = []
    for comment in comments_ref:
        subcomments = []
        comment_contents = comment.to_dict()
        subcomments_ref = deal_ref.collection("comments").document(comment_contents['comment_id']).collection("comments").stream()
        for subcomment in subcomments_ref:
            subcomments.append(subcomment.to_dict())
        commentAsDict = [comment_contents, subcomments]
        comments.append(commentAsDict)

    # Format dates before passing comments array to template
    for comment in comments:
        comment[0]['time'] = datetime.strptime(comment[0].get('time'), '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%d')
        for subcomment in comment[1]:
            subcomment['time'] = datetime.strptime(subcomment.get('time'), '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%d')


    # Sort comments based on votes or other criteria if needed
    sorted_comments = sorted(comments, key=lambda k: k[0].get('upvotes', 0) - k[0].get('downvotes', 0))

    return render_template('view_comments.html', deal_name=deal.get('title', 'Unknown Deal'),
                           deal_id=deal_id, comments=sorted_comments, comment_form=comment_form, current_user=current_user)


@app.route('/view-comments/<deal_id>/<parent_id>', methods=['GET', 'POST'])
def add_subcomments(deal_id, parent_id):
    comment_form = CommentForm()
    deal_ref = db.collection(config.DEAL_COLLECTION).document(deal_id)

    # Handle new subcomments
    if comment_form.validate_on_submit() and current_user.is_authenticated:
        new_comment_text = comment_form.comment.data

        # Check for profanity using the profanity library
        if profanity.contains_profanity(new_comment_text):
            flash('Your comment contains profanity and cannot be posted.', 'error')
            return redirect(url_for('view_and_add_comments', deal_id=deal_id))

        new_comment = {
            'comment_id': str(uuid.uuid4()),
            'user_id': current_user.id,
            'username': current_user.username,
            'text': new_comment_text,
            'time': datetime.now().isoformat(),
            'upvotes': 0,
            'downvotes': 0
        }

        # Add new subcomment document to comments collection under the parent comment document
        deal_ref.collection("comments").document(parent_id).collection("comments").document(new_comment['comment_id']).set(new_comment)
        flash('Comment added successfully!', 'success')
        return redirect(url_for('view_and_add_comments', deal_id=deal_id))

@login_required
@app.route('/deal/<deal_id>/comment/<parent_id>/subcomment/<comment_id>/upvote', methods=['POST'])
def upvote_subcomment(deal_id, parent_id, comment_id):
    comment_ref = db.collection(config.DEAL_COLLECTION).document(deal_id).collection("comments").document(parent_id).collection("comments").document(comment_id)
    comment_ref.update({"upvotes": firestore.Increment(1)})
    return jsonify(success=True), 200

@login_required
@app.route('/deal/<deal_id>/comment/<parent_id>/subcomment/<comment_id>/downvote', methods=['POST'])
def downvote_subcomment(deal_id, parent_id, comment_id):
    comment_ref = db.collection(config.DEAL_COLLECTION).document(deal_id).collection("comments").document(parent_id).collection("comments").document(comment_id)
    comment_ref.update({"downvotes": firestore.Increment(1)})
    return jsonify(success=True), 200

@login_required
@app.route('/deal/<deal_id>/comment/<comment_id>/upvote', methods=['POST'])
def upvote_comment(deal_id,  comment_id):
    comment_ref = db.collection(config.DEAL_COLLECTION).document(deal_id).collection("comments").document(comment_id)
    comment_ref.update({"upvotes": firestore.Increment(1)})
    return jsonify(success=True), 200

@login_required
@app.route('/deal/<deal_id>/comment/<comment_id>/downvote', methods=['POST'])
def downvote_comment(deal_id, comment_id):
    comment_ref = db.collection(config.DEAL_COLLECTION).document(deal_id).collection("comments").document(comment_id)
    comment_ref.update({"downvotes": firestore.Increment(1)})
    return jsonify(success=True), 200
