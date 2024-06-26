from itertools import groupby
from operator import itemgetter
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, get_flashed_messages
from . import app, db
from flask_wtf.csrf import generate_csrf
from wtforms.validators import Optional, DataRequired
from .forms import DealSubmissionForm
from .utils import index_deal, search_deals, parse_deal_submission, transform_deal_structure, reset_elasticsearch, is_elasticsearch_empty, get_active_deals, get_time_until_deals_end, get_time_until_deals_start, autocomplete_deals
import config
from .elastic_utils import check_index, reset_index, search_deals
from firebase_admin import firestore, storage
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
import os
from app import db
from werkzeug.security import generate_password_hash, check_password_hash



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
    if check_index(deal_list):
        reset_index(deal_list)

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

    # Find the time_until_start and for time_until_end for each deal
    until_starts = get_time_until_deals_start(deal_list)
    until_ends = get_time_until_deals_end(deal_list)
    print(len(deal_list), len(until_starts), len(until_ends))
    for i, deal in enumerate(deal_list):
        # Convert the timedelta to string for display
        deal['time_until_start'] = until_starts[i].days * 24 + until_starts[i].seconds // 3600
        deal['time_until_end'] = until_ends[i].days * 24 + until_ends[i].seconds // 3600

    # Create a list of active deals
    active_deals = get_active_deals(deal_list)

    # Sort active deals by time until end
    active_deals = sorted(active_deals, key=lambda k: k['time_until_end'])

    # Create a list of upcoming deals
    upcoming_deals = [deal for deal in deal_list if deal not in active_deals]

    # Sort upcoming deals by time until start
    upcoming_deals = sorted(upcoming_deals, key=lambda k: k['time_until_start'])

    for deal in upcoming_deals:
        print(f"Deal: {deal['title']}, Time until start: {deal['time_until_start']}, Time until end: {deal['time_until_end']}")

    # Create list of Active deals and next 10 upcoming deals
    map_deals = active_deals + upcoming_deals[:10]

    return render_template('index.html', popular_deals=deal_list[:6], deals_json=json.dumps(map_deals), active_deals=active_deals, upcoming_deals=upcoming_deals, enumerate=enumerate, len=len)

