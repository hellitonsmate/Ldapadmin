import pytest
from flask import Flask
from app import app # Assuming app can be imported
import base64

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['ADMIN_USERNAME'] = 'testadmin'
    app.config['ADMIN_PASSWORD'] = 'testpass'
    with app.test_client() as client:
        yield client

def test_protected_route_no_auth(client):
    response = client.get('/')
    assert response.status_code == 401

def test_protected_route_wrong_credentials(client):
    auth_string = "wronguser:wrongpass"
    auth_bytes = auth_string.encode('utf-8')
    encoded_credentials = base64.b64encode(auth_bytes).decode('utf-8')
    headers = {
        'Authorization': f'Basic {encoded_credentials}'
    }
    response = client.get('/', headers=headers)
    assert response.status_code == 401

def test_protected_route_correct_credentials(client):
    username = app.config['ADMIN_USERNAME']
    password = app.config['ADMIN_PASSWORD']
    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode('utf-8')
    encoded_credentials = base64.b64encode(auth_bytes).decode('utf-8')
    headers = {
        'Authorization': f'Basic {encoded_credentials}'
    }
    response = client.get('/', headers=headers)
    assert response.status_code == 200
