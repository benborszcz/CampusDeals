import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime
from profanity import profanity

def duplicate_collection(source_collection, destination_collection):
    # Initialize Firestore
    if not firebase_admin._apps:
        cred = credentials.Certificate('app/firebase_service_account.json')
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Reference to the source collection
    source_ref = db.collection(source_collection)
    docs = source_ref.stream()

    # Create the destination collection
    dest_ref = db.collection(destination_collection)

    # Copy each document from the source to the destination
    for doc in docs:
        doc_dict = doc.to_dict()
        dest_ref.document(doc.id).set(doc_dict)
        print(f'Duplicated document {doc.id}')

def analyze_deal_comments(source_collection):
    # Initialize Firestore
    if not firebase_admin._apps:
        cred = credentials.Certificate('app/firebase_service_account.json')
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Reference to the deals collection
    deals_ref = db.collection(source_collection)
    deals = deals_ref.stream()
    deals = [deal.to_dict() for deal in deals]

    # Count the number of comments for each deal
    for deal in deals:
        deal_id = deal['deal_id']
        comment_count = len(deal.get('comments', []))
        print(f'Deal {deal_id} has {comment_count} comments')

    # If username is none set user_id as username
    for deal in deals:
        for comment in deal.get('comments', []):
            if comment['username'] is None:
                print(f'Comment {comment["comment_id"]} has no username, setting {comment["user_id"]} as username')
                comment['username'] = comment['user_id']
                # Update the comments in Firestore
                print(f'Updating comment {comment["comment_id"]} with username {comment["username"]}')
                deal_ref = deals_ref.document(deal['deal_id'])
                deal_ref.update({'comments': deal['comments']})

def remove_comments_from_unknown(source_collection_name):
    # Initialize Firestore
    if not firebase_admin._apps:
        cred = credentials.Certificate('app/firebase_service_account.json')
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Reference to the deals collection
    deals_ref = db.collection(source_collection_name)
    deals = deals_ref.stream()
    deals = [deal.to_dict() for deal in deals]

    # Remove comments from unknown users
    for deal in deals:
        for comment in deal.get('comments', []):
            if comment['username'] == 'Unknown':
                print(f'Removing comment {comment["comment_id"]} from deal {deal["deal_id"]}')
                deal['comments'].remove(comment)
                # Update the comments in Firestore
                deal_ref = deals_ref.document(deal['deal_id'])
                deal_ref.update({'comments': deal['comments']})

def remove_comments_with_profanity(source_collection_name):
    # Initialize Firestore
    if not firebase_admin._apps:
        cred = credentials.Certificate('app/firebase_service_account.json')
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Reference to the deals collection
    deals_ref = db.collection(source_collection_name)
    deals = deals_ref.stream()
    deals = [deal.to_dict() for deal in deals]

    # Remove comments with profanity
    for deal in deals:
        for comment in deal.get('comments', []):
            if profanity.contains_profanity(comment['text']):
                print(f'Removing comment {comment["comment_id"]} from deal {deal["deal_id"]}')
                deal['comments'].remove(comment)
                # Update the comments in Firestore
                deal_ref = deals_ref.document(deal['deal_id'])
                deal_ref.update({'comments': deal['comments']})

# If tags is outside deal_details move it inside
def move_tags_inside_deal_details(source_collection_name):
    # Initialize Firestore
    if not firebase_admin._apps:
        cred = credentials.Certificate('app/firebase_service_account.json')
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Reference to the deals collection
    deals_ref = db.collection(source_collection_name)
    deals = deals_ref.stream()
    deals = [deal.to_dict() for deal in deals]

    # Move tags inside deal_details
    for deal in deals:
        if 'tags' in deal:
            deal_details = deal.get('deal_details', {})
            deal_details['tags'] = deal['tags']
            deal['deal_details'] = deal_details
            del deal['tags']
            # Update the deal in Firestore
            deal_ref = deals_ref.document(deal['deal_id'])
            deal_ref.update(deal)
    
    # If tags does not exist at all put it inside deal_details
    for deal in deals:
        if 'tags' not in deal:
            deal_details = deal.get('deal_details', {})
            deal_details['tags'] = ['Bar']
            deal['deal_details'] = deal_details
            # Update the deal in Firestore
            deal_ref = deals_ref.document(deal['deal_id'])
            deal_ref.update(deal)


# If tags is inside deal_details move it outside
def move_tags_outside_deal_details(source_collection_name):
    # Initialize Firestore
    if not firebase_admin._apps:
        cred = credentials.Certificate('app/firebase_service_account.json')
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Reference to the deals collection
    deals_ref = db.collection(source_collection_name)
    deals = deals_ref.stream()
    deals = [deal.to_dict() for deal in deals]

    # Move tags outside deal_details
    for deal in deals:
        deal_details = deal.get('deal_details', {})
        if 'tags' in deal_details:
            deal['tags'] = deal_details['tags']
            del deal_details['tags']
            deal['deal_details'] = deal_details
            # Update the deal in Firestore
            deal_ref = deals_ref.document(deal['deal_id'])
            deal_ref.update(deal)

    # If tags does not exist at all put it outside deal_details
    for deal in deals:
        deal_details = deal.get('deal_details', {})
        if 'tags' not in deal and 'tags' not in deal_details:
            deal['tags'] = ['Bar']
            # Update the deal in Firestore
            deal_ref = deals_ref.document(deal['deal_id'])
            deal_ref.update(deal)

def change_upvotes_to_random_number(source_collection_name):
    # Initialize Firestore
    if not firebase_admin._apps:
        cred = credentials.Certificate('app/firebase_service_account.json')
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Reference to the deals collection
    deals_ref = db.collection(source_collection_name)
    deals = deals_ref.stream()
    deals = [deal.to_dict() for deal in deals]

    # Change upvotes to random number
    import random
    for deal in deals:
        deal['upvotes'] = random.randint(0, 150)
        # Update the deal in Firestore
        deal_ref = deals_ref.document(deal['deal_id'])
        deal_ref.update(deal)

def change_downvotes_to_random_number(source_collection_name):
    # Initialize Firestore
    if not firebase_admin._apps:
        cred = credentials.Certificate('app/firebase_service_account.json')
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Reference to the deals collection
    deals_ref = db.collection(source_collection_name)
    deals = deals_ref.stream()
    deals = [deal.to_dict() for deal in deals]

    # Change downvotes to random number
    import random
    for deal in deals:
        deal['downvotes'] = random.randint(0, 50)
        # Update the deal in Firestore
        deal_ref = deals_ref.document(deal['deal_id'])
        deal_ref.update(deal)

if __name__ == "__main__":
    source_collection_name = 'deals2'
    destination_collection_name = 'deals_backup_'+datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    duplicate_collection(source_collection_name, destination_collection_name)
    change_downvotes_to_random_number(source_collection_name)
    change_upvotes_to_random_number(source_collection_name)