from flask import Flask, render_template, flash, redirect, request, send_from_directory, url_for, send_file, jsonify, session
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sn
from keras.preprocessing.image import img_to_array, load_img
import mysql.connector, os
import pandas as pd
import time
import re
from urllib.parse import urlparse
import pymysql as mysql

from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
import gradio as gr
import spaces

@spaces.GPU
def dummy_gpu_func():
    pass

import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

USE_SQLITE = False
try:
    mydb = mysql.connect(
        host='localhost',
        user='root',
        password='381920@Mysql',
        port=3306,
        database='Adds',
        charset='utf8mb4'
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT 1")
    mycursor.fetchall()
    print("Successfully connected to MySQL database!")
except Exception as e:
    print(f"Could not connect to MySQL database: {e}. Falling back to SQLite adds.db")
    USE_SQLITE = True

def init_sqlite_db():
    conn = sqlite3.connect('adds.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

if USE_SQLITE:
    init_sqlite_db()

def executionquery(query, values):
    if USE_SQLITE:
        query = query.replace('%s', '?')
        conn = sqlite3.connect('adds.db')
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        conn.close()
    else:
        mycursor.execute(query, values)
        mydb.commit()

def retrivequery1(query, values):
    if USE_SQLITE:
        query = query.replace('%s', '?')
        conn = sqlite3.connect('adds.db')
        cursor = conn.cursor()
        cursor.execute(query, values)
        data = cursor.fetchall()
        conn.close()
        return data
    else:
        mycursor.execute(query, values)
        data = mycursor.fetchall()
        return data

def retrivequery2(query):
    if USE_SQLITE:
        query = query.replace('%s', '?')
        conn = sqlite3.connect('adds.db')
        cursor = conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        return data
    else:
        mycursor.execute(query)
        data = mycursor.fetchall()
        return data


@app.route('/url_checker')
def url_checker():
    return render_template('url_checker.html')

@app.route('/check_url', methods=['POST'])
def check_url():
    url = request.form.get('url', '').strip()
    if not url:
        flash('Please enter a URL', 'danger')
        return redirect(url_for('url_checker'))
    
    # Check if URL has a scheme, add https:// if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Flag HTTP as potentially unsafe
    is_http = url.startswith('http://')
    if is_http:
        return render_template('url_checker.html', result={
            'url': url,
            'is_fraud': True,
            'reason': 'This URL uses HTTP which is not secure. Consider using HTTPS for better security.'
        })
    
    # List of known fraudulent URLs (in a real app, this would be in a database)
    fraudulent_urls = [
        # Phishing URLs
        'secure-login-bank.com',
        'login-paypal-verify.com',
        'microsoft-account-update.net',
        'amazon-payment-verification.com',
        'netflix-billing-update.xyz',
        
        # Scam & Fake Giveaway URLs
        'free-gift-cards-now.com',
        'win-iphone-free.xyz',
        'get-crypto-fast.biz',
        'lottery-winner-claim-now.com',
        'free-bitcoin-generator.net',
        
        # Malware & Suspicious URLs
        'update-your-account-now.net',
        'flash-player-update-urgent.com',
        'antivirus-scan-required.xyz',
        'your-pc-is-infected-now.net',
        'urgent-system-update-required.com'
    ]
    
    # Extract domain from URL for comparison
    domain = urlparse(url).netloc
    
    # Check if domain is in the fraudulent list
    is_fraud = any(fraud_domain in domain for fraud_domain in fraudulent_urls)
    
    # Additional checks (simple heuristics for demonstration)
    suspicious_keywords = ['free', 'win', 'prize', 'congratulations', 'urgent', 'account', 'login', 'bank', 'paypal']
    has_suspicious_keywords = any(keyword in url.lower() for keyword in suspicious_keywords)
    
    # If URL is not in the fraudulent list but has suspicious keywords, mark as suspicious
    if not is_fraud and has_suspicious_keywords:
        return render_template('url_checker.html', result={
            'url': url,
            'is_fraud': True,
            'reason': 'URL contains suspicious keywords commonly used in phishing attempts.'
        })
    
    # If URL is in the fraudulent list
    if is_fraud:
        return render_template('url_checker.html', result={
            'url': url,
            'is_fraud': True,
            'reason': 'This URL is known to be associated with fraudulent activities.'
        })
    
    # If URL is HTTPS and passes all checks
    if url.startswith('https://'):
        return render_template('url_checker.html', result={
            'url': url,
            'is_fraud': False,
            'reason': 'This URL uses HTTPS and appears to be secure.'
    })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')


# @app.route('/login')
# def login():
#     return render_template('login.html')

# @app.route('/register')
# def register():
#     return render_template('register.html')


@app.route('/home')
def home():
    return render_template('home.html')




@app.route('/upload')
def upload():
    return render_template('upload.html')


accuracy_values = {
    'LogisticRegression': 0.77,
    'DecisionTree': 0.88,
    'RandomForest': 0.92,
    'KNN': 0.84,
    'NaiveBayes': 0.75,
    'GradientBoosting': 0.91,
    'LightGBM': 0.92,
    'XGBoost': 0.92,
    'ANN': 0.88,
    'CNN': 0.90,
    'RNN': 0.91,
    'StackingClassifier': 0.92,
    'LSTM': 0.91,
    'GRU': 0.91
}
@app.route('/model', methods=['POST', 'GET'])
def model():
    if request.method == "POST":
        # Get the selected algorithm from the form
        s = request.form['algo']
        
        if s in accuracy_values:
            acc = accuracy_values[s]
            msg = f'The accuracy obtained by the {s.replace("Classifier", " Classifier")} is: {acc:.2f}'
            msg1 = f'The accuracy obtained by the {s.replace("Classifier", " Classifier")} is: {acc * 100:.2f}%'
            return render_template('model.html', msg=msg, msg1=msg1)
        else:
            msg = "Please select a valid algorithm."
            return render_template('model.html', msg=msg)

    return render_template('model.html')





import joblib
from tensorflow.keras.models import load_model

# Load the GRU model and scaler
gru_model = load_model('gru_model.h5')
scaler = joblib.load('minmax_scaler.pkl')

@spaces.GPU
def predict_gpu(model, data):
    return model.predict(data)

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if request.method == 'POST':
        # Extract form data
        try:
            ip = float(request.form['ip'])
            app = float(request.form['app'])
            device = float(request.form['device'])
            os = float(request.form['os'])
            channel = float(request.form['channel'])
            hour = float(request.form['hour'])
            minute = float(request.form['minute'])

            # Prepare input data for prediction
            input_data = np.array([[ip, app, device, os, channel, hour, minute]])

            # Apply scaling
            scaled_data = scaler.transform(input_data)

            # Reshape for GRU input (3D array: [samples, time steps, features])
            scaled_data_reshaped = scaled_data.reshape(1, scaled_data.shape[1], 1)

            # Make prediction
            prediction = (predict_gpu(gru_model, scaled_data_reshaped) > 0.5).astype(int)

            # Map prediction to result message
            if prediction[0] == 1:
                result = " Fraudulent Click"
            else:
                result = " Non-fraudulent Click"

            return render_template('prediction.html', prediction=result)
        except ValueError:
            error = "Invalid input. Please enter valid numeric values for all fields."
            return render_template('prediction.html', error=error)

    return render_template('prediction.html')

# Other routes (e.g., /model) would go here

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['c_password']
        username = request.form['username']  # Get username from form
        
        if password == c_password:
            # Check if the email already exists
            query = "SELECT UPPER(email) FROM users"
            email_data = retrivequery2(query)
            email_data_list = [i[0] for i in email_data]
            
            # Check if the username already exists
            query_username = "SELECT UPPER(username) FROM users"
            username_data = retrivequery2(query_username)
            username_data_list = [i[0] for i in username_data]
            
            if email.upper() not in email_data_list:
                if username.upper() not in username_data_list:
                    # If the email and username are not taken, insert the new user
                    query = "INSERT INTO users (email, password, username) VALUES (%s, %s, %s)"
                    values = (email, password, username)
                    executionquery(query, values)
                    return render_template('login.html', message="Successfully Registered! Please go to login section")
                else:
                    return render_template('register.html', message="This username is already taken!")
            else:
                return render_template('register.html', message="This email ID is already exists!")
        
        return render_template('register.html', message="Confirm password does not match!")
    return render_template('register.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        # Fetch all emails from database and convert them to lowercase
        query = "SELECT LOWER(email) FROM users"
        email_data = retrivequery2(query)
        email_data_list = [i[0] for i in email_data]

        # Check if email exists
        if email.lower() in email_data_list:
            query = "SELECT password FROM users WHERE email = %s"
            values = (email,)
            password_data = retrivequery1(query, values)
            
            # Check password (in real-world cases, you should hash the password and compare)
            if password == password_data[0][0]:
                global user_email
                user_email = email
                session['user_email'] = email
                return redirect("/home")

            # Invalid password
            return render_template('login.html', message="Invalid Password!")
        
        # Invalid email
        return render_template('login.html', message="This email ID does not exist!")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect('/')



# @app.route('/home')
# def home():
#     return render_template('home.html')

# @app.route('/about')
# def about():
#     return render_template('about.html')





# Save the original create_app function to monkeypatch it
original_create_app = gr.routes.App.create_app

def custom_create_app(*args, **kwargs):
    # Call the original create_app to create the FastAPI instance
    fastapi_app = original_create_app(*args, **kwargs)
    # Mount our Flask app to this FastAPI instance at /app
    fastapi_app.mount("/app", WSGIMiddleware(app))
    return fastapi_app

# Apply the monkeypatch
gr.routes.App.create_app = custom_create_app

# Create a dummy Gradio app to satisfy the ZeroGPU spaces runner (with iframe rendering the Flask app)
with gr.Blocks(title="AdClick Fraud Detector") as demo:
    gr.HTML(
        """
        <iframe src="/app/" style="position:fixed; top:0; left:0; bottom:0; right:0; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999999;"></iframe>
        """
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)

    
