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
        return self._normalize_l2(self.client.embeddings.create(input = [text], model=model, dimensions=50).data[0].embedding)
    
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

# Get the similarity between the input text and the collection
output = moderator.check_duplicate("Buy one get one free Captain Morgan on Thursdays", collection)

# Convert the output to a DataFrame
df = pd.DataFrame(output)

# Sort the DataFrame by similarity 
df = df.sort_values(by="similarity", ascending=False)

# Save the output to a CSV file
df.to_csv("output/output.csv", index=False)


