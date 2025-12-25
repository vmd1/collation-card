#!/usr/bin/env python
"""Test script to verify all services can initialize."""
import sys
import os

def test_dashboard():
    """Test dashboard service."""
    print("Testing Dashboard service...")
    sys.path.insert(0, 'services/dashboard')
    sys.path.insert(0, '.')
    
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['MEDIA_PATH'] = '/tmp/test_media'
    
    from app import create_app
    app = create_app()
    
    with app.test_client() as client:
        # Test that app loads
        assert app is not None
        print("✓ Dashboard app created successfully")
    
    # Clean up path
    sys.path = [p for p in sys.path if 'dashboard' not in p]

def test_submit():
    """Test submit service."""
    print("\nTesting Submit service...")
    sys.path.insert(0, 'services/submit')
    
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['MEDIA_PATH'] = '/tmp/test_media'
    
    from app import create_app
    app = create_app()
    
    with app.test_client() as client:
        # Test health endpoint
        response = client.get('/health')
        assert response.status_code == 200
        print("✓ Submit app created successfully")
        print(f"✓ Health check: {response.get_json()}")
    
    # Clean up path
    sys.path = [p for p in sys.path if 'submit' not in p]

def test_card():
    """Test card service."""
    print("\nTesting Card service...")
    sys.path.insert(0, 'services/card')
    
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['MEDIA_PATH'] = '/tmp/test_media'
    
    from app import create_app
    app = create_app()
    
    with app.test_client() as client:
        # Test API endpoint
        response = client.get('/api/messages')
        assert response.status_code == 200
        print("✓ Card app created successfully")
        print(f"✓ API returns: {response.get_json()}")
    
    # Clean up path
    sys.path = [p for p in sys.path if 'card' not in p]

if __name__ == '__main__':
    print("=" * 60)
    print("Virtual Card - Service Tests")
    print("=" * 60)
    
    try:
        test_dashboard()
        test_submit()
        test_card()
        
        print("\n" + "=" * 60)
        print("✓ All services passed tests!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
