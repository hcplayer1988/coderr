Coderr - Freelance Developer Platform Backend
A Django REST Framework backend for a freelance developer platform connecting businesses with IT professionals. Features include user profiles, service offers, order management, reviews, and platform statistics.
📑 Table of Contents

Features
Tech Stack
Project Structure
Installation & Setup

Prerequisites
1. Clone the Repository
2. Create Virtual Environment
3. Install Dependencies
4. Environment Configuration
5. Database Setup
6. Create Superuser (Optional)
7. Start Development Server


Configuration

Important Settings
CORS Configuration
Media Files Configuration
REST Framework Settings


API Endpoints

Authentication
Profiles
Offers
Orders
Reviews
General


API Usage Examples

Registration
Login
Create Offer
Create Order


Special Features & Considerations

1. User Types
2. Offer Package Structure
3. Order Status Workflow
4. Review System
5. Permissions System
6. Media Files & Image Uploads
7. CORS Configuration
8. Frontend Integration


Admin Panel
Development

Testing
Seeding Database


Troubleshooting

Issue: CORS errors in browser
Issue: 401 Unauthorized on endpoints
Issue: Image upload fails
Issue: Reviews return 400 "already reviewed"


Production Deployment
License


Features

Dual User System: Separate customer and business user types
User Profiles: Customizable profiles with images, phone numbers, location
Service Offers: Create offers with Basic/Standard/Premium packages
Order Management: Full order lifecycle from creation to completion
Review System: 5-star rating system with one review per business user
Platform Statistics: Public endpoint for platform metrics
Image Uploads: Support for profile pictures and offer images
Advanced Filtering: Filter offers by price, delivery time, search terms
Token Authentication: Secure API access with DRF tokens
CORS Enabled: Ready for frontend integration

Tech Stack

Django 6.0.1
Django REST Framework
Token Authentication
SQLite Database (easily switchable to PostgreSQL/MySQL)
django-cors-headers for CORS support
django-filter for advanced filtering
python-decouple for environment variables

Project Structure
coderr/
├── core/                          # Main project settings
│   ├── settings.py
│   └── urls.py
├── auth_app/                      # Authentication
│   ├── api/
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── models.py                  # CustomUser model
│   └── admin.py
├── profile_app/                   # User profiles
│   ├── api/
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── permissions.py
│   │   └── urls.py
│   ├── models.py                  # Profile model
│   └── tests/
├── offer_app/                     # Service offers
│   ├── api/
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── permissions.py
│   │   └── urls.py
│   ├── models.py                  # Offer, OfferDetail models
│   └── tests/
├── order_app/                     # Order management
│   ├── api/
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── permissions.py
│   │   └── urls.py
│   ├── models.py                  # Order model
│   └── tests/
├── reviews_app/                   # Review system
│   ├── api/
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── permissions.py
│   │   └── urls.py
│   ├── models.py                  # Review model
│   └── tests/
├── general_app/                   # Platform statistics
│   ├── api/
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   └── tests/
├── media/                         # Uploaded files
│   ├── profile_images/
│   └── offer_images/
├── db.sqlite3                     # SQLite database
├── manage.py
├── requirements.txt
└── .env                          # Environment variables
Installation & Setup
Prerequisites

Python 3.10 or higher
pip (Python package manager)
Virtual environment (recommended)

