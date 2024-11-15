import streamlit as st
import pymongo
import bcrypt
import pandas as pd
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast

# MongoDB connection for login system
client = pymongo.MongoClient("mongodb://localhost:27017/")
db_auth = client['streamlit_auth']  # Database for authentication
users_collection = db_auth['users']  # Collection for users

# MongoDB connection for novel recommendation system
client = MongoClient('mongodb://localhost:27017/')
db = client['novel_db']
collection = db['novels']

# Load novels from MongoDB into a DataFrame
novels = pd.DataFrame(list(collection.find()))

# Password hashing
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Password verification
def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# Register a new user
def register_user(username, password):
    if users_collection.find_one({"username": username}):
        st.warning("Username already exists! Please choose a different one.")
    else:
        hashed_password = hash_password(password)
        users_collection.insert_one({"username": username, "password": hashed_password})
        st.success("User registered successfully! You can now login.")

# Login an existing user
def login_user(username, password):
    user = users_collection.find_one({"username": username})
    if user:
        if verify_password(password, user['password']):
            st.session_state['username'] = username  # Create session
            st.success(f"Welcome, {username}! You have successfully logged in.")
            return True
        else:
            st.error("Incorrect password. Please try again.")
            return False
    else:
        st.error("Username not found. Please register first.")
        return False

# Logout user
def logout():
    st.session_state.clear()  # Clear session state to log out
    st.success("You have successfully logged out.")

# Function to get novel recommendations
def convert_genres_to_string(genres):
    if isinstance(genres, list):
        return ', '.join(genres)
    try:
        return ', '.join(ast.literal_eval(genres))
    except (ValueError, SyntaxError):
        return genres

novels['genres'] = novels['genres'].apply(convert_genres_to_string)

# Function to get recommendations
def get_recommendations(selected_genre, n_recommendations=5):
    novels['genres'] = novels['genres'].fillna('')
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(novels['genres'])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    idx = novels[novels['genres'].str.contains(selected_genre, case=False)].index

    if len(idx) == 0:
        return pd.DataFrame(columns=['title', 'author', 'genres', 'ratings'])

    sim_scores = list(enumerate(cosine_sim[idx[0]]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:n_recommendations + 1]
    novel_indices = [i[0] for i in sim_scores]

    return novels.iloc[novel_indices]

# Main App Interface
def main():
    if 'username' not in st.session_state:
        # If user is not logged in, show login and register page
        st.sidebar.title("Login or Register")
        option = st.sidebar.selectbox("Choose an option", ["Login", "Register"])

        # Login form
        if option == "Login":
            st.header("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login"):
                if username and password:
                    if login_user(username, password):
                        st.session_state['logged_in'] = True
                else:
                    st.warning("Please fill in both the username and password fields.")

        # Registration form
        elif option == "Register":
            st.header("Register")
            username = st.text_input("Username", key="register_username")
            password = st.text_input("Password", type="password", key="register_password")
            password_confirm = st.text_input("Confirm Password", type="password", key="register_password_confirm")

            if st.button("Register"):
                if username and password and password_confirm:
                    if password == password_confirm:
                        register_user(username, password)
                    else:
                        st.warning("Passwords do not match. Please try again.")
                else:
                    st.warning("Please fill in all fields.")
    else:
        # If logged in, show the dashboard and logout option
        st.sidebar.title(f"Welcome, {st.session_state['username']}!")
        if st.sidebar.button("Logout"):
            logout()  # Log the user out by clearing session state

        # Show the recommendation dashboard
        st.sidebar.header("📚 Novel Recommendation System")
        st.sidebar.write("Welcome! This app helps you find novels based on genre preferences.")
        st.sidebar.write("Explore a collection of diverse novels and get personalized recommendations!")

        st.title("📖 Novel Recommendation System")
        st.markdown("#### Discover Your Next Great Read!")
        st.markdown("**Instructions:** Select a genre and the number of recommendations to find your next novel!")

        # User input for genre
        genre = st.selectbox("**Select a Genre**", novels['genres'].unique())

        # Number of recommendations
        n_recommendations = st.slider("**Number of Recommendations**", 1, 10, 5)

        # Show recommendations when the user clicks the button
        if st.button("🔍 Recommend Novels"):
            recommendations = get_recommendations(genre, n_recommendations)
            if not recommendations.empty:
                st.success("Here are your recommended novels:")
                for index, row in recommendations.iterrows():
                    st.markdown(f"### {row['title']} by {row['author']}")
                    st.markdown(f"**Genres:** {row['genres']}")
                    st.markdown(f"**Pages:** {row['pages']}")
                    st.markdown(f"**Ratings:** {row['ratings']}")
                    st.write("---")  # Divider
            else:
                st.warning("No recommendations found for the selected genre.")

if __name__ == '__main__':
    main()
