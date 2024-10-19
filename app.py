from flask import Flask, request, jsonify
import os
import mimetypes
import requests
import time
import json
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

WEBEX_API_URL = "https://api.wxcc-us1.cisco.com/organization/{orgid}/audio-file"
ORG_ID = "{YOUR ORGID}"
AUTH_TOKEN = "{YOUR TOKEN}"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'grabacion.wav' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['grabacion.wav']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    mime_type, _ = mimetypes.guess_type(file.filename)
    if file and mime_type == 'audio/wav':
        # Renombrar el archivo para evitar duplicaciones
        timestamp = int(time.time())
        new_filename = f"grabacion_{timestamp}.wav"
        file_path = os.path.join(UPLOAD_FOLDER, new_filename)

        try:
            print(f"Saving file to {file_path}")
            file.save(file_path)
            
            blob_id = f"audio-file_{uuid.uuid4()}"
            audio_file_info = {
                "blobId": blob_id,
                "contentType": "AUDIO_WAV",
                "createdTime": int(time.time() * 1000),
                "name": new_filename,  # Usar el nuevo nombre
                "organizationId": ORG_ID,
                "version": 0
            }

            print(f"Sending file to Webex with audio_file_info: {audio_file_info}")

            url = WEBEX_API_URL.format(orgid=ORG_ID)
            files = {
                'audioFile': (new_filename, open(file_path, 'rb'), 'audio/wav'),
                'audioFileInfo': (None, json.dumps(audio_file_info), 'application/json')
            }

            headers = {
                "Authorization": f"Bearer {AUTH_TOKEN}"
            }

            response = requests.post(url, files=files, headers=headers)

            print(f"Webex API response: {response.status_code} - {response.text}")

            if response.status_code == 200:
                return jsonify({'message': 'File uploaded and sent to Webex successfully', 'file_path': file_path}), 200
            else:
                return jsonify({'error': 'Failed to upload file to Webex', 'details': response.text}), 500

        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({'error': f'Error saving or sending file: {str(e)}'}), 500

        finally:
            if 'audioFile' in files:
                files['audioFile'][1].close()

    else:
        return jsonify({'error': 'Invalid file type, only WAV files are allowed'}), 400

if __name__ == '__main__':
    app.run(debug=True)
