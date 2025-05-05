import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings

# Force CPU-only mode before importing TensorFlow-dependent modules
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

# Try to import TensorFlow, but continue if it's not available
try:
    import tensorflow as tf
    print(f"TensorFlow version: {tf.__version__}")

    # Set TensorFlow to use memory growth to avoid OOM errors
    physical_devices = tf.config.list_physical_devices('GPU')
    for device in physical_devices:
        tf.config.experimental.set_memory_growth(device, True)
except ImportError:
    print("TensorFlow is not installed. Some features may not be available.")
    
# Continue with regular imports
from typing import Optional, Union
from flask import (
    Flask, render_template, request, redirect, 
    session, url_for, flash, get_flashed_messages, send_from_directory
)
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import os
import secrets
import string
from model.model_utils import ModelLoader
from werkzeug.utils import secure_filename
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import re  
from PIL import Image
import numpy as np


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
print(f"Using Secret Key: {app.secret_key}")
app.permanent_session_lifetime = timedelta(days=1)

# Email configuration
EMAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('MAIL_PORT', 587))
EMAIL_USERNAME = os.getenv('MAIL_USERNAME', 'your-email@gmail.com') #Enter your mail id
EMAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'your-password') #keep app password server
EMAIL_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'your-email@gmail.com') #Enter your mail id
EMAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'

# Print mail configuration (without showing full password)
print("\nEMAIL CONFIGURATION:")
print(f"EMAIL_SERVER: {EMAIL_SERVER}")
print(f"EMAIL_PORT: {EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {EMAIL_USE_TLS}")
print(f"EMAIL_USERNAME: {EMAIL_USERNAME}")
print(f"EMAIL_PASSWORD: {'*' * 8}")
print(f"EMAIL_SENDER: {EMAIL_SENDER}")

def send_email(to_email, subject, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Create HTML version of the message for better visibility
        if "temporary password" in message.lower():
            # Extract the temporary password from the message
            temp_pw = None
            for line in message.split('\n'):
                if "temporary password:" in line.lower():
                    temp_pw = line.split(":", 1)[1].strip()
                    break
            
            # Create enhanced HTML message with password highlighted
            html_message = f"""
            <html>
            <head>
                <style>
                    .password-box {{
                        background-color: #f0f0f0;
                        border: 2px solid #007bff;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 20px 0;
                        font-size: 18px;
                        text-align: center;
                    }}
                    .password {{
                        font-weight: bold;
                        font-size: 24px;
                        color: #007bff;
                        letter-spacing: 1px;
                    }}
                </style>
            </head>
            <body>
                <h2>Hello from Critter & Flora ID! 🌿🦜</h2>
                <p>Thank you for using our application! 🤗</p>
                
                <div class="password-box">
                    <p>Your temporary password is:</p>
                    <p class="password">{temp_pw}</p>
                </div>
                
                <p>Start exploring nature 🔍 with this password and discover the amazing world around you!</p>
                <p>Don't forget to change your password after logging in.</p>
                <p>Happy exploring!<br>The Critter & Flora Team 🌱</p>
            </body>
            </html>
            """
            
            # Attach HTML version
            msg.attach(MIMEText(html_message, 'html'))
            # Also attach plain text as fallback
            msg.attach(MIMEText(message, 'plain'))
        else:
            # For non-password emails, just use plain text
            msg.attach(MIMEText(message, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT)
        server.ehlo()
        
        # Use TLS if enabled
        if EMAIL_USE_TLS:
            server.starttls()
            server.ehlo()
        
        # Login to server
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, to_email, text)
        
        # Close connection
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

# Clear any existing session when app starts
@app.before_first_request
def clear_session():
    session.clear()

# Flask Development Server Configuration
app.config['ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TESTING'] = False

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'pass11'),
    'database': os.getenv('DB_NAME', 'nature_auth'),
    'port': int(os.getenv('DB_PORT', 3307))
}

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

model_loader = ModelLoader()

# --- Load Species Details ---
SPECIES_DETAILS_PATH = os.path.join('model', 'species_info.json')
all_species_data = {}
try:
    with open(SPECIES_DETAILS_PATH, 'r', encoding='utf-8') as f:
        all_species_data = json.load(f)
    print(f"Successfully loaded species details from {SPECIES_DETAILS_PATH}")
