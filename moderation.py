from openai import OpenAI
import config
import json
from profanity import profanity
import pandas as pd
import numpy as np

class Moderator:
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def moderate_text(self, text):
        # OpenAI's moderation model
        response = self.client.moderations.create(input=text)
        output_o = response.results[0]

        # Profanity filter
        output_p = profanity.contains_profanity(text)

        # Return the flagged status
        return output_o.flagged or output_p
    
    def check_duplicate(self, text, collection):
        # Get the embedding for the input text
        text_embedding = self._get_embedding(text)

        sim_list = []
        for i, item in enumerate(collection):
            # Print update on progress
            print(f"Comparing {i+1} of {len(collection)}")

            # Get the embedding for the item
            item_embedding = self._get_embedding(item)

            # Convert both embeddings to numpy arrays
            text_embedding = np.array(text_embedding)
            item_embedding = np.array(item_embedding)

            # Calculate the cosine similarity
            similarity = self._cosing_similarity(text_embedding, item_embedding)

            # Add the comparison to the list
            comparison = {"input_text": text, "collection_text": item, "similarity": similarity}
            sim_list.append(comparison)

        return sim_list

    def _get_embedding(self, text, model="text-embedding-3-small"):
        text = text.replace("\n", " ")
        return (self.client.embeddings.create(input = [text], model=model, dimensions=1000).data[0].embedding)
    
    def _normalize_l2(self, x):
        x = np.array(x)
        if x.ndim == 1:
            norm = np.linalg.norm(x)
            if norm == 0:
                return x
            return x / norm
        else:
            norm = np.linalg.norm(x, 2, axis=1, keepdims=True)
            return np.where(norm == 0, x, x / norm)
        
    def _cosing_similarity(self, x, y):
        return np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y))



# Example usage:
moderator = Moderator()
output = moderator.moderate_text("Fuck")
print(output)

# Create collection of mock deal descriptions
collection = [
    '$2 off all Drafts from 4-6pm on Mondays',
    '50% off Busch Light from 4-6pm on Tuesdays',
    '$3 Wells all night on Wednesdays',
    'Buy one get one free Captain Morgan on Thursdays',
    '$1 off all Craft Beers from 4-close on Fridays',
    'Half-price Margaritas all night on Saturdays',
    '2-for-1 Shots all night on Sundays',
    '$4 off all Pitchers from 4-6pm on Mondays',
    '25% off all Wine from 4-6pm on Tuesdays',
    '$2 off all Cocktails all night on Wednesdays',
    'Buy one get one half off all Tequila on Thursdays',
    '$1 off all IPAs from 4-close on Fridays',
    'Half-price Mojitos all night on Saturdays',
    '2-for-1 Long Island Iced Teas all night on Sundays',
    '$3 off all Whiskey Shots from 4-6pm on Mondays',
    '30% off all Vodka Drinks from 4-6pm on Tuesdays',
    '$2 off all Rum Cocktails all night on Wednesdays',
    'Buy one get one free Gin & Tonics on Thursdays',
    '$1 off all Ciders from 4-close on Fridays',
    'Half-price Martinis all night on Saturdays'
]

