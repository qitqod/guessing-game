import streamlit as st
import pandas as pd
from assets.utils import fetch_capitals, evaluate_guess, update_game_data, display_hint

# --- PAGE CONFIGURATION ---
# Configure the Streamlit page with title, icon, and layout
st.set_page_config(page_title="Guess the Capital", page_icon="assets/favicon.png")

# --- INITIALIZE SESSION STATE ---
# Initialize session state variables with default values to track game progress and statistics
def initialize_session_state():
    defaults = {
        "game_data": [],  # Stores data for all completed rounds
        "total_guesses": 0,  # Total guesses across all rounds
        "total_non_capitals": 0,  # Total non-capitals guessed
        "total_distance_off": 0,  # Cumulative distance off from correct answers
        "start_playing_clicked": False,  # Indicates if the game has started
        "round_number": 1,  # Current round number
        "current_round": None,  # Data for the ongoing round
        "guesses_this_round": 0,  # Guesses made in the current round
        "non_capitals_this_round": 0,  # Non-capitals guessed in the current round
        "distance_off_this_round": 0,  # Distance off in the current round
        "guess_history": [],  # Stores guesses and outcomes for the current round
        "hints": [],  # Hints for the current round
        "hint_index": 0,  # Tracks which hint to show next
        "round_complete": False,  # Indicates if the round is complete
        "play_again_triggered": False,  # Tracks if "play again" was clicked
        "round_index": 0,  # Tracks round order programmatically
        "average_guesses_previous": 0,  # Avg guesses from previous rounds
        "average_guesses_current": 0,  # Current avg guesses
        "delta_guesses": 0,  # Change in avg guesses
        "average_far_off": 0,  # Avg distance off from target
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# --- START NEW ROUND ---
# Prepares a new round by resetting relevant state variables and fetching new data
def start_new_round():
    with st.spinner("Preparing a new round..."):
        update_game_data()  # Save completed round data
        st.session_state.current_round = fetch_capitals()  # Fetch new round details
        st.session_state.guesses_this_round = 0
        st.session_state.non_capitals_this_round = 0
        st.session_state.distance_off_this_round = 0
        st.session_state.guess_history = []
        st.session_state.round_complete = False
        st.session_state.hint_index = 0
        st.session_state.play_again_triggered = False
        st.session_state.round_index += 1  # Increment round index for tracking
        target = st.session_state.current_round["guess_capital"]
        st.session_state.hints = target["fun_facts"] + [f"It is in {target['country']}"]

# --- START PLAYING BUTTON LOGIC ---
# Starts the game when the "Start Playing" button is clicked
def start_playing():
    with st.spinner("Starting the game..."):
        st.session_state.start_playing_clicked = True
        start_new_round()

# --- EVALUATE GUESS ---
# Evaluates the player's guess, updates stats, and provides feedback
def evaluate_guess_and_provide_feedback(guess):
    with st.spinner("Evaluating your guess..."):
        evaluation = evaluate_guess(st.session_state.current_round, guess.upper())
        st.session_state.guesses_this_round += 1
        st.session_state.total_guesses += 1

        # Handle invalid city or incorrect guess
        if not evaluation["is_capital"] or not evaluation["valid_city"]:
            st.error(f"'{guess}' is not a capital.")
            st.session_state.non_capitals_this_round += 1
            st.session_state.total_non_capitals += 1
            st.session_state.total_distance_off += 0
        else:
            # Valid city but incorrect guess
            if not evaluation["guess_correct"]:
                distance = evaluation.get("distance_to_guess", "N/A")
                if isinstance(distance, (int, float)):
                    st.session_state.distance_off_this_round += distance
                    st.session_state.total_distance_off += distance
                    st.warning(f"You are {distance} km off.")
                else:
                    st.warning("Distance could not be calculated.")
            else:
                # Correct guess
                st.session_state.guess_history.append({
                    "Guess": guess,
                    "Correct": evaluation["guess_correct"],
                    "Distance": evaluation.get("distance_to_guess", "N/A"),
                    "Capital": evaluation["is_capital"],
                    "Comment": evaluation["comment"]

                })
                update_realtime_stats()
                st.success("Congrats! That's correct.")
                st.session_state.round_complete = True
                st.rerun()
                st.balloons()


        # Add guess details to guess history
        st.session_state.guess_history.append({
            "Guess": guess,
            "Correct": evaluation["guess_correct"],
            "Distance": evaluation.get("distance_to_guess", "N/A"),
            "Capital": evaluation["is_capital"]
        })

        # Update stats and provide next hint or end round
        update_realtime_stats()
        if not evaluation["guess_correct"]:
            display_hint()

        # Move to the next round if completed
        if st.session_state.round_complete:
            st.session_state.round_number += 1

# --- UPDATE REAL-TIME STATS ---
# Updates session statistics dynamically during the game
def update_realtime_stats():
    st.session_state.average_guesses_previous = st.session_state.average_guesses_current
    if st.session_state.game_data:
        st.session_state.average_guesses_current = pd.DataFrame(st.session_state.game_data)["Guesses"].mean()
    else:
        st.session_state.average_guesses_current = st.session_state.guesses_this_round
    st.session_state.delta_guesses = st.session_state.average_guesses_current - st.session_state.average_guesses_previous

    if st.session_state.game_data:
        st.session_state.average_far_off = pd.DataFrame(st.session_state.game_data)["Distance Off"].mean()
    else:
        st.session_state.average_far_off = st.session_state.distance_off_this_round

# --- DISPLAY TRACKING VARIABLES ---
# Displays key game statistics for the current session
def display_tracking_variables():
    st.write("### Tracking Variables")
    st.write({
        "Total Guesses": st.session_state.total_guesses,
        "Total Non-Capitals": st.session_state.total_non_capitals,
        "Rounds Played": st.session_state.round_number - 1,
        "Total Distance Off (All Rounds)": st.session_state.total_distance_off,
        "Distance Off This Round": st.session_state.distance_off_this_round,
        "Average Guesses (Current)": st.session_state.average_guesses_current,
        "Average Guesses (Previous)": st.session_state.average_guesses_previous,
        "Delta Guesses": st.session_state.delta_guesses,
        "Average Distance Off": st.session_state.average_far_off,
    })

# --- USER INTERFACE ---
# Defines the main game interface
if not st.session_state.start_playing_clicked:
    st.title("Welcome to Guess the Capital!")
    st.write("Try to guess the capital x km away from the city we give you!")
    st.button("Start Playing", on_click=start_playing)
else:
    if st.session_state.round_complete:
        st.subheader("Round Summary")
        st.write(f"Guesses This Round: {st.session_state.guesses_this_round}")
        st.write(f"Non-Capitals Named: {st.session_state.non_capitals_this_round}")
        st.write(f"Distance Off This Round: {st.session_state.distance_off_this_round}")
        st.write("Guess History:")
        st.write(pd.DataFrame(st.session_state.guess_history))
        st.write(st.session_state.guess_history)
        #st.write(f"Comment: {st.session_state.guess_history["Comment"]}")
        if st.button("Play Again"):
            start_new_round()
            st.rerun()
    else:
        current_data = st.session_state.current_round
        reference_city = current_data["target_capital"]["name"]
        reference_country = current_data["target_capital"]["country"]
        distance = current_data["distance_km"]
        st.write(f"### Round {st.session_state.round_number}: Guess which capital is {distance} km away from {reference_city}, {reference_country}.")
        user_guess = st.text_input("Enter your guess:").strip()

        if st.button("Submit"):
            if user_guess and not user_guess.isalpha():
                st.error("Invalid guess. Please enter a valid word.")
            elif not user_guess:
                st.warning("Guess cannot be empty.")
            else:
                evaluate_guess_and_provide_feedback(user_guess)
        else:
            st.warning("Please enter a valid guess.")

    display_tracking_variables()

# --- DISPLAY CURRENT ROUND DATA ---
# Shows data for the ongoing round if the game has started
if st.session_state.start_playing_clicked and st.session_state.current_round:
    st.write("### Current Round Data")
    st.json(st.session_state.current_round)
