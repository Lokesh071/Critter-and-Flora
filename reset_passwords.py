import mysql.connector
from werkzeug.security import generate_password_hash
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'yourpassword'),
    'database': os.getenv('DB_NAME', 'yourdatabase'),
    'port': int(os.getenv('DB_PORT', 3307))
}

def reset_passwords():
    try:
        # Connect to the database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Generate a temporary password hash
        temp_password = 'ChangeMe123!'
        password_hash = generate_password_hash(temp_password, method='pbkdf2:sha256')
        
        # Update all user passwords
        cursor.execute("UPDATE users SET password = %s", (password_hash,))
        conn.commit()
        
        # Get count of updated users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        print(f"Successfully reset {user_count} user passwords to 'ChangeMe123!'")
        print("Please inform users to change their passwords upon next login.")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    reset_passwords() 
