# File: app/tech_content/__init__.py
"""
Technical Content Enhancer Module

Provides automatic enhancement of technical responses with:
- Mermaid diagrams for architecture and workflows
- Comparison tables for technical choices
- Code examples for implementation guidance
- Technical specifications tables
"""
from app.tech_content.enhancer import (
    TechnicalDomain,
    TechnicalContent,
    detect_technical_domain,
    generate_mermaid_diagram,
    generate_comparison_table,
    generate_code_example,
    generate_specifications,
    enhance_technical_response,
    format_enhanced_response,
    should_enhance,
)

__all__ = [
    "TechnicalDomain",
    "TechnicalContent",
    "detect_technical_domain",
    "generate_mermaid_diagram",
    "generate_comparison_table",
    "generate_code_example",
    "generate_specifications",
    "enhance_technical_response",
    "format_enhanced_response",
    "should_enhance",
]