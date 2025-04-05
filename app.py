from flask import Flask, request, jsonify, render_template, send_from_directory
from PIL import Image
import pytesseract
import re
from datetime import datetime
import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import pandas as pd
from dashboard_helpers import (
    get_savings_suggestions, 
    compare_spending, 
    cash_flow_analysis, 
    spending_alerts,
    get_top_time_intervals
)

app = Flask(__name__,
    template_folder='templates',
    static_folder='static'
)

# Initialize Firebase
import os
import json
from firebase_admin import credentials, initialize_app

firebase_cred_json = os.getenv('FIREBASE_CREDENTIALS')
if firebase_cred_json:
    cred_dict = json.loads(firebase_cred_json)
    cred = credentials.Certificate(cred_dict)
else:
    raise ValueError("Firebase credentials not found.")


firebase_admin.initialize_app(cred)
db = firestore.client()

# Collections for Credit and Debit transactions
credit_collection = db.collection('credit_transactions')
debit_collection = db.collection('debit_transactions')

print("\nFirebase Setup Verified:")
print(f"Using collections: credit_transactions and debit_transactions")

# Helper function to convert Firestore documents to dictionaries
def firestore_to_dict(doc):
    if not doc.exists:
        return None
    doc_dict = doc.to_dict()
    doc_dict['id'] = doc.id
    return doc_dict

def preprocess_image(image_path):
    """Preprocess the uploaded image for better OCR results."""
    image = Image.open(image_path)
    image = image.convert('L')  # Convert to grayscale
    image = image.point(lambda x: 0 if x < 150 else 255)  # Increase contrast
    return image

def convert_to_12_hour_format(time_str):
    """Convert time string to 12-hour format."""
    try:
        if ':' in time_str and len(time_str.split(':')[0]) == 2:
            time_obj = datetime.strptime(time_str, '%H:%M')
            return time_obj.strftime('%I:%M %p')
    except ValueError:
        return time_str

def extract_transaction_details(image_path):
    """Extract transaction details from uploaded image using OCR."""
    try:
        image = preprocess_image(image_path)
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, config=custom_config)
        
        print("Extracted Text:", text)  # Debugging

        # Clean and process text
        corrected_text = re.sub(r'[^\w\s₹.,:am|pm]', '', text)
        corrected_text = re.sub(r'(?<=\d)3(?=\d)', '₹', corrected_text)
        corrected_text = re.sub(r'%', '₹', corrected_text)

        # Determine transaction status
        transaction_status = "Unknown"
        if "credited" in corrected_text.lower():
            transaction_status = "Credited"
        elif "debited" in corrected_text.lower():
            transaction_status = "Debited"

        details = {'Status': transaction_status}

        # Extract date and time
        date_time = re.search(r'(\d{1,2}:\d{2}\s*[APap][Mm])\s*on\s*(\d{1,2}\s\w+\s\d{4})', corrected_text)
        if date_time:
            time_str = date_time.group(1).strip()
            date_str = date_time.group(2).strip()
            
            try:
                datetime_str = f"{date_str} {time_str}"
                datetime_obj = datetime.strptime(datetime_str, '%d %b %Y %I:%M %p')
                details['date'] = datetime_obj
                details['Date'] = datetime_obj.strftime('%Y-%m-%d')
                details['Time'] = datetime_obj.strftime('%H:%M')
            except ValueError as e:
                print(f"Date parsing error: {e}")

        # Extract sender/receiver
        if transaction_status == "Credited":
            sender_match = re.search(r'Received from\s*\n*([^\d\n]+)', corrected_text)
            if sender_match:
                details['Sender'] = sender_match.group(1).strip()
        elif transaction_status == "Debited":
            receiver_match = re.search(r'Paid to\s*\n*([^\d\n]+)', corrected_text)
            if receiver_match:
                details['Receiver'] = receiver_match.group(1).strip()

        # Extract amount
        amount_match = re.search(r'(?:₹|Rs\.?)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', corrected_text)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            details['Amount'] = float(amount_str)

        return details
    except Exception as e:
        print(f"Error in extract_transaction_details: {e}")
        return {'error': str(e)}

@app.route('/')
def index():
    """Render the landing page."""
    try:
        return render_template('tpg.html')
    except Exception as e:
        print(f"Error rendering template: {e}")
        return str(e), 500