collection = [
    {'establishment': 'Joe\'s Bar', 'days_active': ['Thursday'], 'start_time': '18:00:00', 'end_time': '22:00:00', 'description': '$3 off all Whiskey Shots'},
    {'establishment': 'Midway', 'days_active': ['Friday', 'Saturday'], 'start_time': 'Open', 'end_time': 'Close', 'description': '$2 off all Rum Cocktails'},
    {'establishment': 'The Anchor', 'days_active': ['Monday'], 'start_time': '17:00:00', 'end_time': '20:00:00', 'description': 'Half-price Appetizers'},
    {'establishment': 'Luna\'s Cafe', 'days_active': ['Wednesday', 'Thursday'], 'start_time': 'Open', 'end_time': '11:00:00', 'description': 'Buy one get one free on all espresso drinks'},
    {'establishment': 'The Dockside', 'days_active': ['Sunday'], 'start_time': '12:00:00', 'end_time': '16:00:00', 'description': '25% off seafood platters'},
    {'establishment': 'Brew Brothers', 'days_active': ['Tuesday', 'Wednesday'], 'start_time': '15:00:00', 'end_time': '18:00:00', 'description': '$1 off craft beers'},
    {'establishment': 'The Golden Spoon', 'days_active': ['Monday', 'Tuesday', 'Wednesday'], 'start_time': 'Open', 'end_time': 'Close', 'description': '10% off total bill'},
    {'establishment': 'Vine & Dine', 'days_active': ['Thursday', 'Friday'], 'start_time': '19:00:00', 'end_time': '21:00:00', 'description': 'Complimentary wine tasting with any entrée'},
    {'establishment': 'The Night Owl', 'days_active': ['Friday', 'Saturday'], 'start_time': '22:00:00', 'end_time': '02:00:00', 'description': 'Free cover charge'},
    {'establishment': 'Sunset Grill', 'days_active': ['Sunday'], 'start_time': 'Open', 'end_time': 'Close', 'description': 'Kids eat free'},
    {'establishment': 'The Greenhouse', 'days_active': ['Monday', 'Tuesday'], 'start_time': '17:00:00', 'end_time': '19:00:00', 'description': '2 for 1 vegan dishes'},
    {'establishment': 'Harbor View', 'days_active': ['Wednesday', 'Thursday', 'Friday'], 'start_time': '16:00:00', 'end_time': '18:00:00', 'description': 'Oyster Happy Hour'},
    {'establishment': 'The Pit Stop', 'days_active': ['Saturday', 'Sunday'], 'start_time': 'Open', 'end_time': '15:00:00', 'description': '$5 Bloody Marys'},
    {'establishment': 'Mystic Pizzeria', 'days_active': ['Tuesday'], 'start_time': 'Open', 'end_time': 'Close', 'description': '20% off all pizzas'},
    {'establishment': 'The Library', 'days_active': ['Wednesday'], 'start_time': '20:00:00', 'end_time': '23:00:00', 'description': 'Buy 2 get 1 free on all craft cocktails'},
    {'establishment': 'The Speakeasy', 'days_active': ['Thursday', 'Friday', 'Saturday'], 'start_time': '21:00:00', 'end_time': '01:00:00', 'description': 'Complimentary appetizer with premium cocktail purchase'},
    {'establishment': 'Café Del Mar', 'days_active': ['Monday'], 'start_time': 'Open', 'end_time': 'Close', 'description': 'Free coffee refill'},
    {'establishment': 'The Rooftop', 'days_active': ['Sunday'], 'start_time': '17:00:00', 'end_time': '20:00:00', 'description': 'Sunset Specials on signature cocktails'},
    {'establishment': 'The Alley', 'days_active': ['Friday'], 'start_time': 'Open', 'end_time': 'Close', 'description': 'Half off bowling with shoe rental'},
    {'establishment': 'Ocean\'s Edge', 'days_active': ['Saturday', 'Sunday'], 'start_time': '18:00:00', 'end_time': '22:00:00', 'description': 'Complimentary dessert with any main course'}
]

collection_str = [(item['establishment'] + " | " + item['description'] + " | " + " ".join(item['days_active']) + " | " + item['start_time'] + " - " + item['end_time']) for item in collection]
print(collection_str)

# Get the similarity between the input text and the collection_str
output = moderator.check_duplicate("Joes | $3 off Whiskey | Thursday | 18:00:00 - 22:00:00", collection_str)

# Convert the output to a DataFrame
df = pd.DataFrame(output)

# Sort the DataFrame by similarity 
df = df.sort_values(by="similarity", ascending=False)

# Save the output to a CSV file
df.to_csv("output/output.csv", index=False)


