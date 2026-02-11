i"""
Test cases for ArticleStructurer.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.workers.article_structurer import ArticleStructurer


@pytest.mark.asyncio
async def test_extract_topics():
    """Test topic extraction from book data."""
    
    # Mock book data
    book_data = {
        "title": "Designing Data-Intensive Applications",
        "author": "Martin Kleppmann",
        "metadata": {
            "theme": "Computer Science",
            "pages": 600,
            "description": "A comprehensive guide to building reliable, scalable, and maintainable applications."
        }
    }
    
    # Mock LLM response
    mock_llm_response = '''{
  "topics": [
    {
      "name": "Data Systems Fundamentals",
      "description": "Core principles of data-intensive applications",
      "subtopics": ["Reliability", "Scalability", "Maintainability"]
    },
    {
      "name": "Data Storage",
      "description": "Different approaches to data storage",
      "subtopics": ["OLTP", "OLAP", "Data warehousing"]
    },
    {
      "name": "Data Processing",
      "description": "Stream and batch processing techniques",
      "subtopics": ["Stream processing", "Batch processing", "Hybrid approaches"]
    }
  ]
}'''
    
    # Create ArticleStructurer with mocked LLM client
    structurer = ArticleStructurer()
    structurer.llm_client = MagicMock()
    structurer.llm_client.generate = AsyncMock(return_value=mock_llm_response)
    
    # Mock database
    with patch('src.workers.article_structurer.get_database') as mock_db:
        mock_prompts = MagicMock()
        mock_prompts.find_one = AsyncMock(return_value={
            "name": "Topic Extractor for Books",
            "system_prompt": "You are a book analyst...",
            "user_prompt": "Analyze the book...",
            "model_id": "gpt-3.5-turbo",
            "temperature": 0.5,
            "max_tokens": 600
        })
        
        mock_db.return_value.__getitem__.return_value = mock_prompts
        
        # Test topic extraction
        topics = await structurer.extract_topics(book_data)
        
        # Verify results
        assert len(topics) == 3
        assert topics[0]["name"] == "Data Systems Fundamentals"
        assert topics[1]["name"] == "Data Storage"
        assert topics[2]["name"] == "Data Processing"
        assert len(topics[0]["subtopics"]) == 3


@pytest.mark.asyncio
async def test_validate_article():
    """Test article validation."""
    
    structurer = ArticleStructurer()
    
    # Test valid article
    valid_article = """# Book Review

## Introduction
This is the introduction section with more than 150 words. It provides an overview of the book and its main themes. The book explores various aspects of data-intensive applications and provides practical guidance for building scalable systems.

## Chapter 1
This chapter covers the fundamentals of data systems. It discusses reliability, scalability, and maintainability in detail. These are the core principles that every data engineer should understand.

### Subsection 1.1
This subsection delves deeper into reliability patterns and best practices for ensuring system uptime.

### Subsection 1.2
Here we explore scalability techniques and how to design systems that can handle growing loads.

## Chapter 2
This chapter focuses on data storage technologies and their trade-offs for different use cases.

## Chapter 3
Data processing techniques are covered in this chapter, including both stream and batch processing.

## Context and Motivation
This section explains why this book is important and relevant in today's technology landscape.

## Impact and Applicability
The book has significant impact on how we design and build modern data applications.

## Book Details
This section provides metadata about the book including ISBN, publisher, and publication date.

## About the Author
Information about the author's background, expertise, and other notable works.

## Download & Links
Links to purchase or download the book from various platforms.

## Related Subjects
Additional topics and resources related to the book's content for further reading."""
    
    validation = await structurer.validate_article(valid_article)
    
    # Check validation results
    assert validation["is_valid"] == True
    assert validation["word_count"] > 0
    assert validation["section_counts"]["h1"] == 1
    assert validation["section_counts"]["h2"] >= 8
    assert validation["section_counts"]["h3"] >= 2


@pytest.mark.asyncio
async def test_validate_article_invalid_word_count():
    """Test article validation with invalid word count."""
    
    structurer = ArticleStructurer()
    
    # Test article with too few words
    short_article = """# Book Review

## Introduction
This is too short.

## Chapter 1
Not enough content."""
    
    validation = await structurer.validate_article(short_article)
    
    # Should fail validation
    assert validation["is_valid"] == False
    assert "Word count too low" in validation["errors"][0]


