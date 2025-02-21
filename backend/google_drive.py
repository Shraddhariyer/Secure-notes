import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaInMemoryUpload
from google.oauth2.service_account import Credentials
from config import GOOGLE_CREDENTIALS_FILE

# Google API setup
SERVICE_ACCOUNT_FILE = '/Users/shwet/Desktop/projects/SecureNotes/credentails.json'
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=credentials)

def save_note_to_drive(note_id, encrypted_note, use_memory_upload=True):
    service = get_drive_service()

    # Metadata for the file to be uploaded to Google Drive
    file_metadata = {'name': f"{note_id}.txt", 'mimeType': 'text/plain'}

    if use_memory_upload:
        # If using in-memory upload, directly use the encrypted note as a string
        media = MediaInMemoryUpload(encrypted_note.encode(), mimetype='text/plain')
    else:
        # If using file upload, first write to a temporary file
        with open(f"{note_id}.txt", "w") as file:
            file.write(encrypted_note)
        media = MediaFileUpload(f"{note_id}.txt", mimetype='text/plain')

    # Upload the file to Google Drive
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    # Delete the temporary file if used
    if not use_memory_upload:
        os.remove(f"{note_id}.txt")

    return file.get('id')

def delete_note_from_drive(file_id):
    service = get_drive_service()
    service.files().delete(fileId=file_id).execute()
