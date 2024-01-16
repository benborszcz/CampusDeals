import openai
import config

# Set the API Params for OpenAI
openai.api_key = config.OPENAI_API_KEY

class Agent:
    def __init__(self, name: str, description: str, system_message = "", addtional_messages = None,
                 model = "gpt-3.5-turbo-1106", temperature = 0.7, max_tokens = 1000, top_p = 1, frequency_penalty = 0.0,
                 presence_penalty = 0.0):
        self.name = name
        self.description = description
        self.system_message = system_message
        self.addtional_messages = addtional_messages
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.history = []

    def complete_task(self, task: str, persist = False):
        response = self.generate(task, persist)
        response_message = response["choices"][0]["message"]["content"]
        return response_message

    def generate(self, message: str, persist):
        messages = [{"role": "system", "content": self.system_message}]
        print("Agent Name: " + self.name)
        print("System Message: ")
        print(self.system_message)
        print("User Message: ")
        print(message)
        if self.addtional_messages is not None:
            messages.extend(self.addtional_messages)
        if self.history is not None:
            messages.extend(self.history)
        messages.extend([{"role": "user", "content": message}])
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            response_format = { "type": "json_object" },
        )
        if persist:
            self.history.append({"role": "user", "content": message})
            self.history.append({"role": "assistant", "content": response["choices"][0]["message"]["content"]})
        return response
    