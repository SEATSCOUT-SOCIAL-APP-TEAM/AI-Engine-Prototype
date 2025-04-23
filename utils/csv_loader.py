import csv
import io
from typing import Any, Dict, List, Optional, Sequence

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader


class CSVLoader(BaseLoader):
    """Load a `CSV` file into a list of Documents.

    Each document represents one row of the CSV file. Every row is converted into a
    key/value pair and outputted to a new line in the document's page_content.

    The source for each document loaded from csv is set to the value of the
    `file_path` argument for all documents by default.
    You can override this by setting the `source_column` argument to the
    name of a column in the CSV file.
    The source of each document will then be set to the value of the column
    with the name specified in `source_column`.

    Output Example:
        .. code-block:: txt

            column1: value1
            column2: value2
            column3: value3
    """

    def __init__(
            self,
            contents: Any,
            file_path: str = "",
            source_column: Optional[str] = None,
            metadata_columns: Sequence[str] = (),
            csv_args: Optional[Dict] = None,
            encoding: Optional[str] = None,
    ):
        """

        Args:
            source_column: The name of the column in the CSV file to use as the source.
              Optional. Defaults to None.
            metadata_columns: A sequence of column names to use as metadata. Optional.
            csv_args: A dictionary of arguments to pass to the csv.DictReader.
              Optional. Defaults to None.
            encoding: The encoding of the CSV file. Optional. Defaults to None.
            autodetect_encoding: Whether to try to autodetect the file encoding.
        """
        self.contents = contents
        self.file_path = file_path
        self.source_column = source_column
        self.metadata_columns = metadata_columns
        self.encoding = encoding
        self.csv_args = csv_args or {}

    def load(self) -> List[Document]:
        """Load data into document objects."""
        docs = []
        try:
            self.contents = self.contents.decode(self.encoding or "utf-8")
            docs = self.__read_file(self.contents)
        except Exception as e:
            raise RuntimeError(f"Error loading {self.file_path}") from e

        return docs

    def __read_file(self, csvfile) -> List[Document]:
        docs = []

        contents = csvfile.split('\n')[1:]

        # csv_reader = csv.DictReader(csvfile, **self.csv_args)  # type: ignore
        # for i, row in enumerate(csv_reader):
        #     try:
        #         source = (
        #             row[self.source_column]
        #             if self.source_column is not None
        #             else self.file_path
        #         )
        #     except KeyError:
        #         raise ValueError(
        #             f"Source column '{self.source_column}' not found in CSV file."
        #         )

        for i, row in enumerate(contents):
            # content = "\n".join(
            #     f"{k.strip()}: {v.strip() if v is not None else v}"
            #     for k, v in row.items()
            #     if k not in self.metadata_columns
            # )
            # metadata = {"source": source, "row": i}
            # for col in self.metadata_columns:
            #     try:
            #         metadata[col] = row[col]
            #     except KeyError:
            #         raise ValueError(f"Metadata column '{col}' not found in CSV file.")
            # doc = Document(page_content=content, metadata=metadata)
            doc = Document(page_content=row)
            docs.append(doc)
        return docs