1. Clone the Repository
bashgit clone <repository-url>
cd coderr
2. Create Virtual Environment
bash# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
3. Install Dependencies
bashpip install -r requirements.txt
Requirements:
txtDjango==6.0.1
djangorestframework==3.15.2
django-cors-headers==4.6.0
django-filter==24.3
python-decouple==3.8
Pillow==11.0.0
4. Environment Configuration
Create a .env file in the project root:
env# .env
DJANGO_SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
IMPORTANT: Never commit the .env file to version control!
5. Database Setup
bash# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
6. Create Superuser (Optional)
bashpython manage.py createsuperuser
Follow the prompts to create an admin account.
7. Start Development Server
bashpython manage.py runserver
The API will be available at: http://127.0.0.1:8000/
Configuration
Important Settings
CORS Configuration (core/settings.py)
CRITICAL: Update CORS_ALLOWED_ORIGINS with your frontend URL:
pythonCORS_ALLOWED_ORIGINS = [ 
    'http://127.0.0.1:5500',     # Update with your frontend URL
    'http://localhost:5500',     # Update with your frontend URL
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_CREDENTIALS = True
Media Files Configuration
pythonMEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
Ensure media/ directory exists or Django will create it automatically.
REST Framework Settings
pythonREST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/day',
        'user': '10000/day',
    },
}
API Endpoints
Authentication
MethodEndpointDescriptionAuth RequiredPOST/api/registration/Register new userNoPOST/api/login/Login and get tokenNo
Profiles
MethodEndpointDescriptionAuth RequiredGET/api/profile/{id}/Get user profileYesPATCH/api/profile/{id}/Update own profileYes (Owner)GET/api/profiles/business/List all business profilesYesGET/api/profiles/customer/List all customer profilesYes
Offers
MethodEndpointDescriptionAuth RequiredGET/api/offers/List all offers (with filters)NoPOST/api/offers/Create new offerYes (Business)GET/api/offers/{id}/Get offer detailsNoPATCH/api/offers/{id}/Update offerYes (Owner)DELETE/api/offers/{id}/Delete offerYes (Owner)
Query Parameters for GET /api/offers/:

search - Search in title/description
min_price - Minimum price filter
max_price - Maximum price filter
max_delivery_time - Maximum delivery days
ordering - Sort by: created_at, -created_at, min_price, -min_price
creator_id - Filter by business user

Orders
MethodEndpointDescriptionAuth RequiredGET/api/orders/List user's ordersYesPOST/api/orders/Create new orderYes (Customer)PATCH/api/orders/{id}/Update order statusYes (Business)DELETE/api/orders/{id}/Delete orderYes (Admin)GET/api/order-count/{user_id}/Count in-progress ordersYesGET/api/completed-order-count/{user_id}/Count completed ordersYes
Reviews
MethodEndpointDescriptionAuth RequiredGET/api/reviews/List reviews (with filters)YesPOST/api/reviews/Create reviewYes (Customer)PATCH/api/reviews/{id}/Update own reviewYes (Owner)DELETE/api/reviews/{id}/Delete own reviewYes (Owner)
Query Parameters for GET /api/reviews/:

business_user_id - Filter by business user
reviewer_id - Filter by reviewer
ordering - Sort by: updated_at, rating

General
MethodEndpointDescriptionAuth RequiredGET/api/base-info/Get platform statisticsNo
API Usage Examples
Registration
bashPOST http://127.0.0.1:8000/api/registration/

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "repeated_password": "SecurePass123!",
  "type": "business"
}
Response:
json{
  "token": "9d3a5f7b2c1e8d4f6a9b3c7e5d2a8f1b",
  "username": "johndoe",
  "email": "john@example.com",
  "user_id": 1,
  "type": "business"
}
User Types:

"customer" - For clients looking for services
"business" - For freelancers offering services

Login
bashPOST http://127.0.0.1:8000/api/login/