@app.route('/deal_dashboard')
def deal_dashboard():
    """
    Dashboard page that shows all deals in database with filters
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
    if check_index(deal_list):
        reset_index(deal_list)

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

    return render_template('deal_dashboard.html', popular_deals=deal_list, deals_json=json.dumps(deal_list))

@app.route('/submit-deal', methods=['POST', 'GET'])
def submit_deal():

    # load all establishments from firestore
    establishments = db.collection('establishments').stream()
    establishment_list = [establishment.to_dict() for establishment in establishments]

    form = DealSubmissionForm(establishments=establishment_list)
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
        #hits = search_deals(query, days, distance, userLat, userLng)
        hits = search_deals(query, days, distance, userLat, userLng)["hits"]["hits"]
        results = []

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

        # load all establishments from firestore
        establishments = db.collection('establishments').stream()
        establishment_list = [establishment.to_dict() for establishment in establishments]

        # link deals to establishments
        for deal in deal_results:
            for establishment in establishment_list:
                if deal['establishment']['name'] == establishment['name'] or deal['establishment']['name'] in establishment['shortname']:
                    deal['establishment'] = establishment

        return render_template('search_results.html', results=deal_results, enumerate=enumerate, len=len)
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

@app.route('/deal_details_dashboard/<deal_id>', methods=['GET'])
def deal_details_dashboard(deal_id):
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

    return jsonify(deal_dict)

@app.route('/deal/<deal_id>/upvote', methods=['POST'])
@login_required
def upvote_deal(deal_id):
    deal_ref = db.collection(config.DEAL_COLLECTION).document(deal_id)
    deal_ref.update({"upvotes": firestore.Increment(1)})

    user_ref = db.collection('users').document(current_user.id)
    user_ref.update({
        'upvoted_deals': firestore.ArrayUnion([deal_id])
    })
    return jsonify(success=True), 200

@login_required
@app.route('/deal/<deal_id>/downvote', methods=['POST'])
def downvote_deal(deal_id):
    deal_ref = db.collection(config.DEAL_COLLECTION).document(deal_id)
    deal_ref.update({"downvotes": firestore.Increment(1)})

    user_ref = db.collection('users').document(current_user.id)
    user_ref.update({
        'upvoted_deals': firestore.ArrayRemove([deal_id])
    })
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

    # load all establishments from firestore
    establishments = db.collection('establishments').stream()
    establishment_list = [establishment.to_dict() for establishment in establishments]

    # link deals to establishments
    for deal in daily_deals:
        for establishment in establishment_list:
            if deal['establishment']['name'] == establishment['name'] or deal['establishment']['name'] in establishment['shortname']:
                deal['establishment'] = establishment


    # Render the 'daily_deals.html' template
    return render_template('daily_deals.html', daily_deals=daily_deals, enumerate=enumerate, len=len)

@app.route('/view-comments-dashboard/<deal_id>', methods=['GET', 'POST'])
def view_and_add_comments_dashboard(deal_id):
    deal_ref = db.collection(config.DEAL_COLLECTION).document(deal_id)
    deal = deal_ref.get().to_dict()
    comments_ref = deal_ref.collection("comments").stream()
    
    # Handle comment submission
    comment_form = CommentForm(request.form)
    if comment_form.validate_on_submit() and current_user.is_authenticated:
        new_comment_text = comment_form.comment.data

        # Check for profanity using the profanity library
        if profanity.contains_profanity(new_comment_text):
            flash('Your comment contains profanity and cannot be posted.', 'danger')
            return jsonify({'messages': get_flashed_messages(with_categories=True)}), 400

        new_comment = {
            'comment_id': str(uuid.uuid4()),
            'user_id': current_user.id,
            'username': current_user.username,
            'text': new_comment_text,
            'time': datetime.now().isoformat(),
            'upvotes': 0,
            'downvotes': 0,
            'profile_picture': current_user.profile_picture_url 
        }

        # Add new comment document to comments collection
        deal_ref.collection("comments").document(new_comment['comment_id']).set(new_comment)

        # Generate a new CSRF token and include it in the JSON response
        csrf_token = generate_csrf()
        flash('Comment added successfully!', 'success')
        return jsonify({'csrf_token': csrf_token, 'messages': get_flashed_messages(with_categories=True)}), 201

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

    for comment in comments:
        comment[0]['time'] = datetime.strptime(comment[0].get('time'), '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%d')
        for subcomment in comment[1]:
            subcomment['time'] = datetime.strptime(subcomment.get('time'), '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%d')

    # Sort comments based on votes or other criteria if needed
    sorted_comments = sorted(comments, key=lambda k: k[0].get('upvotes', 0) - k[0].get('downvotes', 0), reverse=True)

    # Generate a new CSRF token and include it in the JSON response
    csrf_token = generate_csrf()
    return jsonify({'title': deal.get('title'), 'user_authenticated': current_user.is_authenticated, 
                    'comments': sorted_comments, 'csrf_token': csrf_token, 'messages': get_flashed_messages(with_categories=True)})

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
            'downvotes': 0,
            'profile_picture': current_user.profile_picture_url 
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
            'downvotes': 0,
            'profile_picture': current_user.profile_picture_url 
        }

        # Add new subcomment document to comments collection under the parent comment document
        deal_ref.collection("comments").document(parent_id).collection("comments").document(new_comment['comment_id']).set(new_comment)
        flash('Comment added successfully!', 'success')
        return redirect(url_for('view_and_add_comments', deal_id=deal_id))
    
@app.route('/view-comments-dashboard/<deal_id>/<parent_id>', methods=['GET', 'POST'])
def add_subcomments_dashboard(deal_id, parent_id):
    comment_form = CommentForm()
    deal_ref = db.collection(config.DEAL_COLLECTION).document(deal_id)

    # Handle new subcomments
    if comment_form.validate_on_submit() and current_user.is_authenticated:
        new_comment_text = comment_form.comment.data

        # Check for profanity using the profanity library
        if profanity.contains_profanity(new_comment_text):
            flash('Your comment contains profanity and cannot be posted.', 'danger')
            return jsonify({'messages': get_flashed_messages(with_categories=True)}), 400

        new_comment = {
            'comment_id': str(uuid.uuid4()),
            'user_id': current_user.id,
            'username': current_user.username,
            'text': new_comment_text,
            'time': datetime.now().isoformat(),
            'upvotes': 0,
            'downvotes': 0,
            'profile_picture': current_user.profile_picture_url 
        }

        # Add new subcomment document to comments collection under the parent comment document
        deal_ref.collection("comments").document(parent_id).collection("comments").document(new_comment['comment_id']).set(new_comment)
        csrf_token = generate_csrf()
        flash('Comment added successfully!', 'success')
        return jsonify({'csrf_token': csrf_token, 'messages': get_flashed_messages(with_categories=True)}), 201

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

@login_required
@app.route("/profile")
def profile():
    user_ref = db.collection('users').document(current_user.id)

    user_doc = user_ref.get()

    if not user_doc.exists:
        flash("User not found.", "error")
        return redirect(url_for('index'))
    
    # Retrieve the list of upvoted deals
    user_data = user_doc.to_dict()
    upvoted_deals = user_data.get('upvoted_deals', [])
    
    # Initialize a list to hold the details of the upvoted deals
    upvoted_deal_details = []
    
    # Fetch the details of each upvoted deal
    for deal_id in upvoted_deals:
        deal_ref = db.collection(config.DEAL_COLLECTION).document(deal_id)
        
        deal_doc = deal_ref.get()
        
        if deal_doc.exists:
            upvoted_deal_details.append(deal_doc.to_dict())
    
    return render_template('profile.html', user_id=current_user.id, upvoted_deals=upvoted_deal_details, enumerate=enumerate, len=len)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    # Update the username and email
    new_username = request.form.get('username')
    new_email = request.form.get('email')

    user_ref = db.collection('users').document(current_user.id)

    # Check for duplicate usernames
    if new_username and new_username != current_user.username:
        username_ref = db.collection('users').where('username', '==', new_username).get()
        if username_ref and any(doc.id != current_user.id for doc in username_ref):
            flash('Username already taken by another user. Please choose another.', 'error')
            return render_template('edit_profile.html')
        else:
            user_ref.update({'username': new_username})

    # Check for duplicate emails
    if new_email and new_email != current_user.email:
        email_ref = db.collection('users').where('email', '==', new_email).get()
        if email_ref and any(doc.id != current_user.id for doc in email_ref):
            flash('Email is already in use by another user. Please use a different email.', 'error')
            return render_template('edit_profile.html')
        else:
            user_ref.update({'email': new_email})

    # Update the password
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')

    if current_password and new_password and confirm_new_password:
        # Verify current password
        user_data = user_ref.get().to_dict()
        if not check_password_hash(user_data['password'], current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('edit_profile.html')

        # Check if new passwords match
        if new_password != confirm_new_password:
            flash('New passwords do not match.', 'error')
            return render_template('edit_profile.html')

        # Update password in database
        hashed_new_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        user_ref.update({'password': hashed_new_password})

    # Check for the file upload
    file = request.files.get('profile_picture')
    if file and file.filename:
        # Check for PNGs and JPGs
        if not (file.filename.lower().endswith('jpg') or file.filename.lower().endswith('png') or file.filename.lower().endswith('jpeg')):
            flash('Only JPG and PNG files are allowed for the profile picture.', 'error')
            return render_template('edit_profile.html')

        filename = f"{current_user.id}.{file.filename.split('.')[-1]}"

        bucket = storage.bucket(name='campusdeals-686be.appspot.com')
        blob = bucket.blob(f"profile_picture/{filename}")

        blob.content_disposition = 'inline'
        blob.upload_from_file(file, content_type=file.mimetype)

        firebase_style_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{blob.name.replace('/', '%2F')}?alt=media"
        
        # Update the user's profile picture URL in the database
        user_ref.update({'profile_picture_url': firebase_style_url})
        current_user.profile_picture_url = firebase_style_url

        new_user_data = user_ref.get().to_dict()
        current_user.profile_picture_url = new_user_data.get('profile_picture_url') 

        print(current_user.profile_picture_url)

        updated_user_data = user_ref.get().to_dict()
        print('profile_picture_url:', updated_user_data.get('profile_picture_url'))

    flash('Profile updated successfully!')
    return redirect(url_for('profile'))

@login_required
@app.route("/edit_profile")
def edit_profile():
    return render_template('edit_profile.html', user_id = current_user.id)


@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('query', '')
    suggestions = autocomplete_deals(query)
    return jsonify(suggestions)

@app.route('/newsletter', methods=['GET'])
def newsletter():
    return render_template('newsletter.html')

