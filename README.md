# Critter and Flora - Species Recognition System

## Project Overview

Critter and Flora is an advanced species identification and information system that uses image recognition technology to identify birds, insects, plants, and animals from user-uploaded images. The system provides detailed information about identified species, including scientific name, habitat, diet, lifespan, physical characteristics, and interesting facts.

## Features

- **Multi-Species Recognition**: Upload an image of a bird, insect, plant, or animal and get an accurate identification using machine learning models
- **Comprehensive Species Database**: Access detailed information for hundreds of species
- **Educational Content**: Learn about habitats, behaviors, and interesting facts
- **User-Friendly Interface**: Intuitive design for easy navigation and use
- **Responsive Design**: Works across desktop and mobile devices

## Technical Architecture

The application is built using:
- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python, Flask
- **Database**: MySQL
- **ML Models**: TensorFlow for species recognition
- **Authentication**: Secure user login and registration system

## Data Sources

The species information database includes comprehensive details compiled from:
- Scientific journals and research
- Field guides and manuals
- Expert-verified descriptions and measurements
- High-quality images for reference and identification

## Installation and Setup

### Prerequisites
- Python 3.8+
- MySQL
- TensorFlow 2.x
- Flask
- Required Python packages (listed in requirements.txt)

### Installation Steps

1. Clone the repository:
```
git clone https://github.com/Lokesh071/Critter-and-Flora.git
cd Critter-and-Flora
```

2. Set up a virtual environment (recommended):
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```
pip install -r requirements.txt
```

4. Create a .env file using the .env.template file
   - Update the database configuration
   - Add your email credentials for password reset functionality

5. Configure the database:
   - Create a MySQL database named nature_auth
   - Run the database setup script

6. Start the application:
```
python app.py
```

7. Access the application in your browser at `http://localhost:5000`

## Usage

1. **Register/Login**: Create an account or log in to an existing account
2. **Upload Image**: Upload an image for identification
3. **View Results**: Review the identification results and detailed species information
4. **Explore Database**: Browse the species database by category, habitat, or other filters

## Project Structure

```
Critter-and-Flora/
├── app.py                 # Main Flask application file
├── requirements.txt       # Required Python packages
├── model/                 # ML models and data files
│   ├── model_utils.py     # Model utility functions
│   ├── class_names.txt    # Species class names
│   └── *_info.json        # Detailed species information
├── static/                # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── assets/
├── templates/             # HTML templates
└── uploads/               # User-uploaded images for processing
```

## License

This project is licensed under the MIT License.

## Acknowledgements

- Species data sourced from reputable databases
- The TensorFlow and machine learning communities for providing tools and resources for image recognition

## OUTPUT SCREENS:
  ![Screenshot 2025-05-05 144117](https://github.com/user-attachments/assets/90bc5e0b-dc31-4c5e-abce-68d1651d195e)
  
  ![image](https://github.com/user-attachments/assets/365e928f-379e-4396-a6db-4c87266cf9a8)
  
  ![image](https://github.com/user-attachments/assets/419aced1-b392-484c-b349-82b2c0e7eee7)
  
  ![image](https://github.com/user-attachments/assets/b9810b99-c131-4aac-b1fa-20fb31a95bba)
  
  ![image](https://github.com/user-attachments/assets/6e945866-2d12-402c-9123-b720a34e92e1)
  
  ![image](https://github.com/user-attachments/assets/e631d2e9-b262-4054-8dde-708942adfe1d)
  
  ![image](https://github.com/user-attachments/assets/3f053212-3ca8-411a-a3b1-dc10cbedcdb1)
  
  ![image](https://github.com/user-attachments/assets/d8063b63-b7b8-4d49-a935-f48963a56bc3)
  
  ![image](https://github.com/user-attachments/assets/7037cf05-dddd-47c4-a643-fc5c199bc704)
  
  ![image](https://github.com/user-attachments/assets/068fa5b8-2787-4c71-9359-c868b979d73a)
  
  ![image](https://github.com/user-attachments/assets/b81fb5fd-a406-401e-b19c-11ead4bbd779)
  
  ![image](https://github.com/user-attachments/assets/854385c8-3812-4e13-ab96-022cbf542dda)
  
  ![image](https://github.com/user-attachments/assets/44794ed3-c4bf-46da-b3b5-79fb753e8263)








  

  








