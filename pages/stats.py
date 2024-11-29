import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- PAGE CONFIGURATION ---
# Configure Streamlit page with title, icon, and wide layout
st.set_page_config(page_title="Game Stats", page_icon="📊", layout="wide")

# --- STATS PAGE FUNCTION ---
def stats_page():
    st.title("📊 Game Stats")

    # Check if game data exists
    if "game_data" in st.session_state and st.session_state.game_data:
        # Convert game data to a DataFrame
        games_data = pd.DataFrame(st.session_state.game_data)

        # Clean and rename columns for clarity
        games_data.rename(columns={
            "Round": "Round Number",
            "Guesses": "Nb of Guesses",
            "Non-Capitals": "Non-Capitals Named",
            "Distance Off": "Distance Off (km)",
            "Guess History": "Guess History",
        }, inplace=True)
        games_data.drop(columns=["Target Country"], inplace=True, errors="ignore")

        # Create "Round Description" as "Reference City - Target Capital"
        if "Reference City" in games_data.columns:
            games_data["Round Description"] = games_data["Reference City"] + " - " + games_data["Target Capital"]
        else:
            games_data["Round Description"] = games_data["Target Capital"]

        # Format "Guess History" as a readable string
        games_data["Guess History"] = games_data["Guess History"].apply(
            lambda x: ", ".join([entry["Guess"] for entry in x])
        )

        # Align indices with round numbers
        games_data.index = games_data.index + 1

        # Calculate statistics for metrics
        avg_guesses_current = games_data["Nb of Guesses"].mean()
        delta_guesses = avg_guesses_current - st.session_state.average_guesses_previous

        avg_distance_current = games_data["Distance Off (km)"].mean()
        delta_distance = avg_distance_current - st.session_state.average_far_off

        total_non_capitals_current = games_data["Non-Capitals Named"].sum()
        delta_non_capitals = total_non_capitals_current - st.session_state.total_non_capitals

        # Update session state
        st.session_state.average_guesses_previous = avg_guesses_current
        st.session_state.average_far_off = avg_distance_current
        st.session_state.total_non_capitals = total_non_capitals_current

        # --- SUMMARY METRICS ---

        # --- CHARTS ---

        st.title("##How did you do? Let's review your stats.")

        #Bar Chart 1: number of guesses per round
        st.bar_chart(
            data=games_data,
            x="Round Description",
            y="Nb of Guesses",
            x_label="Cities",
            y_label="Number of Guesses",
            use_container_width=False
        )

        #Bar Chart 2: distance off per round
        st.bar_chart(
            data=games_data,
            x="Round Description",
            y="Distance Off (km)",
            x_label="Cities",
            y_label="Distance off in km / round",
            use_container_width=False
        )

         # --- QUALITY METRICS ---

        # Display metrics for average guesses, distance off, and total non-capitals
        st.write("###Did you improve?")
        col1, col2, col3 = st.columns(3)
        col1.metric("Avg Nb of Guesses", f"{avg_guesses_current:.2f}", f"{delta_guesses:+.2f}", delta_color="inverse" if delta_guesses > 0 else "normal")
        col2.metric("Avg Distance Off (km)", f"{avg_distance_current:.2f}", f"{delta_distance:+.2f}", delta_color="inverse" if delta_distance > 0 else "normal")
        col3.metric("Total Non-Capitals", total_non_capitals_current, f"{delta_non_capitals:+}", delta_color="inverse" if delta_non_capitals > 0 else "normal")
      
        # --- DETAILED DATA ---

        # Display detailed round data table
        st.write("### Detailed Round Data")
        st.dataframe(
            games_data.drop(columns=["Round Number", "Round Description"], axis=1, errors="ignore"),
            use_container_width=True,
        )
    else:
        # Display message if no game data is available
        st.warning("No game data available yet! Play a round to start tracking your stats.")

# Call the stats page function
stats_page()
