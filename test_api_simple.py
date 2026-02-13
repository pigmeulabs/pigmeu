#!/usr/bin/env python3
"""
Simple test to verify the API endpoints are properly configured.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_endpoints_exist():
    """Test that the new endpoints are properly defined"""
    try:
        from src.api.articles import router, approve_article, reject_article
        
        # Check if endpoints exist in router
        endpoints = [route.path for route in router.routes]
        
        print("Available article endpoints:")
        for endpoint in endpoints:
            print(f"  - {endpoint}")
        
        # Verify our new endpoints exist (check for partial matches)
        approve_found = any("/approve" in endpoint for endpoint in endpoints)
        reject_found = any("/reject" in endpoint for endpoint in endpoints)
        assert approve_found, "Approve endpoint not found"
        assert reject_found, "Reject endpoint not found"
        
        print("\n✓ All required endpoints are properly configured")
        return True
        
    except Exception as e:
        print(f"✗ Error testing endpoints: {e}")
        return False

async def test_enum_values():
    """Test that ArticleStatus enum has the required values"""
    try:
        from src.models.enums import ArticleStatus
        
        required_statuses = ['DRAFT', 'IN_REVIEW', 'APPROVED', 'PUBLISHED', 'ARCHIVED']
        
        print("\nArticleStatus enum values:")
        for status in ArticleStatus:
            print(f"  - {status.value}")
        
        # Verify required statuses exist
        for status_name in required_statuses:
            assert hasattr(ArticleStatus, status_name), f"{status_name} not found in ArticleStatus"
        
        print("✓ All required status values are present")
        return True
        
    except Exception as e:
        print(f"✗ Error testing enums: {e}")
        return False

async def test_schema_fields():
    """Test that ArticleResponse schema includes new fields"""
    try:
        # Import directly to avoid SchemaModel dependency
        from src.models.schemas import ArticleResponse
        import inspect
        
        # Get the schema fields by inspecting the model
        print("\nArticleResponse schema fields:")
        for field_name, field_info in ArticleResponse.__annotations__.items():
            print(f"  - {field_name}: {field_info}")
        
        # Verify new fields exist in annotations
        annotations = ArticleResponse.__annotations__
        assert 'approved_at' in annotations, "approved_at field missing"
        assert 'rejection_feedback' in annotations, "rejection_feedback field missing"
        assert 'rejection_timestamp' in annotations, "rejection_timestamp field missing"
        
        print("✓ All required schema fields are present")
        return True
        
    except Exception as e:
        print(f"✗ Error testing schema: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("Running API configuration tests...\n")

    results = []

    results.append(await test_endpoints_exist())
    results.append(await test_enum_values())
    results.append(await test_schema_fields())

    print(f"\n{'='*50}")
    print(f"Test Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("🎉 All API configuration tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)