{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
Response:
json{
  "token": "9d3a5f7b2c1e8d4f6a9b3c7e5d2a8f1b",
  "email": "john@example.com",
  "user_id": 1
}
Create Offer
bashPOST http://127.0.0.1:8000/api/offers/
Authorization: Token 9d3a5f7b2c1e8d4f6a9b3c7e5d2a8f1b
Content-Type: application/json

{
  "title": "Professional Website Development",
  "description": "I create modern, responsive websites",
  "image": null,
  "details": [
    {
      "title": "Basic Package",
      "revisions": 2,
      "delivery_time_in_days": 7,
      "price": 299.99,
      "features": ["Responsive Design", "5 Pages", "Contact Form"],
      "offer_type": "basic"
    },
    {
      "title": "Standard Package",
      "revisions": 3,
      "delivery_time_in_days": 14,
      "price": 599.99,
      "features": ["Responsive Design", "10 Pages", "Contact Form", "SEO", "Blog"],
      "offer_type": "standard"
    },
    {
      "title": "Premium Package",
      "revisions": 5,
      "delivery_time_in_days": 21,
      "price": 999.99,
      "features": ["Everything in Standard", "E-Commerce", "Custom CMS", "3 Months Support"],
      "offer_type": "premium"
    }
  ]
}
Create Order
bashPOST http://127.0.0.1:8000/api/orders/
Authorization: Token <customer-token>
Content-Type: application/json

{
  "offer_detail_id": 2,
  "business_user_id": 5
}
Response:
json{
  "id": 1,
  "offer_detail": 2,
  "business_user": 5,
  "customer_user": 3,
  "status": "in_progress",
  "created_at": "2026-02-13T10:00:00Z",
  "updated_at": "2026-02-13T10:00:00Z"
}
Special Features & Considerations
1. User Types
IMPORTANT: The platform has two distinct user types:

Customer (type="customer"): Can order services, write reviews
Business (type="business"): Can create offers, receive orders

Key Rules:

Only business users can create offers
Only customer users can create orders
Only customer users can write reviews
Only business users can be reviewed

2. Offer Package Structure
Every offer must have exactly 3 packages:
pythonoffer_types = ['basic', 'standard', 'premium']
Each package includes:

title - Package name
revisions - Number of revision rounds
delivery_time_in_days - Delivery timeframe
price - Package price (Decimal)
features - List of included features (Array)
offer_type - Must be: 'basic', 'standard', or 'premium'

Creating an offer without all 3 packages will fail validation!
3. Order Status Workflow
Order statuses follow this workflow:

in_progress (default on creation)
completed (updated by business user)

Status Rules:

Customer creates order → status: in_progress
Business user completes work → updates to: completed
Only business user of the order can update status

4. Review System
Critical Rules:

One Review Per Business User: A customer can only review a business user once
Customer Only: Only type="customer" users can create reviews
Business Users Only: Only type="business" users can be reviewed
No Self-Reviews: Users cannot review themselves
Rating Range: 1-5 stars only
Owner Permissions: Only review author can update/delete their review

Attempting to create a duplicate review returns 400:
json{
  "non_field_errors": [
    "You have already reviewed this business user. You can only submit one review per business profile."
  ]
}
5. Permissions System
Public Endpoints:

Registration
Login
GET /api/offers/ (list and detail)
GET /api/base-info/

Authenticated Endpoints:

All profile endpoints
POST /api/offers/ (business users only)
All order endpoints (customer for POST, business for PATCH)
All review endpoints (customer for POST)

Owner-Only Actions:

Update/Delete own offers
Update own profile
Update/Delete own reviews

Admin-Only:

Delete orders

6. Media Files & Image Uploads
Profile Images:
python# Upload profile image
PATCH /api/profile/{id}/
Content-Type: multipart/form-data

file: <image-file>
first_name: "John"
last_name: "Doe"
Offer Images:
python# Create offer with image
POST /api/offers/
Content-Type: multipart/form-data

image: <image-file>
title: "Web Development"
# ... other fields as JSON
Image Storage:

Profile images: media/profile_images/
Offer images: media/offer_images/

Access uploaded images:
http://127.0.0.1:8000/media/profile_images/filename.jpg
7. CORS Configuration
CRITICAL: Disable any "Allow CORS" browser extensions!
The backend has proper CORS configured. Browser extensions interfere with the built-in configuration and cause errors.
Common CORS issues:

Browser extension blocking requests
Frontend running on different port than configured
Browser cache not cleared after config changes

Solution:

Disable ALL CORS browser extensions
Update CORS_ALLOWED_ORIGINS in settings.py
Clear browser cache (Ctrl + Shift + R)
Test in Incognito mode

8. Frontend Integration
Include token in all authenticated requests:
javascriptconst response = await fetch('http://127.0.0.1:8000/api/offers/', {
  method: 'POST',
  headers: {
    'Authorization': 'Token YOUR_TOKEN_HERE',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: "Website Development",
    // ...
  })
});
For image uploads:
javascriptconst formData = new FormData();
formData.append('file', imageFile);
formData.append('first_name', 'John');

const response = await fetch('http://127.0.0.1:8000/api/profile/1/', {
  method: 'PATCH',
  headers: {
    'Authorization': 'Token YOUR_TOKEN_HERE',
    // Do NOT set Content-Type for FormData!
  },
  body: formData
});
Admin Panel
Access the Django admin at: http://127.0.0.1:8000/admin/
Features:

