from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from . import app, db
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

@app.route('/deal_dashboard')
def deal_dashboard():
    """
    Dashboard page that shows all deals in database with filters
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

    return render_template('deal_dashboard.html', popular_deals=deal_list)

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
    days = request.args.getlist('day')
    if query or days:
        # Assuming search_deals returns a list of Firestore documents
        hits = search_deals(query, days)
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
    # deal = db.collection('deals').document(deal_id).get()
    # print(deal.to_dict())
    # return render_template('deal_details.html', deal=deal.to_dict())

    deal = db.collection('deals').document(deal_id).get().to_dict()
    return jsonify(deal)


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
def view_and_add_comments(deal_id):
    deal_ref = db.collection('deals').document(deal_id)
    deal = deal_ref.get().to_dict()
    comments = deal.get('comments', [])

    comment_form = CommentForm()

    if comment_form.validate_on_submit() and current_user.is_authenticated:
        new_comment_text = comment_form.comment.data

        # Check for profanity using the profanity library
        if profanity.contains_profanity(new_comment_text):
            flash('Your comment contains profanity and cannot be posted.', 'error')
            return redirect(url_for('view_and_add_comments', deal_id=deal_id))

        new_comment = {
            'user_id': current_user.id,
            'username': current_user.username,
            'text': new_comment_text,
            'time': datetime.now().isoformat()
        }

        # Update the deal document with the new comment
        deal_ref.update({
            'comments': firestore.ArrayUnion([new_comment])
        })

        flash('Comment added successfully!', 'success')
        return redirect(url_for('view_and_add_comments', deal_id=deal_id))

    # Format the date before passing it to the template
    formatted_comments = [
        {
            **comment,
            'time': datetime.strptime(comment['time'], '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%d')
        }
        if 'time' in comment else comment
        for comment in comments
    ]

    return render_template('view_comments.html', deal_name=deal.get('title', 'Unknown Deal'),
                           deal_id=deal_id, comments=formatted_comments, comment_form=comment_form, current_user=current_user)