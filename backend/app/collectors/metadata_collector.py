"""
Metadata Collector - Advanced Document Metadata Extraction
Searches for public documents in a domain and extracts forensic metadata
"""

import io
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

import httpx
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
import olefile

from app.collectors.base import BaseCollector
from app.models.schemas import CollectorResult

try:
    from googlesearch import search as google_search
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

logger = logging.getLogger(__name__)


class MetadataCollector(BaseCollector):
    """
    Advanced forensic collector for document metadata extraction.
    
    Searches for public documents (PDF, DOCX, XLSX) in a target domain
    and extracts metadata like authors, creation dates, software used, etc.
    
    Useful for:
    - Identifying employees/users
    - Software fingerprinting
    - Timeline reconstruction
    - Information leakage detection
    """
    
    SUPPORTED_FILETYPES = ['pdf', 'docx', 'xlsx', 'doc', 'xls']
    MAX_RESULTS = 5  # Limit to prevent slow searches
    TIMEOUT = 10.0
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max per file
    
    # User-Agent to avoid bot detection
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )
    
    async def collect(self, target: str) -> CollectorResult:
        """
        Collect document metadata from a target domain.
        
        Args:
            target: Domain to search (e.g., "example.com")
            
        Returns:
            CollectorResult with document metadata and potential users
        """
        if not GOOGLE_AVAILABLE:
            return self._generate_result(
                target=target,
                success=False,
                data={},
                error="googlesearch-python not installed. Install with: pip install googlesearch-python"
            )
        
        domain = self._sanitize_domain(target)
        
        try:
            # Phase 1: Search for documents
            logger.info(f"Searching for documents in {domain}")
            document_urls = await self._search_documents(domain)
            
            if not document_urls:
                return self._generate_result(
                    target=domain,
                    success=True,
                    data={
                        "domain": domain,
                        "documents_found": 0,
                        "documents": [],
                        "potential_users": []
                    },
                    metadata={
                        "search_query": self._build_search_query(domain),
                        "filetypes": self.SUPPORTED_FILETYPES
                    }
                )
            
            # Phase 2: Download and extract metadata
            logger.info(f"Found {len(document_urls)} documents, extracting metadata...")
            documents_with_metadata = []
            potential_users = set()
            
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.TIMEOUT),
                headers={"User-Agent": self.USER_AGENT},
                follow_redirects=True
            ) as client:
                for url in document_urls:
                    try:
                        metadata = await self._process_document(client, url)
                        if metadata:
                            documents_with_metadata.append(metadata)
                            
                            # Extract potential users from author fields
                            if metadata.get('author'):
                                potential_users.add(metadata['author'])
                            if metadata.get('creator'):
                                potential_users.add(metadata['creator'])
                            
                    except Exception as e:
                        logger.warning(f"Failed to process {url}: {e}")
                        continue
            
            return self._generate_result(
                target=domain,
                success=True,
                data={
                    "domain": domain,
                    "documents_found": len(documents_with_metadata),
                    "documents": documents_with_metadata,
                    "potential_users": sorted(list(potential_users)),
                    "summary": self._generate_summary(documents_with_metadata)
                },
                metadata={
                    "search_query": self._build_search_query(domain),
                    "filetypes_searched": self.SUPPORTED_FILETYPES,
                    "max_results": self.MAX_RESULTS,
                    "total_urls_found": len(document_urls)
                }
            )
            
        except Exception as e:
            logger.error(f"MetadataCollector error: {e}")
            return self._generate_result(
                target=domain,
                success=False,
                data={},
                error=f"Collection failed: {str(e)}"
            )
    
    def _sanitize_domain(self, target: str) -> str:
        """Remove protocol and path from domain"""
        domain = target.strip().lower()
        domain = re.sub(r'^https?://', '', domain)
        domain = domain.split('/')[0]
        return domain
    
    def _build_search_query(self, domain: str) -> str:
        """Build Google dork query for document search"""
        filetypes = ' OR '.join([f'filetype:{ft}' for ft in self.SUPPORTED_FILETYPES])
        return f'site:{domain} ({filetypes})'
    
    async def _search_documents(self, domain: str) -> List[str]:
        """
        Search for documents using Google dork.
        
        Note: googlesearch-python is synchronous, so we run it directly
        """
        query = self._build_search_query(domain)
        document_urls = []
        
        try:
            # googlesearch returns generator, convert to list with limit
            results = google_search(query, num_results=self.MAX_RESULTS, advanced=True)
            
            for result in results:
                # result can be a string URL or SearchResult object
                url = result.url if hasattr(result, 'url') else str(result)
                document_urls.append(url)
                
                if len(document_urls) >= self.MAX_RESULTS:
                    break
            
            logger.info(f"Found {len(document_urls)} document URLs")
            
        except Exception as e:
            logger.error(f"Google search failed: {e}")
        
        return document_urls
    
    async def _process_document(
        self,
        client: httpx.AsyncClient,
        url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Download document in memory and extract metadata.
        
        Args:
            client: HTTP client
            url: Document URL
            
        Returns:
            Dictionary with document metadata or None if failed
        """
        try:
            # Download file in memory
            logger.debug(f"Downloading {url}")
            response = await client.get(url)
            
            if response.status_code != 200:
                logger.warning(f"Failed to download {url}: HTTP {response.status_code}")
                return None
            
            # Check file size
            content_length = len(response.content)
            if content_length > self.MAX_FILE_SIZE:
                logger.warning(f"File too large: {url} ({content_length} bytes)")
                return None
            
            # Detect file type from URL or content-type
            filetype = self._detect_filetype(url, response.headers.get('content-type', ''))
            
            # Extract metadata based on file type
            file_stream = io.BytesIO(response.content)
            
            if filetype == 'pdf':
                metadata = self._extract_pdf_metadata(file_stream)
            elif filetype in ['docx', 'doc']:
                metadata = self._extract_docx_metadata(file_stream)
            elif filetype in ['xlsx', 'xls']:
                metadata = self._extract_office_metadata(file_stream)
            else:
                logger.warning(f"Unsupported file type: {filetype}")
                return None
            
            # Add URL and file info
            metadata['url'] = url
            metadata['filetype'] = filetype
            metadata['size_bytes'] = content_length
            
            return metadata
            
        except httpx.TimeoutException:
            logger.warning(f"Timeout downloading {url}")
            return None
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return None
    
    def _detect_filetype(self, url: str, content_type: str) -> str:
        """Detect file type from URL or Content-Type header"""
        url_lower = url.lower()
        
        for ft in self.SUPPORTED_FILETYPES:
            if url_lower.endswith(f'.{ft}'):
                return ft
        
        # Try content-type
        content_type_lower = content_type.lower()
        if 'pdf' in content_type_lower:
            return 'pdf'
        elif 'wordprocessingml' in content_type_lower or 'msword' in content_type_lower:
            return 'docx'
        elif 'spreadsheetml' in content_type_lower or 'excel' in content_type_lower:
            return 'xlsx'
        
        return 'unknown'
    
    def _extract_pdf_metadata(self, file_stream: io.BytesIO) -> Dict[str, Any]:
        """Extract metadata from PDF using PyPDF2"""
        metadata = {}
        
        try:
            reader = PdfReader(file_stream)
            pdf_metadata = reader.metadata
            
            if pdf_metadata:
                # Common PDF metadata fields
                metadata['author'] = self._sanitize_string(pdf_metadata.get('/Author', ''))
                metadata['creator'] = self._sanitize_string(pdf_metadata.get('/Creator', ''))
                metadata['producer'] = self._sanitize_string(pdf_metadata.get('/Producer', ''))
                metadata['subject'] = self._sanitize_string(pdf_metadata.get('/Subject', ''))
                metadata['title'] = self._sanitize_string(pdf_metadata.get('/Title', ''))
                
                # Parse dates
                creation_date = pdf_metadata.get('/CreationDate', '')
                if creation_date:
                    metadata['creation_date'] = self._parse_pdf_date(creation_date)
                
                mod_date = pdf_metadata.get('/ModDate', '')
                if mod_date:
                    metadata['modification_date'] = self._parse_pdf_date(mod_date)
            
            metadata['page_count'] = len(reader.pages)
            
        except Exception as e:
            logger.error(f"PDF metadata extraction failed: {e}")
            metadata['error'] = str(e)
        
        return metadata
    
    def _extract_docx_metadata(self, file_stream: io.BytesIO) -> Dict[str, Any]:
        """Extract metadata from DOCX using python-docx"""
        metadata = {}
        
        try:
            doc = DocxDocument(file_stream)
            core_props = doc.core_properties
            
            metadata['author'] = self._sanitize_string(core_props.author or '')
            metadata['title'] = self._sanitize_string(core_props.title or '')
            metadata['subject'] = self._sanitize_string(core_props.subject or '')
            metadata['creator'] = self._sanitize_string(core_props.last_modified_by or '')
            
            if core_props.created:
                metadata['creation_date'] = core_props.created.isoformat()
            if core_props.modified:
                metadata['modification_date'] = core_props.modified.isoformat()
            
            metadata['paragraph_count'] = len(doc.paragraphs)
            
        except Exception as e:
            logger.error(f"DOCX metadata extraction failed: {e}")
            metadata['error'] = str(e)
        
        return metadata
    
    def _extract_office_metadata(self, file_stream: io.BytesIO) -> Dict[str, Any]:
        """Extract metadata from old Office formats (XLS, DOC) using olefile"""
        metadata = {}
        
        try:
            ole = olefile.OleFileIO(file_stream)
            meta = ole.get_metadata()
            
            metadata['author'] = self._sanitize_string(meta.author or '')
            metadata['title'] = self._sanitize_string(meta.title or '')
            metadata['subject'] = self._sanitize_string(meta.subject or '')
            metadata['creator'] = self._sanitize_string(meta.last_saved_by or '')
            
            if meta.create_time:
                metadata['creation_date'] = meta.create_time.isoformat()
            if meta.last_saved_time:
                metadata['modification_date'] = meta.last_saved_time.isoformat()
            
            ole.close()
            
        except Exception as e:
            logger.error(f"Office metadata extraction failed: {e}")
            metadata['error'] = str(e)
        
        return metadata
    
    def _sanitize_string(self, value: str) -> str:
        """Remove strange characters and clean metadata strings"""
        if not value:
            return ''
        
        # Remove null bytes and control characters
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(value))
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else ''
    
    def _parse_pdf_date(self, date_str: str) -> str:
        """
        Parse PDF date format (D:YYYYMMDDHHmmSS) to ISO format.
        Example: D:20230115103045+01'00' -> 2023-01-15T10:30:45
        """
        try:
            # Remove D: prefix and timezone info for simplicity
            date_str = date_str.replace('D:', '')
            date_str = re.sub(r'[+\-].*$', '', date_str)
            
            if len(date_str) >= 14:
                dt = datetime.strptime(date_str[:14], '%Y%m%d%H%M%S')
                return dt.isoformat()
            elif len(date_str) >= 8:
                dt = datetime.strptime(date_str[:8], '%Y%m%d')
                return dt.isoformat()
        except Exception:
            pass
        
        return date_str
    
    def _generate_summary(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from extracted metadata"""
        software_used = set()
        authors = set()
        
        for doc in documents:
            if doc.get('producer'):
                software_used.add(doc['producer'])
            if doc.get('creator'):
                software_used.add(doc['creator'])
            if doc.get('author'):
                authors.add(doc['author'])
        
        return {
            "total_documents": len(documents),
            "unique_authors": len(authors),
            "software_detected": sorted(list(software_used)),
            "filetypes_found": list(set(doc.get('filetype', 'unknown') for doc in documents))
        }