except FileNotFoundError:
    print(f"Warning: Species details file not found at {SPECIES_DETAILS_PATH}")
except json.JSONDecodeError:
    print(f"Warning: Error decoding JSON from {SPECIES_DETAILS_PATH}")

# --- Load Dog Breed Details ---
DOG_BREED_INFO_PATH = os.path.join('model', 'dog_breed_info.json')
dog_breed_info = {}
try:
    with open(DOG_BREED_INFO_PATH, 'r', encoding='utf-8') as f:
        dog_breed_info = json.load(f)
    print(f"Successfully loaded dog breed details from {DOG_BREED_INFO_PATH}")
except FileNotFoundError:
    print(f"Warning: Dog breed info file not found at {DOG_BREED_INFO_PATH}")
except json.JSONDecodeError:
    print(f"Warning: Error decoding JSON from {DOG_BREED_INFO_PATH}")

# --- Load Bird Details ---
BIRD_INFO_PATH = os.path.join('model', 'bird_info_converted.json')
bird_info = {}
try:
    with open(BIRD_INFO_PATH, 'r', encoding='utf-8') as f:
        bird_info = json.load(f)
    print(f"Successfully loaded bird details from {BIRD_INFO_PATH}")
except FileNotFoundError:
    print(f"Warning: Bird info file not found at {BIRD_INFO_PATH}")
except json.JSONDecodeError:
    print(f"Warning: Error decoding JSON from {BIRD_INFO_PATH}")

# --- Load Flower Details ---
FLOWER_INFO_PATH = os.path.join('model', 'flower_info_varied.json')
flower_info = {}
try:
    with open(FLOWER_INFO_PATH, 'r', encoding='utf-8') as f:
        flower_info = json.load(f)
    print(f"Successfully loaded flower details from {FLOWER_INFO_PATH}")
    print(f"Found {len(flower_info)} flower entries")
except FileNotFoundError:
    print(f"Warning: Flower details file not found at {FLOWER_INFO_PATH}")
except json.JSONDecodeError:
    print(f"Warning: Error decoding JSON from {FLOWER_INFO_PATH}")
except Exception as e:
    print(f"Warning: Error loading flower info: {str(e)}")

# --- Load Insect Details ---
INSECT_INFO_PATH = os.path.join('model', 'insect_info.json')
INSECT_LABELS_PATH = os.path.join('model', 'insect_labels.json')
insect_info = {}
insect_labels = {}

try:
    with open(INSECT_INFO_PATH, 'r', encoding='utf-8') as f:
        insect_info = json.load(f)
    print(f"Successfully loaded insect details from {INSECT_INFO_PATH}")
    print(f"Found {len(insect_info)} insect entries")
except FileNotFoundError:
    print(f"Warning: Insect details file not found at {INSECT_INFO_PATH}")
except json.JSONDecodeError:
    print(f"Warning: Error decoding JSON from {INSECT_INFO_PATH}")
except Exception as e:
    print(f"Warning: Error loading insect info: {str(e)}")

try:
    with open(INSECT_LABELS_PATH, 'r', encoding='utf-8') as f:
        insect_labels = json.load(f)
    print(f"Successfully loaded insect labels from {INSECT_LABELS_PATH}")
    print(f"Found {len(insect_labels)} insect label entries")
except FileNotFoundError:
    print(f"Warning: Insect labels file not found at {INSECT_LABELS_PATH}")
except json.JSONDecodeError:
    print(f"Warning: Error decoding JSON from {INSECT_LABELS_PATH}")
except Exception as e:
    print(f"Warning: Error loading insect labels: {str(e)}")

def get_db_connection():
    try:
        print(f"Attempting to connect to database with config: {DB_CONFIG}")
        conn = mysql.connector.connect(**DB_CONFIG)
        print("Database connection successful")
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        flash('Database connection error. Please try again later.', 'error')
        return None

def generate_temp_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def is_password_valid(password):
    """
    Validate if the password meets the following criteria:
    - 8 characters minimum
    - One lowercase character
    - One uppercase character
    - One number
    - One special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

# Welcome email function
def send_welcome_email(email, username):
    """
    Send a welcome email to newly registered users
    """
    try:
        subject = "Welcome to Critter & Flora! 🌿"
        message = f"""
Hello {username}! 🌟

