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
        #output_p = profanity.contains_profanity(text)
        output_p = False

        # Return the flagged status
        return output_o.flagged or output_p
    
    def check_duplication_by_embeddings(self, text, collection):
        # Get the embedding for the input text
        text_embedding = self._get_embedding(text)

        sim_list = []
        for i, item in enumerate(collection):
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
    
    def check_duplicate_time_logic(self, deal_in, collection):
        # Create a dictionary to store the details of the comparisons
        details = {}

        # Get the days of the week
        days = deal_in['deal_details']['days_active']

        # Get the start and end times
        start_time = deal_in['deal_details']['start_time']
        end_time = deal_in['deal_details']['end_time']

        # Convert the start and end times to integers   
        try:
            start_time = int(start_time.replace(":", ""))
        except:
            start_time = 0

        try:
            end_time = int(end_time.replace(":", ""))
        except:
            end_time = 240000

        # Get the deals that are active on the same days
        deals_f1 = [item for item in collection if set(item['deal_details']['days_active']).intersection(set(days))]

        details['deals_f1'] = deals_f1

        # Get the deals that are active at the same time, while doing a try and except to handle the open and close times, and convert them to integers
        deals_f2 = []
        for deal in deals_f1:
            try:
                deal_start_time = int(deal['deal_details']['start_time'].replace(":", ""))
            except:
                deal_start_time = 0

            try:
                deal_end_time = int(deal['deal_details']['end_time'].replace(":", ""))
            except:
                deal_end_time = 240000

            # Check if the deal is active at the same time
            # print(f"Deal start time: {deal_start_time}, Deal end time: {deal_end_time}, Input start time: {start_time}, Input end time: {end_time}")
            if (start_time == deal_start_time) and (end_time == deal_end_time):
                deals_f2.append(deal)

        details['deals_f2'] = deals_f2

        # Create a list of establishments in text
        deals_establishment_collection = [str(item['establishment']['name']).lower().replace("'","").replace("bar","").replace("tavern","").replace("the","").replace("restaurant","").replace(" ","").strip() for item in deals_f2]
        estab_sim_list = self.check_duplication_by_embeddings(str(deal_in['establishment']['name']).lower().replace("'","").replace("bar","").replace("tavern","").replace("the","").replace("restaurant","").replace(" ","").strip(), deals_establishment_collection)

        details['estab_sim_list'] = estab_sim_list

        # Filter deals that are at the same establishment
        deals_f3 = []
        for i, estab in enumerate(estab_sim_list):
            if estab['similarity'] > 0.6:
                deals_f3.append(deals_f2[i])
        
        details['deals_f3'] = deals_f3

        # Create a list of descriptions in text
        deals_description_collection = [str(item['description']).lower() for item in deals_f3]
        desc_sim_list = self.check_duplication_by_embeddings(str(deal_in['description']).lower(), deals_description_collection)

        details['desc_sim_list'] = desc_sim_list

        # Filter deals that have the same description
        deals_f4 = []
        for i, desc in enumerate(desc_sim_list):
            if desc['similarity'] > 0.4:
                deals_f4.append(deals_f3[i])


        details['deals_f4'] = deals_f4
            
        sim_list = deals_f4
        return sim_list, details
        
    def _get_embedding(self, text, model="text-embedding-3-small"):
        text = text.replace("\n", " ")
        return (self.client.embeddings.create(input = [text], model=model).data[0].embedding)
    
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


