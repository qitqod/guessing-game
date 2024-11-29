import json
from openai import OpenAI
import streamlit as st
import toml

# Initialize the OpenAI client with the API key from the secrets file
api_key = st.secrets["openai"]["api_key"]
client = OpenAI(api_key=api_key)

# fetch function that will get the requested data from the gpt-3.5-turbo model and provide it in JSON format
def fetch_capitals():
    """
    Fetches details about two random capitals using the OpenAI API.
    """
    prompt = """
    Provide a JSON object with the following details about two random capitals, 1 target capital, and 1 capital to be guessed:
    - Name of the target_capital + its country.
    - Name of the guess_capital + name of its country (you are allowed to mention the name of the capital and its country in this field)
    - 4 fun facts about the guess_capital where you do not mention the guess_capital's name nor its country's name in this manner:
        - 1. flight time between them in one sentence WITHOUT mentioning the guess capital's name nor its country. 
        - 2. How many people live in it in one sentence WITHOUT mentioning the guess capital's name nor its country. 
        - 3. When it was founded WITHOUT mentioning the guess capital's name nor its country.
        - 4. Famous dish of the guess_capital WITHOUT mentioning the guess capital's name nor its country. 
    - Distance between the two capitals in kilometers

    Example:
    {
        "target_capital": {"name": "Tunis", "country": "Tunisia"},
        "guess_capital": {"name": "Rome", "country": "Italy", "fun_facts": ["it would take you x hours to fly there.", "20 million people live there.", "it was founded in 1580.", "It is famous for its couscous."]},
        "distance_km": 5837
    }
    """
    try:
        # Create a chat completion request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a fact and geography expert and provide the requested data accurately and you don't favor popular capitals over others. The probability is even across all capitals. You do not reveal the name nor the country of the guess capital in the fun facts; you only reveal them in their appropriate field, which is guess_capital name and guess_capital country."},
                {"role": "user", "content": prompt},
            ],
            temperature=  0.7  # for some randomness
        )
        # Extract and parse the response content
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except json.JSONDecodeError:
        return "We are experiencing a server issue, please try again."
    except Exception as e:
        return f"An error occurred: {e}"


# Function that evaluates user input and compares it using GPT-3.5
def evaluate_guess(city_details, user_guess):
    """
    Evaluate the user's guess in the context of the city game.

    Args:
        city_details (dict): Dictionary containing city details and distance information.
        user_guess (str): The city guessed by the user.

    Returns:
        dict: Evaluation result including correctness, capital status, and distance.
    """
    # Construct the prompt for the OpenAI model
    prompt = f"""
Reference City: {city_details['target_capital']['name']}
Correct City: {city_details['guess_capital']['name']}
User Guess: {user_guess}

Evaluate the user's guess following these instructions:
- Normalize input for comparison: Treat New York the same as new york the same as NEW YORK etc. Uppercase and lowercase dont matter. 
- Does the guess match the target_capital? 
- Is the guess a capital of a country?
- Is the guess an existing recognized city? 
- If the city does not exist, return null.
- If the city is a valid city (existing), then calculate the distance in kilometers from the target_city to the city the user guessed.
- Give your comment on how well the player has been guessing, taking into account these criteria and your short feedback.
- Provide the output in this JSON format:
{{
    "guess_correct": <true/false>,
    "is_capital": <true/false>,
    "valid_city": <true/false>,
    "distance_to_guess": <distance or null>
    "comment": "<string>"
}}
- Use 'null' for missing or inapplicable values for 'distance_to_guess'.
- The 'comment' field should always be a string, even if empty (e.g., "").
- All boolean values must be explicitly true or false.
- When checking if a city is a capital, refer to its official status globally. And also, the capitalization of the letters do not play a role, for example, berlin is a capital, as well as Berlin. That holds true for cities as well. And if the given input provided can either be a capital, non-capital city, an object, a name etc then check if it hold true in this order.
- If the user sends and input which is not a valid string (empty input, digits, emojis etc) - tell them that it is not correct and they said something funny and count it as a wrong guess"
"""

    try:
        # Use the chat completion API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a geography and distance expert that evaluates accurately if the user guess is a real city,  a capital, and how far is it from the  capital."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2  # Set temperature for deterministic responses
        )
        # Extract and parse the response content
        content = response.choices[0].message.content.strip()
        result = json.loads(content)  # Parse JSON-like string into a Python dictionary

        # Additional check: If the city is not valid, set the distance to None
        if not result.get("valid_city", False):
            result["distance_to_guess"] = None
        return result

    except json.JSONDecodeError:
        return {"error": "Failed to parse the response. Please try again."}
    except Exception as e:
        return {"error": str(e)}

def update_game_data():
    if st.session_state.round_complete and st.session_state.guess_history:
        st.session_state.game_data.append({
            "Round": st.session_state.round_number - 1,
            "Guesses": st.session_state.guesses_this_round,
            "Non-Capitals": st.session_state.non_capitals_this_round,
            "Distance Off": st.session_state.distance_off_this_round,
            "Guess History": st.session_state.guess_history,
            "Target Capital": st.session_state.current_round["guess_capital"]["name"],
            "Target Country": st.session_state.current_round["guess_capital"]["country"],
            "Round Won": any(guess["Correct"] for guess in st.session_state.guess_history),
        })


        
def display_hint():
    # if st.session_state.hint_index < len(st.session_state.hints):
        st.info(f"Hint: {st.session_state.hints[st.session_state.hint_index]}")
        st.session_state.hint_index += 1
    # else:
    #     target = st.session_state.current_round["guess_capital"]
    #     st.error(f"Round lost! The correct answer was {target['name']}, {target['country']}. Good luck next time!")
    #     st.session_state.round_complete = True
