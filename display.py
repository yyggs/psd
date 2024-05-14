import logging
from flask import Flask, make_response, request, render_template_string, jsonify, redirect, url_for, send_from_directory, \
    render_template
from werkzeug.utils import secure_filename
import os
import requests
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROTO_DIR = os.path.join(BASE_DIR, '..')
sys.path.append(PROTO_DIR)
import extract


app = Flask(__name__)

# Set the directory for file uploads
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'UploadedPaper') 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class Article:
    def __init__(self, title, keywords, abstract, references, doi):
        self.title = title
        self.keywords = keywords
        self.abstract = abstract
        self.references = references
        self.doi = doi

    def __repr__(self):
        return f"Article(title={self.title}, keywords={self.keywords}, abstract={self.abstract}, references={self.references}, doi = {self.doi})"

articles = {}

def check_grobid_service(url):
    try:
        response = requests.get(url + "/api/isalive", timeout=5)  # Set timeout to 5 seconds
        if response.status_code == 200:
            print("Grobid service is running.")
            return True
        else:
            print("Grobid service returned an error: Status code", response.status_code)
            return False
    except requests.exceptions.ConnectionError:
        print("Unable to connect to Grobid service.")
        return False
    except requests.exceptions.Timeout:
        print("Request to connect to Grobid service timed out.")
        return False



@app.route('/')
def index():
    with open(BASE_DIR+'/page1.html', 'r') as file:
        html_content = file.read()
    return render_template_string(html_content)

@app.route('/page2.html')
def page2():
    return render_template('page2.html')

@app.route('/check-data-ready', methods=['GET'])
def check_data_ready():
    if articles:  
        return jsonify({'ready': True, 'message': 'Data is ready.'})
    else:
        return jsonify({'ready': False, 'message': 'Data is not ready yet.'})

@app.route('/page3')
def page3():
    return render_template('page3.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    grobid_server_url = "http://grobid:8070"
    
    if not check_grobid_service(grobid_server_url):
        return make_response(jsonify({"error": "Grobid service is not running. The docker is preparing, please wait"}), 503)

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not file.filename.lower().endswith('.pdf'):
        # Return a specific JSON response if the file is not a PDF
        return jsonify({'error': 'Invalid file type', 'message': 'Only PDF files are allowed'}), 401

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return redirect('/page2.html')

@app.route('/process-file', methods=['GET'])
def process_uploaded_file():
    processed_articles = extract.process_file()
    for idx, article in enumerate(processed_articles, start=0):
        articles[str(idx)] = article.__dict__
    return jsonify(articles)  



@app.route('/paper-details/<paper_number>')
def get_paper_details(paper_number):
    print("Paper number:", paper_number)
    if paper_number not in articles:
        return jsonify({'error': 'Paper not found'}), 404

    return jsonify(articles[paper_number]), 200

if __name__ == "__main__":
    app.run(debug=True)
