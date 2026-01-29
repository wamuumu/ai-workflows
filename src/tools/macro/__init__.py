"""
Macro Tools Package
===================

This package provides composite/macro tools that combine multiple atomic
tools to perform complex tasks in a single call.

Main Responsibilities:
    - Reduce workflow complexity for common multi-step operations
    - Demonstrate atomic vs macro tool selection tradeoffs
    - Provide high-level abstractions over atomic tool combinations

Available Macro Tools:
    - plan_trip: Weather + attractions + activities
    - analyze_stock_with_news: Stock price + news + sentiment
    - process_text_multilingual: Clean + translate + sentiment
    - research_topic: Web search + news search
    - analyze_documents_batch: File listing + reading + sentiment

Design Philosophy:
    Macro tools trade off flexibility for convenience. They are useful
    when the combination of atomic operations is common and well-defined,
    but may be less suitable for novel or customized workflows.
"""

from tools.macro.composite import (
    plan_trip,
    analyze_stock_with_news,
    process_text_multilingual,
    research_topic,
    analyze_documents_batch,
)