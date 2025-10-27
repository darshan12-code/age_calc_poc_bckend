from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from functools import wraps
import re

app = Flask(__name__)


CORS(app)

# Request validation decorator
def validate_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function

# Date validation function
def validate_date(date_str):
    """Validate date format and check if it's not in future"""
    if not date_str:
        return False, "Date of birth is required"
    
    # Check date format (YYYY-MM-DD)
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False, "Invalid date format. Use YYYY-MM-DD"
    
    try:
        dob = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return False, "Invalid date value"
    
    today = datetime.now().date()
    
    if dob > today:
        return False, "Date of birth cannot be in the future"
    
    # Check for reasonable date (not before 1900)
    if dob.year < 1900:
        return False, "Date of birth must be after 1900"
    
    return True, dob

def calculate_age_details(dob):
    """Calculate detailed age information"""
    today = datetime.now().date()
    
    # Calculate years
    years = today.year - dob.year
    
    # Adjust if birthday hasn't occurred this year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    
    # Calculate the exact birth date for this year
    try:
        birthday_this_year = dob.replace(year=today.year)
    except ValueError:
        # Handle leap year babies (Feb 29)
        birthday_this_year = dob.replace(year=today.year, day=28)
    
    # If birthday has passed, use this year's birthday, else last year's
    if birthday_this_year <= today:
        last_birthday = birthday_this_year
    else:
        try:
            last_birthday = dob.replace(year=today.year - 1)
        except ValueError:
            last_birthday = dob.replace(year=today.year - 1, day=28)
    
    # Calculate months and days since last birthday
    months = today.month - last_birthday.month
    days = today.day - last_birthday.day
    
    if days < 0:
        months -= 1
        # Get days in previous month
        if today.month == 1:
            prev_month = 12
            prev_year = today.year - 1
        else:
            prev_month = today.month - 1
            prev_year = today.year
        
        # Get the last day of previous month
        if prev_month in [1, 3, 5, 7, 8, 10, 12]:
            days_in_prev_month = 31
        elif prev_month in [4, 6, 9, 11]:
            days_in_prev_month = 30
        else:
            # February
            if prev_year % 4 == 0 and (prev_year % 100 != 0 or prev_year % 400 == 0):
                days_in_prev_month = 29
            else:
                days_in_prev_month = 28
        
        days += days_in_prev_month
    
    if months < 0:
        months += 12
    
    # Calculate total months and days
    total_months = years * 12 + months
    total_days = (today - dob).days
    
    # Calculate next birthday
    try:
        next_birthday = dob.replace(year=today.year)
        if next_birthday <= today:
            next_birthday = dob.replace(year=today.year + 1)
    except ValueError:
        # Leap year baby
        next_birthday = dob.replace(year=today.year, day=28)
        if next_birthday <= today:
            next_birthday = dob.replace(year=today.year + 1, day=28)
    
    days_until_birthday = (next_birthday - today).days
    
    return {
        'years': years,
        'months': months,
        'days': days,
        'total_months': total_months,
        'total_days': total_days,
        'next_birthday': f"{next_birthday.strftime('%B %d, %Y')} ({days_until_birthday} days)",
        'dob': dob.strftime('%B %d, %Y')
    }

@app.route('/api/calculate-age', methods=['POST'])
@validate_json
def calculate_age():
    """Calculate age from date of birth"""
    data = request.get_json()
    dob_str = data.get('dob', '').strip()
    
    # Validate date
    is_valid, result = validate_date(dob_str)
    if not is_valid:
        return jsonify({'error': result}), 400
    
    dob = result
    
    # Calculate age details
    age_info = calculate_age_details(dob)
    
    return jsonify(age_info), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'age-calculator-api',
        'version': '1.0.0'
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)