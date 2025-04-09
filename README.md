# Digital Wallet Tracker
![Dashboard Screenshot](https://github.com/VaishnaviVadla33/DigitalWalletTracker02/raw/main/Dashboard_image.png)
Digital Wallet Tracker is a web application designed to help users track their Unified Payments Interface (UPI) transactions efficiently. Users can upload screenshots of their transaction confirmations, and the application uses Optical Character Recognition (OCR) to extract relevant details like amount, date, time, and sender/receiver. This data is then stored and can be visualized on a comprehensive financial dashboard, offering insights into spending patterns, cash flow, and potential savings.

The application utilizes Flask for the backend, Firebase Firestore for database storage, and various Python libraries for OCR and data analysis. The frontend provides an intuitive interface for uploading images, viewing transaction history, and exploring the interactive dashboard.

## Features

* **Transaction Screenshot Upload:** Upload images (screenshots) of UPI transaction confirmations.
* **OCR Data Extraction:** Automatically extracts transaction details (amount, date, time, status - credited/debited, sender/receiver) from the uploaded image using Pytesseract.
* **Manual Data Entry/Edit:** Allows users to review and edit extracted details or manually input transaction data via a form.
* **Transaction Categorization:** Classify transactions as Personal, Regular Bills, or Business, and add personal references (Family, Friends, Others).
* **Priority Rating:** Rate transactions based on necessity (Necessary, Moderate, Not Necessary).
* **Firebase Firestore Integration:** Securely stores credit and debit transaction data in separate Firestore collections.
* **Transaction History:** View a detailed history of all recorded credit and debit transactions in tabular format.
* **Financial Dashboard:**
    * Visualize credit and debit transaction history over time (Line Chart).
    * Compare monthly spending across different years (Bar Chart).
    * Analyze cash flow with an Inflow vs. Outflow summary (Doughnut Chart).
    * Identify peak transaction times (Bar Chart).
    * Receive potential savings suggestions based on spending categories.
    * Get alerts for significant spending amounts.

## Technologies Used

* **Backend:** Python, Flask
* **Database:** Google Firebase Firestore
* **OCR:** Pytesseract, Pillow (PIL Fork)
* **Data Analysis:** Pandas, NumPy, Scikit-learn
* **Frontend:** HTML, CSS, JavaScript
* **Charting:** Chart.js
* **Environment Variables:** python-dotenv
* **Deployment (Implied):** Gunicorn (listed in requirements)

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd DigitalWalletTracker02-main
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You might need to install Tesseract OCR engine separately on your system for Pytesseract to work. Refer to the Tesseract documentation for OS-specific instructions.)*
4.  **Set up Firebase:**
    * Create a Firebase project at [https://console.firebase.google.com/](https://console.firebase.google.com/).
    * Enable Firestore Database.
    * Generate a private key file (Service Account JSON) for your project.
    * Set the `FIREBASE_CREDENTIALS` environment variable to the *content* of this JSON key file. You can use a `.env` file for this:
        ```.env
        FIREBASE_CREDENTIALS='{ "type": "service_account", "project_id": "...", ... }'
        ```
5.  **Run the application:**
    ```bash
    flask run
    ```
    Or using Gunicorn:
    ```bash
    gunicorn app:app
    ```
6.  Access the application in your browser, typically at `http://127.0.0.1:5000/`.

## Usage

1.  Navigate to the home page.
2.  Ensure you have a full screenshot of the desired transaction from your **PhonePe history**.
3.  Click or drag the transaction screenshot onto the upload area.
4.  Click "Extract Transaction Details".
5.  A modal window will appear pre-filled with the extracted data.
6.  **Carefully review and verify** all extracted details. Correct any inaccuracies. Fill in the remaining fields (Category, Reference, Rating).
7.  Submit the transaction. A success message will confirm storage.
8.  Navigate to the "Transaction History" page to view all entries.
9.  Navigate to the "Dashboard" page to see visualizations and financial insights.

## Important Notes

* **Application Scope:** This application is currently designed **specifically for PhonePe transaction screenshots**. Screenshots from other UPI apps may not work correctly.
* **Screenshot Requirements:** For best results, please upload a **full, clear screenshot** of the transaction taken directly from your PhonePe **transaction history** screen.
* **OCR Accuracy:** The text extraction (OCR) process is not 100% accurate in all cases. Accuracy can be affected by factors like screenshot quality and changes in the PhonePe app's font or layout.
* **User Verification Required:** Due to potential OCR inaccuracies, it is **essential** that you carefully review and verify all extracted data in the form after uploading a screenshot before submitting the transaction.

## Live Demo & Conclusion

This application provides a practical way to digitize and analyze your PhonePe transaction history.

You can access a live preview of the website hosted on Render here:

**[Website Preview](https://digitalwallettracker02.onrender.com/)**

**Important Demo Limitation:** Please note that the **OCR/image extraction functionality does not work** in this hosted preview version due to deployment environment limitations (likely related to Tesseract dependencies). The demo primarily showcases the frontend interface, form structure, and dashboard layout.

To experience the full application, including the transaction data extraction, please follow the given setup--installation steps to run it on your local machine.
