#!/usr/bin/env python3
"""
Test script for Celery + Redis setup
Verifies that all components are correctly configured
"""
import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    try:
        from app.core.celery_app import celery_app
        print("✓ celery_app imported successfully")
        
        from app.tasks.scan_tasks import perform_osint_scan, COLLECTOR_MAP
        print(f"✓ scan_tasks imported successfully ({len(COLLECTOR_MAP)} collectors)")
        
        from app.routers.scan import router
        print("✓ scan router imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_celery_config():
    """Test Celery configuration"""
    print("\n🔍 Testing Celery configuration...")
    try:
        from app.core.celery_app import celery_app
        
        config = celery_app.conf
        print(f"✓ Broker: {config.broker_url}")
        print(f"✓ Backend: {config.result_backend}")
        print(f"✓ Serializer: {config.task_serializer}")
        print(f"✓ Default queue: {config.task_default_queue}")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_redis_connection():
    """Test Redis connection"""
    print("\n🔍 Testing Redis connection...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✓ Redis is running and accessible")
        
        # Test set/get
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        r.delete('test_key')
        print("✓ Redis read/write working")
        
        return True
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        print("  Make sure Redis is running: redis-server")
        return False


def test_collector_map():
    """Test that all collectors are available"""
    print("\n🔍 Testing collector mapping...")
    try:
        from app.tasks.scan_tasks import COLLECTOR_MAP
        
        print(f"✓ Found {len(COLLECTOR_MAP)} collectors:")
        for collector_type, collector_class in COLLECTOR_MAP.items():
            print(f"  - {collector_type}: {collector_class.__name__}")
        
        return True
    except Exception as e:
        print(f"✗ Collector map test failed: {e}")
        return False


def test_task_registration():
    """Test that Celery tasks are registered"""
    print("\n🔍 Testing task registration...")
    try:
        from app.core.celery_app import celery_app
        
        registered_tasks = celery_app.tasks
        task_names = [name for name in registered_tasks.keys() if 'app.tasks' in name]
        
        print(f"✓ Found {len(task_names)} registered tasks:")
        for task_name in task_names:
            print(f"  - {task_name}")
        
        return True
    except Exception as e:
        print(f"✗ Task registration test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("CELERY + REDIS SETUP TEST")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Celery Config", test_celery_config),
        ("Redis Connection", test_redis_connection),
        ("Collector Map", test_collector_map),
        ("Task Registration", test_task_registration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Setup is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
