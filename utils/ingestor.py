from __future__ import annotiations

import os
import base64
import uuid, time

from langchain_community.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document
from qdrant_client import models