@pytest.mark.asyncio
async def test_validate_article_invalid_structure():
    """Test article validation with invalid structure."""
    
    structurer = ArticleStructurer()
    
    # Test article with wrong heading structure
    invalid_article = """# Book Review

## Chapter 1
Content here.

## Chapter 2
More content."""  # Missing required sections
    
    validation = await structurer.validate_article(invalid_article)
    
    # Should fail validation
    assert validation["is_valid"] == False
    assert any("Expected at least 8 H2 sections" in error for error in validation["errors"])


@pytest.mark.asyncio
async def test_structure_article():
    """Test article structure generation."""
    
    # Mock book data
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "metadata": {}
    }
    
    # Mock topics
    topics = [
        {"name": "Topic 1", "description": "Description 1", "subtopics": ["Sub1", "Sub2"]},
        {"name": "Topic 2", "description": "Description 2", "subtopics": ["Sub3", "Sub4"]},
        {"name": "Topic 3", "description": "Description 3", "subtopics": ["Sub5", "Sub6"]},
    ]
    
    # Mock context
    context = "This is the context for the book."
    
    # Mock LLM response
    mock_article = """# Test Book Review

## Topic 1
Content for topic 1.

## Topic 2
Content for topic 2.

## Topic 3
Content for topic 3.

## Introduction to Book Topic
Introduction content.

## Context and Motivation
Context content.

## Impact and Applicability
Impact content.

## Book Details
Book details.

## About the Author
Author info.

## Download & Links
Links.

## Related Subjects
Related subjects."""
    
    # Create ArticleStructurer with mocked LLM client
    structurer = ArticleStructurer()
    structurer.llm_client = MagicMock()
    structurer.llm_client.generate = AsyncMock(return_value=mock_article)
    
    # Mock database
    with patch('src.workers.article_structurer.get_database') as mock_db:
        mock_prompts = MagicMock()
        mock_prompts.find_one = AsyncMock(return_value={
            "name": "SEO-Optimized Article Writer",
            "system_prompt": "You are an expert...",
            "user_prompt": "Write a comprehensive...",
            "model_id": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 2500
        })
        
        mock_db.return_value.__getitem__.return_value = mock_prompts
        
        # Test article generation
        article = await structurer.structure_article(book_data, topics, context)
        
        # Verify structure
        assert article.startswith("#")
        assert "##" in article
        assert "Topic 1" in article
        assert "Topic 2" in article
        assert "Topic 3" in article


@pytest.mark.asyncio
async def test_generate_valid_article():
    """Test complete article generation with validation."""
    
    # Mock book data
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "metadata": {},
        "context": "Context for the book."
    }
    
    # Mock valid article that will pass validation
    mock_valid_article = """# Test Book Review

## Topic 1
This is a comprehensive section with more than 200 words. It covers the first main topic of the book in detail, providing insights and analysis that readers will find valuable. The section is well-structured with multiple paragraphs.

### Subsection 1.1
This subsection explores specific aspects of Topic 1.

### Subsection 1.2
Additional details about Topic 1 are covered here.

## Topic 2
This section covers the second main topic with over 200 words of content. It provides a thorough examination of the subject matter and includes practical examples.

### Subsection 2.1
Specific aspects of Topic 2 are discussed here.

### Subsection 2.2
More details about Topic 2 can be found in this subsection.

## Topic 3
The third main topic is covered in this section with comprehensive analysis.

## Introduction to Book Topic
This section provides an introduction to the book's main topic.

## Context and Motivation
Here we discuss the context and motivation behind the book.

## Impact and Applicability
This section covers the impact and applicability of the book's content.

## Book Details
Metadata and details about the book publication.

## About the Author
Information about the author's background and expertise.

## Download & Links
Links to purchase or download the book.

## Related Subjects
Additional topics related to the book's content."""
    
    # Create ArticleStructurer with mocked methods
    structurer = ArticleStructurer()
    structurer.extract_topics = AsyncMock(return_value=[
        {"name": "Topic 1", "description": "Desc 1", "subtopics": []},
        {"name": "Topic 2", "description": "Desc 2", "subtopics": []},
        {"name": "Topic 3", "description": "Desc 3", "subtopics": []},
    ])
    structurer.structure_article = AsyncMock(return_value=mock_valid_article)
    structurer.validate_article = AsyncMock(return_value={
        "is_valid": True,
        "errors": [],
        "word_count": 1000
    })
    
    # Test article generation
    article = await structurer.generate_valid_article(book_data, book_data["context"], max_retries=3)
    
    # Verify that methods were called
    structurer.extract_topics.assert_called_once()
    structurer.structure_article.assert_called_once()
    structurer.validate_article.assert_called_once()
    
    # Verify result
    assert article == mock_valid_article


