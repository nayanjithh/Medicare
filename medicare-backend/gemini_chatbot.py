import os
import json
from google import genai
from google.genai import types
from pymongo import MongoClient

uri = <INSER_YOUR_MONGODB_URI>
client = MongoClient(uri)
db = client["medicaredb"]
collection = db["Patients"]

memory = ""

def search(name: str, age: int):
    global memory
    result = collection.find_one({"name": name.lower(), "age": age}, {"_id": 0})
    if result:
        lines = ""
        lines += f"🩺 Patient ID: {result.get('patient_id', '')}"
        lines += f"\nName: {result.get('name', '')}"
        lines += f"\nAge: {result.get('age', '')}"
        lines += f"\nDate: {result.get('date', '')}"
        lines += f"\nSource: {result.get('source', '')}"

        symptoms = result.get("symptoms", [])
        if symptoms:
            lines += "\n\n Symptoms:"
            for s in symptoms:
                lines += f"\n  - {s}"

        diagnosis = result.get("diagnosis", "")
        if diagnosis:
            lines += f"\n\nDiagnosis: \n  - {diagnosis}"

        medicines = result.get("medicines recommended", [])
        if medicines:
            lines += "\n\nMedicines Recommended:"
            for m in medicines:
                lines += f"\n  - {m}"

        recommendations = result.get("doctor recommendations", [])
        if recommendations:
            lines += "\n\nDoctor Recommendations:"
            for r in recommendations:
                lines += f"\n  - {r}"

        improvements = result.get("improvements", [])
        if improvements:
            lines += "\n\nImprovements:"
            for i in improvements:
                lines += f"\n  - {i}"

        memory += lines

        return lines
    else:
        return "No patient found with the given details."

def generate(user_input: str):
    global memory
    client = genai.Client(
        api_key= <INSERT_YOUR_GEMEINI_API_KEY>
    )

    model = "gemini-flash-latest"
    
    memory += f"user: {user_input}\n"

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=memory)],
        )
    ]

    tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="search",
                    description="Used for searching a user's medical details",
                    parameters=genai.types.Schema(
                        type=genai.types.Type.OBJECT,
                        properties={
                            "name": genai.types.Schema(type=genai.types.Type.STRING),
                            "age": genai.types.Schema(type=genai.types.Type.NUMBER),
                        },
                        required=["name", "age"]
                    ),
                )
            ]
        )
    ]

    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
        ],
        tools=tools,
        system_instruction=[
            types.Part.from_text(
                text="""You are a helpful nurse chatbot for the Medicare website so response in sentence without special characters.
                You provide empathetic medical guidance, and can search patient results using the search(name, age) function when necessary."""
            ),
        ],
    )

    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.function_calls:
            fn_call = chunk.function_calls[0]
            if fn_call.name == "search":
                args = fn_call.args
                result = search(args.get("name"), args.get("age"))
                response_text += f"\n🔍 Patient Data:\n{result}\n"
        elif chunk.text:
            response_text += chunk.text
    memory += f"assistant: {response_text}\n"

    return response_text
