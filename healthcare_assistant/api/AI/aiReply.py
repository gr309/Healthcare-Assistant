import threading, json, re, os
from dotenv import load_dotenv
from groq import Groq


from ..Models.chat import Conversation  
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")



class HealthCareAsistantClass:
    client = None
    error_message = ""
    status = 200
    conversation = None
    ai_reply = "working"
    def __init__(self):
        try: 
            print('working')


            if not GROQ_API_KEY:
                self.error_message =  "AI service is not configured yet."
                self.status = 400
                return 

            self.client = Groq(api_key=GROQ_API_KEY)
         

        except Exception:
            self.error_message = "Ai Server Error"
            self.check_apistatus = 400

    def check_conv(self, conv_id):
        try:
            self.conversation = Conversation.objects.get(id=conv_id)

        except:
            self.status = 400
            self.error_message = "conversation is not found"
    def handle_title(self, query):
        if self.conversation.title != "New Conversation":
            return

        prompt = f"""
            You are an AI that generates a short conversation title.

            Based on the user's initial query, generate a concise title.

            Return ONLY valid JSON:
            {{
            "title": "..."
            }}

            Rules:
            - Maximum 6 words
            - Focus on main health issue
            - No punctuation at the end
            - No extra explanation

            User query:
            "{query}"

            Do not return anything except valid JSON.
        """

        chat_completion = self.client.chat.completions.create(
            messages = [
                {"role": "user", "content": prompt}
                ],
            model = "openai/gpt-oss-20b",
            temperature=0.3
        )
        response =  chat_completion.choices[0].message.content

        try:
            data = json.loads(response)
            title = data.get('title', 'Untitled')
        except:
            title = 'Untitled'


        self.conversation.title = title
        self.conversation.save()

    def handle_main_ai(self, query):
        prompt = f"""
            You are a healthcare assistant AI.

            Context (important medical memory from previous conversation):
            {self.conversation.analization}

            User question:
            "{query}"

            Your tasks:
            1. Answer the question safely and clearly
            2. Use context if relevant
            3. Extract important medical keywords from the user input + context

            Return ONLY valid JSON:

            {{
            "answer": "...",
            "confidence": "low | medium | high",
            "suggestion": "...",
            "emergency": true | false,
            "keywords": ["...", "..."]
            }}

            Rules:
            - "emergency" = true ONLY for serious symptoms (chest pain, breathing issues, unconsciousness, heavy bleeding, etc.)
            - "keywords" must include only meaningful medical info:
            (symptoms, duration, severity, conditions)
            - DO NOT include greetings or filler words in keywords
            - Keep answer simple and safe
            - If unsure → set confidence = "low"

            Do not return anything except valid JSON.
        """
        chat_completion = self.client.chat.completions.create(
            messages = [
                {"role": "user", "content": prompt}
                ],
            model = "meta-llama/llama-4-scout-17b-16e-instruct",
        )

        response = chat_completion.choices[0].message.content



        try:
            json_str = re.search(r'\{.*\}', response, re.DOTALL).group()
            data = json.loads(json_str)
        except:

            return {
                "answer": "Sorry, I couldn't process that properly.",
                "confidence": "low",
                "suggestion": "Please try again.",
                "emergency": False,
            }

        answer = data.get("answer", "")
        confidence = data.get("confidence", "low")
        suggestion = data.get("suggestion", "")
        emergency = data.get("emergency", False)
        keywords = data.get("keywords", [])


        analizatin = self.conversation.analization
        if isinstance(analizatin, str):
            try:
                analizatin = json.loads(analizatin)
            except:
                analizatin = []

        if not isinstance(analizatin, list):
            analizatin = []

        if not isinstance(keywords, list):
            keywords = []

        analizatin.append(keywords)

        self.conversation.analization = json.dumps(analizatin)
        self.conversation.save()



        return  {
            "answer": answer,
            "confidence":confidence,
            "suggestion": suggestion,
            "emergency": emergency,
        }

    def get_reply(self, query, conv_id):
        self.check_conv(conv_id)

        if self.status == 400:
            return self.error_message
        self.handle_title(query)

        reply = self.handle_main_ai(query)
        print(reply)

        return reply



HealthCareAsistant = HealthCareAsistantClass()


