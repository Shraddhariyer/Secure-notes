import base64
import hashlib
import os
import time
import uuid
from flask import Flask, request, jsonify, render_template
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from google_drive import save_note_to_drive, delete_note_from_drive  # Ensure these are properly implemented
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'templates'))

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["secure_notes"]

# Function to encrypt the message using AES-GCM with a password-derived key
def encrypt_message(message, password):
    salt = os.urandom(16)
    key = PBKDF2(password, salt, dkLen=32, count=1000000)
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(message.encode())
    encrypted_message = base64.b64encode(salt + cipher.nonce + tag + ciphertext).decode()
    return encrypted_message

# Function to decrypt the message using AES-GCM with the derived password key
def decrypt_message(encrypted_message, password):
    raw_data = base64.b64decode(encrypted_message)
    salt = raw_data[:16]
    nonce = raw_data[16:32]
    tag = raw_data[32:48]
    ciphertext = raw_data[48:]

    key = PBKDF2(password, salt, dkLen=32, count=1000000)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    decrypted_message = cipher.decrypt_and_verify(ciphertext, tag).decode()
    return decrypted_message

# Function to save note to Google Drive (Implementation should be done in google_drive.py)
def save_note_to_drive(note_id, encrypted_note):
    # Implement Google Drive API to save the note
    # Return file_id for the saved note
    return f"file_id_for_{note_id}"

# Function to delete note from Google Drive (Implementation should be done in google_drive.py)
def delete_note_from_drive(file_id):
    # Implement Google Drive API to delete the note by file_id
    pass

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/create', methods=['POST'])
def create_note():
    # Extract data from the request (this part is similar to your original code)
    data = request.json
    note_content = data.get('note')
    password = data.get('password')  # User password to derive encryption key
    expire_time = int(data.get('expire_time', 300))  # Default: 5 minutes if not specified

    # Validation to check if both note content and password are provided
    if not note_content or not password:
        return jsonify({"error": "Note content and password are required!"}), 400

    # Encrypt the note content using AES encryption with password-derived key
    encrypted_note = encrypt_message(note_content, password)
    
    # Create a unique ID for the note
    note_id = str(uuid.uuid4())[:8]  # Using a short UUID (8 characters) for note ID
    
    # Save the encrypted note to Google Drive (implemented in google_drive.py)
    file_id = save_note_to_drive(note_id, encrypted_note)
    
    # Calculate the expiration time based on the current time and the requested expire_time
    expires_at = datetime.utcnow() + timedelta(seconds=expire_time)
    
    # Store the note data in MongoDB with expiration time and file information
    db.notes.insert_one({
        "_id": note_id,
        "encrypted_note": encrypted_note,
        "password": password,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "file_id": file_id,
        "accessed": False
    })

    # Return a URL to view the note
    return jsonify({"note_url": f"/view/{note_id}"})


@app.route('/view/<note_id>', methods=['GET'])
def view_note_form(note_id):
    # Fetch note from MongoDB by note_id
    note_data = db.notes.find_one({"_id": note_id})
    
    # Check if the note exists and if it's expired
    if not note_data or note_data['expires_at'] < datetime.utcnow():
        return render_template('note_deleted.html')

    # Ask the user for the password to decrypt the note
    return render_template('view.html', note_id=note_id)

@app.route('/view/<note_id>', methods=['POST'])
def view_note(note_id):
    # Fetch note data from MongoDB
    note_data = db.notes.find_one({"_id": note_id})
    
    # Check if the note exists and if it has expired
    if not note_data or note_data['expires_at'] < datetime.utcnow():
        return render_template('note_deleted.html')

    # Get the password entered by the user
    password = request.form.get('password')
    
    # Check if the password matches the one stored in the database
    if note_data['password'] != password:
        return jsonify({"error": "Incorrect password!"}), 400

    # Decrypt the note content using the password
    decrypted_note = decrypt_message(note_data['encrypted_note'], password)

    # Mark the note as accessed and delete it from MongoDB and Google Drive
    db.notes.delete_one({"_id": note_id})
    delete_note_from_drive(note_data['file_id'])

    # Render the decrypted note
    return render_template('view.html', note=decrypted_note)


if __name__ == '__main__':
    app.run(debug=True)