@app.route('/upload', methods=['POST'])
def upload_image():
    """Handle image upload and extraction of transaction details."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Create uploads directory if it doesn't exist
        if not os.path.exists('uploads'):
            os.makedirs('uploads')

        image_path = os.path.join('uploads', image_file.filename)
        image_file.save(image_path)
        
        details = extract_transaction_details(image_path)
        
        # Clean up uploaded file
        try:
            os.remove(image_path)
        except Exception as e:
            print(f"Error removing temporary file: {e}")
        
        return jsonify(details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submit', methods=['POST'])
def submit_transaction():
    """Handle transaction form submission."""
    try:
        # Extract form data
        data = {
            'name': request.form.get('name'),
            'transaction_id': request.form.get('transaction_id'),
            'amount': float(request.form.get('amount', 0)),
            'payee_type': request.form.get('payee_type'),
            'personal_reference': request.form.get('personal_reference'),
            'transaction_rating': request.form.get('transaction_rating')
        }

        # Parse and combine date and time
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        if date_str and time_str:
            data['date'] = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')

        # Insert data into appropriate collection
        payment_type = request.form.get('payment_type')
        if payment_type == 'Credited':
            credit_collection.add(data)
        else:
            debit_collection.add(data)

        return jsonify({'message': 'Transaction data stored successfully'}), 200
    except Exception as e:
        print(f"Error in submit_transaction: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    template_path = os.path.join('templates', 'financial_dashboard.html')
    if not os.path.exists(template_path):
        return f"Template not found at {template_path}", 404
    return render_template('financial_dashboard.html')

@app.route('/dashboard-data')
def dashboard_data():
    try:
        # Get all credit transactions
        credit_docs = credit_collection.stream()
        credit_transactions = [doc.to_dict() for doc in credit_docs]
        
        # Get all debit transactions
        debit_docs = debit_collection.stream()
        debit_transactions = [doc.to_dict() for doc in debit_docs]

        credit_df = pd.DataFrame(credit_transactions)
        debit_df = pd.DataFrame(debit_transactions)

        # Convert 'date' columns to datetime and coerce errors
        if 'date' in credit_df.columns:
            credit_df['date'] = pd.to_datetime(credit_df['date'], errors='coerce')
        if 'date' in debit_df.columns:
            debit_df['date'] = pd.to_datetime(debit_df['date'], errors='coerce')

        all_transactions = pd.concat([credit_df, debit_df], ignore_index=True)
        if 'date' in all_transactions.columns:
            all_transactions['date'] = pd.to_datetime(all_transactions['date'], errors='coerce')

        # Perform financial analysis
        savings_suggestions = get_savings_suggestions(all_transactions)
        monthly_comparison = compare_spending(all_transactions)
        alerts = spending_alerts(all_transactions)

        # Pass the credit_df and debit_df to cash_flow_analysis
        inflows, outflows = cash_flow_analysis(credit_df, debit_df)
        
        # Get top 3 time intervals with highest transaction counts
        top_time_intervals = get_top_time_intervals(credit_df, debit_df)

        # Convert the DataFrames to JSON-compatible data structures
        credit_chart_data = {
            'dates': credit_df['date'].dt.strftime('%Y-%m-%d').tolist() if 'date' in credit_df.columns else [],
            'amounts': credit_df['amount'].tolist() if 'amount' in credit_df.columns else []
        }
        debit_chart_data = {
            'dates': debit_df['date'].dt.strftime('%Y-%m-%d').tolist() if 'date' in debit_df.columns else [],
            'amounts': debit_df['amount'].tolist() if 'amount' in debit_df.columns else []
        }

        # Dashboard data to send to the frontend
        dashboard_data = {
            'monthly_comparison': monthly_comparison,
            'savings_suggestions': savings_suggestions,
            'inflows': inflows,
            'outflows': outflows,
            'alerts': alerts,
            'credit_chart_data': credit_chart_data,
            'debit_chart_data': debit_chart_data,
            'top_time_intervals': top_time_intervals.to_dict(orient='records') if top_time_intervals is not None else []
        }

        return jsonify(dashboard_data)
    except Exception as e:
        print(f"Error in dashboard_data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/history')
def history():
    try:
        print("\n=== Starting History Route ===")
        
        # Check Firebase connection
        print("Checking Firebase connection...")
        
        # Fetch transactions
        print("\nFetching transactions...")
        credit_docs = credit_collection.stream()
        credit_transactions = [doc.to_dict() for doc in credit_docs]
        debit_docs = debit_collection.stream()
        debit_transactions = [doc.to_dict() for doc in debit_docs]
        
        print(f"Found {len(credit_transactions)} credit transactions")
        print(f"Found {len(debit_transactions)} debit transactions")
        
        # Parse dates
        print("\nParsing dates...")
        def parse_date_and_time(transactions):
            processed_transactions = []
            for transaction in transactions:
                try:
                    if 'date' in transaction and transaction['date']:
                        if isinstance(transaction['date'], datetime):
                            dt = transaction['date']
                        elif isinstance(transaction['date'], str):
                            dt = datetime.strptime(transaction['date'], '%Y-%m-%d %H:%M:%S')
                        else:
                            # Handle Firestore Timestamp
                            dt = transaction['date'].to_pydatetime()
                        transaction['date'] = dt.strftime('%Y-%m-%d')
                        transaction['time'] = dt.strftime('%H:%M:%S')
                    else:
                        transaction['date'] = 'Unknown Date'
                        transaction['time'] = 'Unknown Time'
                    processed_transactions.append(transaction)
                except Exception as e:
                    print(f"Error processing transaction: {e}")
                    print(f"Problematic transaction: {transaction}")
            return processed_transactions

        credit_transactions = parse_date_and_time(credit_transactions)
        debit_transactions = parse_date_and_time(debit_transactions)
        
        print("\nRendering template...")
        return render_template(
            'financial_history.html',
            credit_transactions=credit_transactions,
            debit_transactions=debit_transactions
        )
    except Exception as e:
        print(f"\nERROR in history route: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    print("Current working directory:", os.getcwd())
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True, port=5000)