Welcome to Critter & Flora ID! 🦜🌸

Thank you for creating an account with us. We're excited to have you join our community of nature enthusiasts!

With Critter & Flora ID, you can:
🔍 Identify birds, flowers, plants, dogs, cats and insects
🌱 Learn about different species in nature
📸 Upload images for instant identification

Start exploring the natural world around you!

Happy exploring!
The Critter & Flora Team(Batch-20) 🌿
"""
        
        return send_email(email, subject, message)
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
        return False

# Function to check if user exists
def check_user_exists(email=None, username=None):
    """
    Check if a user with the given email or username exists in the database.
    Returns True if exists, False otherwise.
    """
    if not email and not username:
        return False
        
    conn = get_db_connection()
    if not conn:
        print("Database connection failed during user check")
        return False
        
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE "
        params = []
        
        if email and username:
            query += "email = %s OR username = %s"
            params = [email, username]
        elif email:
            query += "email = %s"
            params = [email]
        elif username:
            query += "username = %s"
            params = [username]
            
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return bool(result)
    except Error as e:
        print(f"Database error during user check: {e}")
        if conn:
            conn.close()
        return False

@app.route('/')
def home():
    print("Home route accessed")
    session.clear()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    print(f"Login route accessed. Method: {request.method}")
    if request.method == 'GET':
        session.clear()
        return render_template('login.html')
        
    if request.method == 'POST':
        login_id = request.form.get('login_id')  # This can be either email or username
        password = request.form.get('password')
        print(f"Login attempt for: {login_id}")
        
        # First check if the user exists
        user_exists = check_user_exists(email=login_id) or check_user_exists(username=login_id)
        if not user_exists:
            print(f"User not found for login_id: {login_id}")
            flash('Invalid credentials', 'error')
            return render_template('login.html')
            
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                # Check if login is with email or username
                cursor.execute("SELECT * FROM users WHERE email = %s OR username = %s", (login_id, login_id))
                user = cursor.fetchone()
                
                if user and check_password_hash(user['password'], password):
                    print("Login successful")
                    session.clear()  # Clear any existing session
                    session.permanent = True
                    session['user'] = {'id': user.get('id'), 'email': user['email'], 'username': user.get('username')}
                    return redirect(url_for('button'))
                else:
                    print("Invalid credentials")
                    flash('Invalid credentials', 'error')
            except Error as e:
                print(f"Database error during login: {e}")
                flash('Authentication error', 'error')
            finally:
                cursor.close()
                conn.close()
        else:
            print("Database connection failed")
            flash('Database connection error', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    print(f"Register route accessed. Method: {request.method}")
    if 'user' in session:
        print("User already logged in, redirecting to button")
        return redirect(url_for('button'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        print(f"Registration attempt for email: {email}, username: {username}")

        if not email or not username or not password or password != confirm_password:
            print("Invalid registration details")
            flash('Invalid registration details', 'error')
            return redirect(url_for('register'))

        # Validate password meets requirements
        is_valid, message = is_password_valid(password)
        if not is_valid:
            print(f"Password validation failed: {message}")
            flash(message, 'error')
            return render_template('register.html', registration_success=False)
        # Check if email or username already exists using the new function
        if check_user_exists(email=email):
            print(f"Email already exists: {email}")
            flash('Registration failed: Email already exists', 'error')
            return render_template('register.html', registration_success=False)
            
        if check_user_exists(username=username):
            print(f"Username already exists: {username}")
            flash('Registration failed: Username already exists', 'error')
            return render_template('register.html', registration_success=False)

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (email, username, password) VALUES (%s, %s, %s)", 
                             (email, username, hashed_pw))
                conn.commit()
                print("Registration successful")
                
                # Send welcome email
                if send_welcome_email(email, username):
                    print(f"Welcome email sent to {email}")
                else:
                    print(f"Failed to send welcome email to {email}")
                
                return render_template('register.html', registration_success=True)
            except Error as e:
                print(f"Registration failed: {e}")
                flash('Registration failed: Database error', 'error')
            finally:
                cursor.close()
                conn.close()
        else:
            print("Database connection failed during registration")
            flash('Database error', 'error')
    return render_template('register.html', registration_success=False)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if 'user' in session:
        return redirect(url_for('button'))
        
    if request.method == 'POST':
        login_id = request.form.get('login_id')  # This can be email or username
        
        # Check if user exists first
        user_exists = check_user_exists(email=login_id) or check_user_exists(username=login_id)
        if not user_exists:
            print(f"User not found for login_id: {login_id}")
            flash('User not found', 'error')
            return render_template('forgot.html')
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE email = %s OR username = %s", (login_id, login_id))
                user = cursor.fetchone()
                if user:
                    temp_pw = generate_temp_password()
                    cursor.execute("UPDATE users SET password = %s WHERE email = %s OR username = %s", 
                                 (generate_password_hash(temp_pw, method='pbkdf2:sha256'), user['email'], user.get('username')))
                    conn.commit()
                    
                    # Send email with temporary password
                    try:
                        email = user['email']
                        print(f"Attempting to send email to {email} with SMTP server {EMAIL_SERVER}:{EMAIL_PORT}")
                        print(f"Using username: {EMAIL_USERNAME}")
                        
                        
                        message = f"""
