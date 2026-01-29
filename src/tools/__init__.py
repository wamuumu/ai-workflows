"""
Tools Package
=============

This package provides the tool system for AI workflows, including tool
definitions, registration, and execution infrastructure.

Core Components:
    - tool.py: Tool class and ToolType enum definitions
    - registry.py: ToolRegistry for tool discovery and management
    - decorator.py: @tool decorator for easy tool registration

Tool Categories:
    The package includes subpackages for different tool categories:
    - weather: Weather data and forecasts
    - travel: Flight, hotel, and route planning
    - finance: Stock prices and financial data
    - web: Web scraping and API calls
    - text: Text processing and translation
    - math: Mathematical computations
    - news: News retrieval
    - documents: Document processing
    - ml: Machine learning operations
    - macro: Composite/macro tools
    - communication: Email and notifications

Usage Example:
    >>> from tools.registry import ToolRegistry
    >>> tool = ToolRegistry.get("get_weather")
    >>> result = tool.run(city="London", unit="celsius")
"""