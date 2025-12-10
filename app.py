from flask import Flask, request, render_template, redirect, url_for, send_file, session
import asyncio
import io
import csv
from urllib.parse import urlparse
import email_theifer # Your modified script

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_session' # Replace with a strong, unique key in production

# --- Helper Functions ---
def is_valid_http_url(url):
    """Checks if the given string is a valid HTTP or HTTPS URL."""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except ValueError:
        return False

# --- Routes ---
@app.route('/', methods=['GET'])
def index():
    """Renders the main input form."""
    return render_template('index.html')

@app.route('/theif', methods=['POST'])
async def theif():
    """Handles the URL submission, runs the email_theifer, and displays results."""
    target_url = request.form.get('url')
    
    if not target_url:
        return render_template('index.html', error="Please enter a URL.")
    
    if not is_valid_http_url(target_url):
        return render_template('index.html', error="Please enter a valid HTTP or HTTPS URL.")

    emails = []
    error_message = None
    try:
        # Run the email_theifer. This is where the long-running task might hit timeouts.
        emails = await email_theifer.run_email_theifer(target_url)
        session['found_emails'] = emails # Store emails in session for download
    except asyncio.TimeoutError:
        error_message = "Crawl timed out. The website might be too large or slow. Try a smaller scope."
    except Exception as e:
        error_message = f"An error occurred during crawling: {e}"

    return render_template('results.html', emails=emails, error=error_message, target_url=target_url)

@app.route('/download_emails', methods=['GET'])
def download_emails():
    """Allows users to download the found emails as a CSV file."""
    emails = session.get('found_emails', [])
    if not emails:
        return redirect(url_for('index')) # Redirect if no emails in session

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Email Address']) # CSV header
    for email in emails:
        writer.writerow([email])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='extracted_emails.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)
