from flask import Flask, request, jsonify, send_from_directory, render_template, send_file, redirect, url_for
import os
from PyPDF2 import PdfReader
from gtts import gTTS
import qrcode
import logging

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = 'audio'
QR_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/pdf_to_audio')
def pdf_to_audio():
    return render_template('pdf_to_audio.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.pdf'):
        pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(pdf_path)

        try:
            text = extract_text_from_pdf(pdf_path)
            if not text:
                raise ValueError("Extracted text is empty")

            audio_filename = file.filename.replace('.pdf', '.mp3')
            audio_path = convert_text_to_audio(text, audio_filename)
            return redirect(url_for('download_audio', filename=audio_filename))
        except Exception as e:
            logging.error(f"Error processing file {file.filename}: {str(e)}")
            return jsonify({'error': f"Failed to process the PDF: {str(e)}"}), 500

    return jsonify({'error': 'Invalid file format'}), 400

def extract_text_from_pdf(pdf_path):
    logging.debug(f"Extracting text from PDF: {pdf_path}")
    text = ""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                logging.debug(f"Extracted text from page {page_num}: {page_text[:100]}...")  # Log first 100 characters
                text += page_text
    except Exception as e:
        logging.error(f"Failed to extract text from PDF {pdf_path}: {str(e)}")
        raise
    return text

def convert_text_to_audio(text, filename):
    logging.debug(f"Converting text to audio: {filename}")
    try:
        tts = gTTS(text=text, lang='en')
        audio_path = os.path.join(AUDIO_FOLDER, filename)
        tts.save(audio_path)
    except Exception as e:
        logging.error(f"Failed to convert text to audio {filename}: {str(e)}")
        raise
    return audio_path

@app.route('/audio/<filename>')
def download_audio(filename):
    return send_file(os.path.join(AUDIO_FOLDER, filename), as_attachment=True)

@app.route('/qr_generator')
def qr_generator():
    return render_template('qr_generator.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    content_type = request.form['content_type']
    content = request.form['content']

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(content)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(os.path.join(QR_FOLDER, 'qrcode.png'))

    return render_template('result.html', content_type=content_type, download_link='/download_qr')

@app.route('/download_qr')
def download_qr():
    return send_file(os.path.join(QR_FOLDER, 'qrcode.png'), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
