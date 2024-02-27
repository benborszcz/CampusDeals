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


if __name__ == "__main__":
    source_collection_name = 'deals'
    destination_collection_name = 'deals_backup_'+datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    #remove_comments_with_profanity(source_collection_name)