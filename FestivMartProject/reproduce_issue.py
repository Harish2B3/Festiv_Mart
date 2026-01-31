import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FestivMartProject.settings')
from django.conf import settings
if not settings.configured:
    django.setup()
settings.ALLOWED_HOSTS.append('testserver')

from django.test import Client
from django.contrib.auth.models import User

def test_signup():
    client = Client()
    
    # Test Individual Signup
    print("Testing Individual Signup...")
    response = client.post('/signup/', {
        'username': 'test_individual',
        'email': 'individual@test.com',
        'password': 'password123',
        'password_confirm': 'password123',
        'first_name': 'Test',
        'last_name': 'Individual',
        'account_type': 'individual',
        'terms_agreed': 'on'
    })
    print(f"Individual Response: {response.status_code}")
    if response.status_code == 302:
        print("Individual Signup Successful (Redirected to dashboard)")
    else:
        print("Individual Signup Failed")
        # print(response.content.decode())

    # Test Business Signup
    print("\nTesting Business Signup...")
    response = client.post('/signup/', {
        'username': 'test_business',
        'email': 'business@test.com',
        'password': 'password123',
        'password_confirm': 'password123',
        'first_name': 'Test',
        'last_name': 'Business',
        'account_type': 'business',
        'business_name': 'Test Corp',
        'terms_agreed': 'on'
    })
    print(f"Business Response: {response.status_code}")
    if response.status_code == 302:
        print("Business Signup Successful (Redirected to dashboard)")
    else:
        print("Business Signup Failed")
        # print(response.content.decode())

if __name__ == "__main__":
    test_signup()
