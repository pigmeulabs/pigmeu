#!/usr/bin/env python3
"""
Test script to verify article generation functionality.
"""

import asyncio
from src.workers.article_structurer import ArticleStructurer
from src.workers.llm_client import LLMClient


async def test_article_structurer():
    """Test the ArticleStructurer with mock data."""
    
    print("🧪 Testing ArticleStructurer...")
    
    # Create structurer
    structurer = ArticleStructurer()
    
    # Mock book data
    book_data = {
        "title": "Designing Data-Intensive Applications",
        "author": "Martin Kleppmann",
        "metadata": {
            "theme": "Computer Science",
            "pages": 600,
            "description": "A comprehensive guide to building reliable, scalable, and maintainable applications."
        },
        "context": "This book covers fundamental principles of data systems including reliability, scalability, and maintainability. It explores various data storage and processing techniques."
    }
    
    print(f"📚 Testing with book: {book_data['title']} by {book_data['author']}")
    
    try:
        # Test topic extraction
        print("\n🔍 Testing topic extraction...")
        topics = await structurer.extract_topics(book_data)
        print(f"✅ Extracted {len(topics)} topics:")
        for i, topic in enumerate(topics, 1):
            print(f"   {i}. {topic['name']}: {topic['description']}")
            if topic.get('subtopics'):
                print(f"      Subtopics: {', '.join(topic['subtopics'])}")
    
    except Exception as e:
        print(f"❌ Topic extraction failed: {e}")
        return False
    
    try:
        # Test article generation
        print("\n📝 Testing article generation...")
        article_content = await structurer.structure_article(book_data, topics, book_data['context'])
        print(f"✅ Generated article with {len(article_content.split())} words")
        
        # Show first few lines
        lines = article_content.split('\n')
        print("\n📄 Article preview:")
        for line in lines[:10]:
            print(f"   {line}")
        
    except Exception as e:
        print(f"❌ Article generation failed: {e}")
        return False
    
    try:
        # Test article validation
        print("\n🔍 Testing article validation...")
        validation = await structurer.validate_article(article_content)
        
        if validation['is_valid']:
            print("✅ Article validation passed!")
            print(f"   Word count: {validation['word_count']}")
            print(f"   Sections: {validation['section_counts']['h1']} H1, {validation['section_counts']['h2']} H2, {validation['section_counts']['h3']} H3")
            print(f"   Paragraphs: {validation['paragraph_stats']['total_paragraphs']} total")
        else:
            print("❌ Article validation failed:")
            for error in validation['errors']:
                print(f"   - {error}")
            return False
            
    except Exception as e:
        print(f"❌ Article validation failed: {e}")
        return False
    
    print("\n✅ All tests passed!")
    return True


async def test_complete_pipeline():
    """Test the complete article generation pipeline."""
    
    print("\n🚀 Testing complete article generation pipeline...")
    
    structurer = ArticleStructurer()
    
    book_data = {
        "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
        "author": "Robert C. Martin",
        "metadata": {
            "theme": "Software Engineering",
            "pages": 464,
            "description": "A guide to writing clean, maintainable, and professional code."
        },
        "context": "This book teaches best practices for writing clean code in various programming languages. It covers principles, patterns, and practical techniques for improving code quality."
    }
    
    try:
        # Generate and validate article
        article_content = await structurer.generate_valid_article(
            book_data=book_data,
            context=book_data['context'],
            max_retries=2
        )
        
        print(f"✅ Successfully generated valid article!")
        print(f"   Word count: {len(article_content.split())}")
        
        # Validate the generated article
        validation = await structurer.validate_article(article_content)
        
        if validation['is_valid']:
            print("✅ Generated article passed all validation checks!")
            return True
        else:
            print("❌ Generated article failed validation:")
            for error in validation['errors']:
                print(f"   - {error}")
            return False
            
    except Exception as e:
        print(f"❌ Complete pipeline test failed: {e}")
        return False


async def main():
    """Main test function."""
    
    print("🧪 Starting ArticleStructurer tests...\n")
    
    # Test 1: Basic functionality
    test1_passed = await test_article_structurer()
    
    # Test 2: Complete pipeline
    test2_passed = await test_complete_pipeline()
    
    print("\n" + "="*50)
    print("📊 Test Results:")
    print(f"   Basic functionality: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Complete pipeline: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("="*50)
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print("\n💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)