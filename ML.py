import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Streamlit app title
st.title("Startup Profit Prediction App")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Data Preview")
    st.write(df.head())

    # Display basic info
    st.write("### Data Summary")
    st.write(df.describe())
    st.write("Missing Values:")
    st.write(df.isnull().sum())

    # Visualization
    st.write("### Data Visualization")
    fig, ax = plt.subplots()
    sns.heatmap(df.corr(), annot=True, cmap='coolwarm', ax=ax)
    st.pyplot(fig)

    # Select features and target
    features = ['R&D Spend', 'Administration', 'Marketing Spend']
    target = 'Profit'

    X = df[features]
    y = df[target]

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Scale data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Model selection
    model_choice = st.selectbox("Select Model", ["Linear Regression", "Decision Tree", "Random Forest"])

    if model_choice == "Linear Regression":
        model = LinearRegression()
    elif model_choice == "Decision Tree":
        model = DecisionTreeRegressor()
    else:
        model = RandomForestRegressor(n_estimators=100)

    # Train the model
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_test_scaled)

    # Model performance
    st.write("### Model Performance")
    st.write(f"MAE: {mean_absolute_error(y_test, y_pred)}")
    st.write(f"MSE: {mean_squared_error(y_test, y_pred)}")
    st.write(f"R² Score: {r2_score(y_test, y_pred)}")

    # Predict on new input
    st.write("### Make a Prediction")
    input_data = []
    for feature in features:
        value = st.number_input(f"Enter {feature}", value=float(df[feature].mean()))
        input_data.append(value)

    if st.button("Predict Profit"):
        input_data = np.array(input_data).reshape(1, -1)
        input_scaled = scaler.transform(input_data)
        prediction = model.predict(input_scaled)[0]
        st.write(f"### Predicted Profit: ${prediction:,.2f}")