Hello from Critter & Flora ID! 🌿🦜

Thank you for using our application! 🤗

Your temporary password: {temp_pw}

Start exploring nature 🔍 with this password and discover the amazing world around you!

Don't forget to change your password after logging in.

Happy exploring!
The Critter & Flora Team 🌱
"""
                        
                        if send_email(email, "Your Password Reset - Critter & Flora ID", message):
                            flash('Check your email for your new password! 📧 Ready to explore nature? 🌿', 'success')
                        else:
                            # Fall back to displaying the password if email fails
                            flash(f'Here is your temporary password: {temp_pw} - Change after login 🔐', 'success')
                    except Exception as mail_error:
                        print(f"Error sending email: {str(mail_error)}")
                        print(f"Error type: {type(mail_error).__name__}")
                        # Fall back to displaying the password if email fails
                        flash(f'Here is your temporary password: {temp_pw} - Change after login 🔐', 'success')
                    
                    return redirect(url_for('login'))
                else:
                    flash('User not found', 'error')
            except Exception as e:
                flash('An error occurred while processing your request', 'error')
                print(f'Database error: {str(e)}')
            finally:
                cursor.close()
                conn.close()
        else:
            flash('Database error', 'error')
    return render_template('forgot.html')

@app.route('/button')
def button():
    print("Button route accessed")
    if 'user' not in session:
        print("User not logged in, redirecting to login")
        flash('Please login to access this page', 'error')
        return redirect(url_for('login'))
    return render_template('button.html')

@app.route('/index')
def index():
    if 'user' not in session:
        print("User not logged in, redirecting to login")
        flash('Please login to access this page', 'error')
        return redirect(url_for('login'))
        
    category = request.args.get('category', '')

    # Retrieve predictions and image from session
    predictions = session.pop('predictions', [])
    uploaded_image_filename = session.pop('uploaded_image_path', None)
    
    descriptions = {
        'birds': "Capture📷. Upload⬆️. Discover the bird behind the feathers🦜",
        'dogs': " Upload your pups photo to discover the breed and story behind the wa🐕",
        'cats': "Upload your cats photo to learn its breed and traits😼",
        'flowers': "Upload a flower and reveal its name and origin🌸",
        'insects': "Curious bug🤔 Drop a photo to uncover its identity🐞",
        'plants': "Snap📷. Upload⬆️. Identify your plant in seconds🌱"
    }
    
    page_description = descriptions.get(category, "Image Identifier 📸")
    
    # Initialize uploaded_image_url
    uploaded_image_url = None
    if uploaded_image_filename:
        uploaded_image_url = url_for('uploaded_image', filename=uploaded_image_filename)
    
    print(f"Rendering index template with category: {category}")
    return render_template('index.html', 
                          category=category,
                          page_description=page_description,
                          predictions=predictions, 
                          uploaded_image_url=uploaded_image_url)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user' not in session:
        flash('Please login to use this feature', 'error')
        return redirect(url_for('login'))
        
    if 'image' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(request.referrer or url_for('button'))
        
    file = request.files['image']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.referrer or url_for('button'))
        
    # Get category from referrer URL
    referrer = request.referrer or ''
    category = 'general'
    if 'category=' in referrer:
        category = referrer.split('category=')[1].split('&')[0]
        
    print(f"📸 Upload request for category: {category}")
        
    if file and allowed_file(file.filename):
        try:
            # Save the uploaded file to the uploads folder
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            print(f"💾 File saved to {filepath}")
            
            # Validate the file is a valid image before prediction
            try:
                img = Image.open(filepath)
                img.verify()  # Make sure it's a valid image
                print(f"✅ Image verified as valid: {filepath}")
                img.close()
                
                # Reopen the image to check dimensions
                img = Image.open(filepath)
                width, height = img.size
                print(f"📏 Image dimensions: {width}x{height} pixels")
                
                # Warn if image is very small
                if width < 100 or height < 100:
                    print(f"⚠️ Warning: Image is very small ({width}x{height})")
                    flash('Warning: The uploaded image is very small. This may affect prediction accuracy.', 'warning')
                
                # Warn if image is extremely large
                if width > 4000 or height > 4000:
                    print(f"⚠️ Warning: Image is very large ({width}x{height})")
                    flash('Warning: The uploaded image is very large. This may slow down processing.', 'warning')
                
            except Exception as img_err:
                print(f"❌ Error verifying image: {str(img_err)}")
                flash(f'Invalid image file: {str(img_err)}', 'error')
                return redirect(request.referrer or url_for('button'))
            
            # Additional debug for specific categories
            if category.lower() == 'dogs':
                print(f"🐕 DOG PREDICTION REQUESTED - Special debug mode enabled")
                # Check if the dog model is loaded properly
                if model_loader.dog_model is None:
                    print(f"⚠️ Warning: Specialized dog model is not loaded in model_loader")
                    print(f"Will attempt to use general model as fallback if available")
                    if model_loader.model is None and model_loader.general_model is None:
                        print(f"❌ Error: Neither specialized dog model nor general model is available")
                        flash('The dog breed classifier is not available at this time.', 'error')
                        return redirect(request.referrer or url_for('button'))
                    else:
                        print(f"✅ General model is available as fallback")
                        flash('Using general image classifier for dog breed detection', 'info')
                else:
                    print(f"✅ Specialized dog model is loaded with input shape: {model_loader.dog_input_shape}")
                    print(f"✅ Dog labels count: {len(model_loader.dog_labels)}")
                
                print(f"✅ Dog info entries: {len(model_loader.dog_info)}")
            
            elif category.lower() == 'plants':
                print(f"🌿 PLANT PREDICTION REQUESTED - Special debug mode enabled")
                # Check if the plant model is loaded properly
                if model_loader.plant_model is None:
                    print(f"❌ Error: Plant model is not loaded in model_loader")
                    flash('The plant classifier is not available at this time.', 'error')
                    return redirect(request.referrer or url_for('button'))
                print(f"✅ Plant model is loaded with input shape: {model_loader.plant_input_shape}")
                print(f"✅ Plant labels count: {len(model_loader.plant_labels)}")
                print(f"✅ Plant info entries: {len(model_loader.plant_info)}")
            
            # Use model_loader to predict the contents of the image
            print(f"🔄 Starting prediction for category: {category}")
            predictions = model_loader.predict(filepath, category)
            print(f"✅ Prediction complete: {len(predictions)} results returned")
            
            # Additional debugging for predictions
            if predictions:
                for i, pred in enumerate(predictions):
                    confidence = pred.get('confidence', pred.get('confidence_internal', 0))
                    print(f"📊 Prediction {i+1}: {pred.get('label', 'Unknown')} - {confidence:.2f}%")
            
            # Check if predictions contain error messages
            if predictions and any(k in predictions[0] for k in ['error', 'description']):
                # Extract error details
                error_msg = predictions[0].get('error', 'Unknown error')
                description = predictions[0].get('description', '')
                
                if error_msg != 'Unknown error':
                    print(f"❌ Image analysis error: {error_msg}")
                    flash(f'Image analysis error: {error_msg}', 'error')
                elif description:
                    # Use description as a more user-friendly message
                    print(f"⚠️ Analysis note: {description}")
                    flash(f'Analysis note: {description}', 'warning')
                
                # If confidence is zero, this is likely an error result
                if predictions[0].get('confidence', 1.0) == 0.0:
                    print(f"⚠️ Prediction returned with zero confidence: {predictions[0].get('label', 'Unknown')}")
                    if category.lower() == 'birds':
                        flash('No bird could be identified in this image. Please try another image of a bird.', 'warning')
                    elif category.lower() == 'dogs':
                        flash('No dog breed could be identified in this image. Please try another image of a dog.', 'warning')
                    elif category.lower() == 'plants':
                        flash('No plant species could be identified in this image. Please try another image of a plant.', 'warning')
                
            # Save predictions and image path in session
            session['predictions'] = predictions
            session['uploaded_image_path'] = filename
            
            # Redirect to the appropriate index page
            return redirect(url_for('index', category=category))
            
        except Exception as e:
            print(f"❌ Error during upload/prediction: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Error processing image: {str(e)}', 'error')
            return redirect(request.referrer or url_for('button'))
    else:
        extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'tif', 'heic', 'heif', 'svg'}
        flash(f'Invalid file type. Allowed image types: {", ".join(extensions)}', 'error')
        return redirect(request.referrer or url_for('button'))

@app.route('/uploads/<filename>')
def uploaded_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    print("Logout route accessed")
    session.clear()
    print("Session cleared, redirecting to login")
    return redirect(url_for('login'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'tif', 'heic', 'heif', 'svg'}

@app.route('/debug-db', methods=['GET'])
def debug_database():
    """
    Debug route to check database connection and users table
    Only accessible in development mode
    """
    if not app.config['DEBUG']:
        return "Debug mode not enabled", 403
    
    output = []
    output.append("<h1>Database Debug Information</h1>")
    
    # Test connection
    conn = get_db_connection()
    if conn:
        output.append("<p style='color:green'>✅ Database connection successful</p>")
        
        try:
            # Get table structure
            cursor = conn.cursor()
            cursor.execute("DESCRIBE users")
            columns = cursor.fetchall()
            
            output.append("<h2>Table Structure:</h2>")
            output.append("<table border='1'><tr><th>Field</th><th>Type</th><th>Null</th><th>Key</th><th>Default</th><th>Extra</th></tr>")
            for column in columns:
                output.append(f"<tr><td>{column[0]}</td><td>{column[1]}</td><td>{column[2]}</td><td>{column[3]}</td><td>{column[4]}</td><td>{column[5]}</td></tr>")
            output.append("</table>")
            
            # List users
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            
            output.append(f"<h2>Users ({len(users)}):</h2>")
            if users:
                output.append("<table border='1'><tr>")
                for field in columns:
                    output.append(f"<th>{field[0]}</th>")
                output.append("</tr>")
                
                for user in users:
                    output.append("<tr>")
                    for value in user:
                        # Don't show actual passwords
                        if str(value).startswith('pbkdf2:sha256'):
                            output.append("<td>[HASHED PASSWORD]</td>")
                        else:
                            output.append(f"<td>{value}</td>")
                    output.append("</tr>")
                output.append("</table>")
            else:
                output.append("<p>No users found in database</p>")
                
            cursor.close()
        except Error as e:
            output.append(f"<p style='color:red'>Error querying database: {str(e)}</p>")
        finally:
            conn.close()
    else:
        output.append("<p style='color:red'>❌ Database connection failed</p>")
    
    return "<br>".join(output)

@app.route('/clear-users', methods=['GET'])
def clear_users():
    """
    Debug route to clear all users from the database
    Only accessible in development mode
    """
    if not app.config['DEBUG']:
        return "Debug mode not enabled", 403
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users")
            conn.commit()
            result = f"All users deleted. Affected rows: {cursor.rowcount}"
            cursor.close()
            conn.close()
            return result
        except Error as e:
            return f"Error clearing users: {str(e)}"
    else:
        return "Database connection failed"

@app.route('/test-dog-classifier', methods=['GET', 'POST'])
def test_dog_classifier():
    """
    Test endpoint for troubleshooting the dog breed classifier
    """
    if 'user' not in session:
        flash('Please login to access this page', 'error')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No file uploaded', 400
            
        file = request.files['image']
        if file.filename == '':
            return 'No selected file', 400
            
        if file and allowed_file(file.filename):
            # Save the uploaded file to the uploads folder
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Debug info
            debug_info = []
            debug_info.append(f"File saved to: {filepath}")
            
            # Verify the image
            try:
                from PIL import Image
                img = Image.open(filepath)
                img_info = f"Image size: {img.width}x{img.height}, format: {img.format}"
                debug_info.append(img_info)
            except Exception as img_err:
                debug_info.append(f"Error opening image: {str(img_err)}")
                return "<br>".join(debug_info), 400
            
            # Test if dog model is loaded
            if model_loader.dog_model is None:
                debug_info.append("ERROR: Dog model is not loaded!")
                return "<br>".join(debug_info), 500
                
            # Test if dog labels are loaded
            if not model_loader.dog_labels:
                debug_info.append("ERROR: Dog labels are not loaded!")
                return "<br>".join(debug_info), 500
                
            # Test if dog info is loaded
            if not model_loader.dog_info:
                debug_info.append("WARNING: Dog info dictionary is empty!")
                
            debug_info.append(f"Dog model input shape: {model_loader.dog_input_shape}")
            debug_info.append(f"Number of dog labels: {len(model_loader.dog_labels)}")
            debug_info.append(f"Number of dog info entries: {len(model_loader.dog_info)}")
            
            # Try preprocessing
            try:
                # Test preprocessing step
                img_array = model_loader._preprocess_keras(filepath, model_loader.dog_input_shape)
                debug_info.append(f"Preprocessing successful. Array shape: {img_array.shape}")
            except Exception as preprocess_err:
                debug_info.append(f"ERROR during preprocessing: {str(preprocess_err)}")
                return "<br>".join(debug_info), 500
                
            # Try model prediction
            try:
                # Run prediction with the dog model directly
                predictions = model_loader.dog_model.predict(img_array, verbose=0)
                debug_info.append(f"Prediction successful. Output shape: {predictions.shape}")
                
                # Get top 3 predictions
                top_indices = np.argsort(-predictions[0])[:3]
                debug_info.append("Top 3 predictions:")
                
                for i, idx in enumerate(top_indices):
                    if idx < len(model_loader.dog_labels):
                        label = model_loader.dog_labels[idx]
                        confidence = float(predictions[0][idx])
                        debug_info.append(f"  {i+1}. {label} - {confidence:.4f} ({confidence*100:.2f}%)")
                
                # Get the top breed
                if top_indices[0] < len(model_loader.dog_labels):
                    top_breed = model_loader.dog_labels[top_indices[0]]
                    debug_info.append(f"Top breed: {top_breed}")
                    
                    # Check if breed info is available
                    if top_breed in model_loader.dog_info:
                        debug_info.append(f"Breed info found for: {top_breed}")
                    else:
                        debug_info.append(f"No direct breed info match for: {top_breed}")
                        
                        # Try standard case match
                        standard_breed_name = ' '.join(word.capitalize() for word in top_breed.split())
                        if standard_breed_name in model_loader.dog_info:
                            debug_info.append(f"Standard case match found: {standard_breed_name}")
                        else:
                            debug_info.append("No standard case match found")
                            
                            # Try case-insensitive match
                            found = False
                            for info_breed in model_loader.dog_info.keys():
                                if top_breed.lower() == info_breed.lower():
                                    debug_info.append(f"Case-insensitive match found: {info_breed}")
                                    found = True
                                    break
                            
                            if not found:
                                debug_info.append("No case-insensitive match found")
                
                # Try the full predict_dog method
                try:
                    result = model_loader.predict_dog(filepath)
                    debug_info.append("<hr>")
                    debug_info.append("<h3>Complete prediction result:</h3>")
                    if result:
                        for key, value in result.items():
                            debug_info.append(f"<b>{key}</b>: {value}")
                    else:
                        debug_info.append("predict_dog returned None")
                except Exception as full_err:
                    debug_info.append(f"Error in full predict_dog: {str(full_err)}")
                
            except Exception as pred_err:
                debug_info.append(f"ERROR during prediction: {str(pred_err)}")
                return "<br>".join(debug_info), 500
                
            return "<br>".join(debug_info)
    
    # GET request - show a simple form
    return '''
    <!doctype html>
    <title>Test Dog Classifier</title>
    <h1>Test Dog Classifier</h1>
    <p>Use this form to test the dog breed classifier directly:</p>
    <form method=post enctype=multipart/form-data>
      <input type=file name=image accept="image/*">
      <input type=submit value=Test>
    </form>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True, threaded=True)
