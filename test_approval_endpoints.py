#!/usr/bin/env python3
"""
Test script for article approval endpoints.
This script tests the new approval/rejection functionality.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.enums import ArticleStatus
from src.db.repositories import ArticleRepository, SubmissionRepository
from src.api.articles import approve_article, reject_article
from src.api.dependencies import get_article_repo, get_submission_repo

# Mock database and dependencies
class MockArticle:
    def __init__(self, article_id, status, submission_id=None):
        self.article_id = article_id
        self.status = status
        self.submission_id = submission_id
        self.data = {
            "_id": article_id,
            "status": status,
            "submission_id": submission_id,
            "title": "Test Article",
            "content": "Test content",
            "word_count": 100,
            "book_id": "book_123"
        }

    async def get_by_id(self, article_id):
        if article_id == self.article_id:
            return self.data
        return None

    async def update(self, article_id, fields):
        if article_id == self.article_id:
            self.data.update(fields)
            return True
        return False

class MockSubmission:
    def __init__(self, submission_id, status):
        self.submission_id = submission_id
        self.status = status
        self.data = {
            "_id": submission_id,
            "status": status,
            "title": "Test Submission",
            "author_name": "Test Author"
        }

    async def get_by_id(self, submission_id):
        if submission_id == self.submission_id:
            return self.data
        return None

    async def update_status(self, submission_id, status, extra_fields):
        if submission_id == self.submission_id:
            self.data["status"] = status
            self.data.update(extra_fields)
            return True
        return False

async def test_approve_article():
    """Test article approval functionality"""
    print("Testing article approval...")

    # Setup mock data
    article_id = "article_123"
    submission_id = "sub_123"

    article_repo = MockArticle(article_id, ArticleStatus.IN_REVIEW.value, submission_id)
    submission_repo = MockSubmission(submission_id, "article_generated")

    # Test approval
    try:
        result = await approve_article(
            article_id,
            article_repo,
            submission_repo
        )

        print(f"✓ Approval successful: {result}")

        # Verify status changes
        article_data = await article_repo.get_by_id(article_id)
        submission_data = await submission_repo.get_by_id(submission_id)

        assert article_data["status"] == ArticleStatus.APPROVED.value, f"Expected approved status, got {article_data['status']}"
        assert submission_data["status"] == "approved", f"Expected approved submission status, got {submission_data['status']}"
        assert "approved_at" in article_data, "approved_at should be set"

        print("✓ All approval assertions passed")
        return True

    except Exception as e:
        print(f"✗ Approval test failed: {e}")
        return False

async def test_reject_article():
    """Test article rejection functionality"""
    print("\nTesting article rejection...")

    # Setup mock data
    article_id = "article_456"
    submission_id = "sub_456"

    article_repo = MockArticle(article_id, ArticleStatus.IN_REVIEW.value, submission_id)
    submission_repo = MockSubmission(submission_id, "article_generated")

    # Test rejection
    try:
        payload = {"feedback": "Needs more details"}
        result = await reject_article(
            article_id,
            payload,
            article_repo
        )

        print(f"✓ Rejection successful: {result}")

        # Verify status changes
        article_data = await article_repo.get_by_id(article_id)

        assert article_data["status"] == ArticleStatus.DRAFT.value, f"Expected draft status, got {article_data['status']}"
        assert article_data["rejection_feedback"] == "Needs more details", "Feedback should be stored"
        assert "rejection_timestamp" in article_data, "rejection_timestamp should be set"

        print("✓ All rejection assertions passed")
        return True

    except Exception as e:
        print(f"✗ Rejection test failed: {e}")
        return False

async def test_invalid_approval():
    """Test invalid approval scenarios"""
    print("\nTesting invalid approval scenarios...")

    # Test approving an already approved article
    article_id = "article_789"
    article_repo = MockArticle(article_id, ArticleStatus.APPROVED.value)

    try:
        await approve_article(article_id, article_repo, None)
        print("✗ Should have failed approving already approved article")
        return False
    except Exception as e:
        print(f"✓ Correctly rejected approval of approved article: {e}")

    # Test approving a published article
    article_id = "article_101"
    article_repo = MockArticle(article_id, ArticleStatus.PUBLISHED.value)

    try:
        await approve_article(article_id, article_repo, None)
        print("✗ Should have failed approving published article")
        return False
    except Exception as e:
        print(f"✓ Correctly rejected approval of published article: {e}")

    return True

async def main():
    """Run all tests"""
    print("Running article approval/rejection tests...\n")

    results = []

    results.append(await test_approve_article())
    results.append(await test_reject_article())
    results.append(await test_invalid_approval())

    print(f"\n{'='*50}")
    print(f"Test Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)