if __name__ == "__main__":
    # Example usage:
    moderator = Moderator()


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

    collection_tester = [
        {"establishment": "Joes", "days_active": ["Thursday"], "start_time": "18:00:00", "end_time": "22:00:00", "description": "$3 off whiskey"},
        {"establishment": "Midway on High", "days_active": ["Friday", "Saturday"], "start_time": "Open", "end_time": "Close", "description": "$2 off rum cocktail's"},
        {"establishment": "Anchor", "days_active": ["Monday"], "start_time": "17:00:00", "end_time": "20:00:00", "description": "Half-price apps"},
        {"establishment": "Lunas", "days_active": ["Wednesday", "Thursday"], "start_time": "Open", "end_time": "11:00:00", "description": "Buy one get one espresso drinks"},
        {"establishment": "The Dockside Tavern", "days_active": ["Sunday"], "start_time": "12:00:00", "end_time": "16:00:00", "description": "25% off platters of seafood"},
        {"establishment": "Brew Brothers Bar", "days_active": ["Tuesday", "Wednesday"], "start_time": "15:00:00", "end_time": "18:00:00", "description": "$1 off beers crafted"},
        {"establishment": "Golden Spoon Tavern", "days_active": ["Monday", "Tuesday", "Wednesday"], "start_time": "Open", "end_time": "Close", "description": "10% discount on total bill"},
        {"establishment": "Vine & Dine Bistro", "days_active": ["Thursday", "Friday"], "start_time": "19:00:00", "end_time": "21:00:00", "description": "Wine tasting included with any entree"},
        {"establishment": "Night Owl Lounge", "days_active": ["Friday", "Saturday"], "start_time": "22:00:00", "end_time": "02:00:00", "description": "No cover charge"},
        {"establishment": "Sunset Grill & Bar", "days_active": ["Sunday"], "start_time": "Open", "end_time": "Close", "description": "Children dine for free"},
        {"establishment": "The Greenhouse Cafe", "days_active": ["Monday", "Tuesday"], "start_time": "17:00:00", "end_time": "19:00:00", "description": "Two vegan dishes for the price of one"},
        {"establishment": "Harbor View Pub", "days_active": ["Wednesday", "Thursday", "Friday"], "start_time": "16:00:00", "end_time": "18:00:00", "description": "Happy Hour on oysters"},
        {"establishment": "Pit Stop Bar & Grill", "days_active": ["Saturday", "Sunday"], "start_time": "Open", "end_time": "15:00:00", "description": "$5 for Bloody Marys"},
        {"establishment": "Mystic Pizza", "days_active": ["Tuesday"], "start_time": "Open", "end_time": "Close", "description": "20% discount on all pizzas"},
        {"establishment": "Library Lounge", "days_active": ["Wednesday"], "start_time": "20:00:00", "end_time": "23:00:00", "description": "Buy 2 craft cocktails, get 1 free"},
        {"establishment": "The Speak Easy", "days_active": ["Thursday", "Friday", "Saturday"], "start_time": "21:00:00", "end_time": "01:00:00", "description": "Free appetizer with premium cocktail purchase"},
        {"establishment": "Cafe Del Mar", "days_active": ["Monday"], "start_time": "Open", "end_time": "Close", "description": "Free refill on coffee"},
        {"establishment": "Rooftop Lounge", "days_active": ["Sunday"], "start_time": "17:00:00", "end_time": "20:00:00", "description": "Specials on signature cocktails during sunset"},
        {"establishment": "Alley", "days_active": ["Friday"], "start_time": "Open", "end_time": "Close", "description": "Bowling at half price with shoe rental"},
        {"establishment": "Ocean's Edge Restaurant", "days_active": ["Saturday", "Sunday"], "start_time": "18:00:00", "end_time": "22:00:00", "description": "Dessert on the house with any main course"},
    ]

    expected_outputs = [
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

    # Run the check_duplicate_time_logic function for each deal in the collection_tester and put them into a pd dataframe with in-depth testing results and problems that arose
    outputs = []

    for i, deal in enumerate(collection_tester): 
        output, details = moderator.check_duplicate_time_logic(deal, collection)
        if len(output) == 0:
            output = None
        else:
            output = output[0]
        outputs.append({'deal_in': deal, 'output': output, 'result': output == expected_outputs[i], 'details': details})
        print(f"Deal {i+1} of {len(collection_tester)}")

    # Compare outputs to expected_outputs
    total_correct = 0
    for i, output in enumerate(outputs):
        if output['result']:
            total_correct += 1
        else:
            print(f"Deal {i+1} failed")

    print(f"Total correct: {total_correct} of {len(outputs)}")
    print(f"Accuracy: {total_correct/len(outputs)}")

    # Create a dataframe from the outputs
    df = pd.DataFrame(outputs)
    df.to_csv(f"outputs_{total_correct}_{len(outputs)}.csv")
    df.to_json(f"outputs_{total_correct}_{len(outputs)}.json", orient="records", lines=False, indent=2)

