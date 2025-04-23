import io
from typing import Any, Dict, List, Optional, Sequence
import PyPDF2

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader


class PDFLoader(BaseLoader):
    """Loads a PDF with PyPDF2 and chunks at character level.

    Loader also stores page numbers in metadata.
    """

    def __init__(
            self,
            contents: Any,
            file_path: str = "",
    ):
        """

        Args:
            file_path: The path to the file to load.
            password: The password for the PDF file. Optional. Defaults to None.
        """
        self.contents = contents
        self.file_path = file_path

    def load(self) -> List[Document]:
        """Load data into document objects."""
        docs = []
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(self.contents))
            docs = [
                Document(
                    page_content=page.extract_text(),
                    metadata={"source": self.file_path, "page": page_number},
                )
                for page_number, page in enumerate(pdf_reader.pages)
            ]
        except Exception as e:
            raise RuntimeError(f"Error loading {self.file_path}") from e

        return docs