User management (customer/business)
Profile overview
Offer management
Order tracking
Review moderation

Development
Testing
Run the test suite:
bash# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test offer_app
python manage.py test order_app
python manage.py test reviews_app

# Run with verbosity
python manage.py test --verbosity=2
Test Coverage:

auth_app: Registration, Login
profile_app: Profile CRUD, Lists
offer_app: Offer CRUD, Filtering, Permissions (100%)
order_app: Order CRUD, Count endpoints (100%)
reviews_app: Review CRUD, Duplicate prevention (100%)
general_app: Platform statistics (100%)

Seeding Database
Use the included Postman collection to seed realistic data:
File: Coderr_Seed_Database_Postman.json
Includes:

6 Business users with professional profiles
24 Service offers (4 per user)
72 Offer packages (Basic/Standard/Premium)

Realistic business profiles:

Max Weber - Web Development
Sarah Schmidt - Graphic Design
Thomas Müller - Mobile Apps
Julia Fischer - Digital Marketing
Anna Becker - Content Writing
Michael Hoffmann - Video Production

To seed:

Import collection into Postman
Run all requests in sequence
Database populated with professional demo data

Troubleshooting
Issue: CORS errors in browser
Symptoms:
Access to fetch has been blocked by CORS policy
Solution:

Disable ALL browser CORS extensions ← Most common cause!
Check CORS_ALLOWED_ORIGINS matches frontend URL exactly
Ensure CORS_ALLOW_METHODS includes 'PATCH'
Restart Django server
Clear browser cache (Ctrl + Shift + R)
Test in Incognito mode

If still failing:
python# Temporarily add to settings.py for testing
CORS_ALLOW_ALL_ORIGINS = True  # Remove in production!
Issue: 401 Unauthorized on endpoints
Solution:

Verify token exists and is valid
Check header format: Authorization: Token <your-token>
Ensure token belongs to correct user type
Verify endpoint requires authentication

Check token in admin:
http://127.0.0.1:8000/admin/ → Auth Token → Tokens
Issue: Image upload fails
Symptoms:
400 Bad Request: "The submitted file is empty"
Solution:

Use multipart/form-data (NOT application/json)
Don't set Content-Type header manually (let browser set it)
Ensure media/ directory exists and is writable
Check file size isn't too large

Example working code:
javascriptconst formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/api/profile/1/', {
  method: 'PATCH',
  headers: {
    'Authorization': 'Token YOUR_TOKEN'
    // Do NOT set Content-Type!
  },
  body: formData
});
Issue: Reviews return 400 "already reviewed"
Symptoms:
json{
  "non_field_errors": [
    "You have already reviewed this business user..."
  ]
}
This is expected behavior! The system enforces one review per business user.
Solution:

Each customer can only review a business user once
To change a review, use PATCH /api/reviews/{id}/
To remove and recreate, DELETE then POST

Issue: Cannot create offer - "3 packages required"
Symptoms:
json{
  "details": ["Must provide exactly 3 offer details (basic, standard, premium)"]
}
Solution:
Ensure your offer includes all 3 packages:
json{
  "details": [
    {"offer_type": "basic", ...},
    {"offer_type": "standard", ...},
    {"offer_type": "premium", ...}
  ]
}
Production Deployment
Before deploying:

Change SECRET_KEY:

python# Use environment variable
SECRET_KEY = config('DJANGO_SECRET_KEY')

Set DEBUG = False:

pythonDEBUG = config('DEBUG', default=False, cast=bool)

Configure ALLOWED_HOSTS:

pythonALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

Use PostgreSQL:

pythonDATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': '5432',
    }
}

Configure static/media files:

pythonSTATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Use cloud storage (e.g., AWS S3, Google Cloud Storage)

Enable HTTPS:

pythonSECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

Update CORS for production:

pythonCORS_ALLOWED_ORIGINS = [
    'https://yourdomain.com',
]

Configure logging:

pythonLOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/path/to/django/error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
License
This project is licensed under the MIT License.