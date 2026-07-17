from app.ingestion.parsers import file_parser_registry
from app.ingestion.parsers.pdf_parser import pdf_parser
from app.ingestion.parsers.docx_parser import docx_parser
from app.ingestion.parsers.image_parser import image_parser


def register_all_parsers():
    """Register all file type parsers into the global registry."""
    file_parser_registry.register("application/pdf", pdf_parser)
    file_parser_registry.register("application/vnd.openxmlformats-officedocument.wordprocessingml.document", docx_parser)
    file_parser_registry.register("application/msword", docx_parser)  # .doc fallback
    file_parser_registry.register("image/*", image_parser)


register_all_parsers()