@pytest.mark.asyncio
async def test_generate_valid_article_with_retry():
    """Test article generation with retry on validation failure."""
    
    # Mock book data
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "metadata": {},
        "context": "Context for the book."
    }
    
    # Mock invalid article (first attempt)
    mock_invalid_article = """# Test Book Review

## Topic 1
Too short.

## Topic 2
Also too short."""
    
    # Mock valid article (second attempt)
    mock_valid_article = """# Test Book Review

## Topic 1
This is a comprehensive section with more than 200 words. It covers the first main topic of the book in detail.

## Topic 2
This section covers the second main topic with over 200 words of content.

## Topic 3
The third main topic is covered in this section with comprehensive analysis.

## Introduction to Book Topic
This section provides an introduction to the book's main topic.

## Context and Motivation
Here we discuss the context and motivation behind the book.

## Impact and Applicability
This section covers the impact and applicability of the book's content.

## Book Details
Metadata and details about the book publication.

## About the Author
Information about the author's background and expertise.

## Download & Links
Links to purchase or download the book.

## Related Subjects
Additional topics related to the book's content."""
    
    # Create ArticleStructurer with mocked methods
    structurer = ArticleStructurer()
    structurer.extract_topics = AsyncMock(return_value=[
        {"name": "Topic 1", "description": "Desc 1", "subtopics": []},
        {"name": "Topic 2", "description": "Desc 2", "subtopics": []},
        {"name": "Topic 3", "description": "Desc 3", "subtopics": []},
    ])
    
    # Mock structure_article to return invalid article first, then valid
    structurer.structure_article = AsyncMock(side_effect=[mock_invalid_article, mock_valid_article])
    
    # Mock validate_article to fail first, then pass
    structurer.validate_article = AsyncMock(side_effect=[
        {
            "is_valid": False,
            "errors": ["Word count too low"],
            "word_count": 100
        },
        {
            "is_valid": True,
            "errors": [],
            "word_count": 1000
        }
    ])
    
    # Test article generation with retry
    article = await structurer.generate_valid_article(book_data, book_data["context"], max_retries=2)
    
    # Verify that methods were called multiple times
    assert structurer.structure_article.call_count == 2
    assert structurer.validate_article.call_count == 2
    
    # Verify that valid article was returned
    assert article == mock_valid_article


@pytest.mark.asyncio
async def test_generate_valid_article_max_retries():
    """Test article generation failure after max retries."""
    
    # Mock book data
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "metadata": {},
        "context": "Context for the book."
    }
    
    # Mock invalid article
    mock_invalid_article = """# Test Book Review

## Topic 1
Too short."""
    
    # Create ArticleStructurer with mocked methods
    structurer = ArticleStructurer()
    structurer.extract_topics = AsyncMock(return_value=[
        {"name": "Topic 1", "description": "Desc 1", "subtopics": []},
    ])
    structurer.structure_article = AsyncMock(return_value=mock_invalid_article)
    structurer.validate_article = AsyncMock(return_value={
        "is_valid": False,
        "errors": ["Word count too low", "Expected at least 8 H2 sections"],
        "word_count": 50
    })
    
    # Test that max retries raises exception
    with pytest.raises(ValueError, match="Failed to generate valid article after 2 attempts"):
        await structurer.generate_valid_article(book_data, book_data["context"], max_retries=2)