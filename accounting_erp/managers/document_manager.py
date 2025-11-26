#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Document Manager
File attachment and document management
"""

import logging
import os
import shutil
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import mimetypes

logger = logging.getLogger(__name__)

class DocumentManager:
    """File attachment and document management"""

    def __init__(self, storage_path: str = "attachments"):
        """
        Initialize Document Manager

        Args:
            storage_path: Base storage path for documents
        """
        self.storage_path = storage_path
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = {
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
            # Documents
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.txt', '.rtf', '.odt', '.ods', '.odp',
            # Archives
            '.zip', '.rar', '.7z', '.tar', '.gz',
            # Other
            '.csv', '.json', '.xml', '.html', '.htm'
        }

        # Ensure storage directories exist
        os.makedirs(storage_path, exist_ok=True)
        os.makedirs(os.path.join(storage_path, 'temp'), exist_ok=True)
        os.makedirs(os.path.join(storage_path, 'thumbnails'), exist_ok=True)

        logger.info(f"Document Manager initialized with storage path: {storage_path}")

    def upload_document(self, file_data: bytes, original_filename: str,
                      entry_id: Optional[int] = None, account_id: Optional[int] = None,
                      description: Optional[str] = None, uploaded_by: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Upload document and save to storage

        Args:
            file_data: Raw file data
            original_filename: Original filename
            entry_id: Journal entry ID
            account_id: Account ID
            description: File description
            uploaded_by: User ID who uploaded

        Returns:
            Document information or None if failed
        """
        try:
            # Validate inputs
            if not file_data or not original_filename:
                logger.error("File data and filename are required")
                return None

            # Validate file size
            if len(file_data) > self.max_file_size:
                logger.error(f"File too large: {len(file_data)} bytes (max: {self.max_file_size})")
                return None

            # Validate file extension
            file_ext = Path(original_filename).suffix.lower()
            if file_ext not in self.allowed_extensions:
                logger.error(f"File extension not allowed: {file_ext}")
                return None

            # Generate unique filename
            file_id = str(uuid.uuid4())
            safe_filename = self.generate_safe_filename(file_id, original_filename)
            file_path = os.path.join(self.storage_path, safe_filename)

            # Calculate file hash for integrity checking
            file_hash = hashlib.sha256(file_data).hexdigest()

            # Check for duplicates by hash
            existing_doc = self.find_document_by_hash(file_hash)
            if existing_doc:
                logger.info(f"Document already exists: {existing_doc['filename']}")
                return existing_doc

            # Save file to storage
            with open(file_path, 'wb') as f:
                f.write(file_data)

            # Generate thumbnail if it's an image
            thumbnail_path = None
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                thumbnail_path = self.generate_thumbnail(file_path, file_id)

            # Get MIME type
            mime_type, _ = mimetypes.guess_type(original_filename)

            # Prepare document data
            document_info = {
                'entry_id': entry_id,
                'account_id': account_id,
                'filename': safe_filename,
                'original_filename': original_filename,
                'file_path': file_path,
                'file_size': len(file_data),
                'file_hash': file_hash,
                'mime_type': mime_type,
                'thumbnail_path': thumbnail_path,
                'description': description,
                'uploaded_at': datetime.now(),
                'uploaded_by': uploaded_by
            }

            return document_info

        except Exception as e:
            logger.error(f"Failed to upload document: {e}")
            return None

    def generate_safe_filename(self, file_id: str, original_filename: str) -> str:
        """Generate safe filename for storage"""
        try:
            # Extract file extension
            file_ext = Path(original_filename).suffix.lower()

            # Remove special characters from original name
            safe_name = ''.join(c for c in Path(original_filename).stem if c.isalnum() or c in (' ', '-', '_')).rstrip()

            # Limit length
            safe_name = safe_name[:50] if len(safe_name) > 50 else safe_name

            # Combine with UUID and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"{timestamp}_{file_id}_{safe_name}{file_ext}"

        except Exception as e:
            logger.error(f"Failed to generate safe filename: {e}")
            # Fallback to UUID only
            return f"{file_id}_{original_filename}"

    def generate_thumbnail(self, file_path: str, file_id: str) -> Optional[str]:
        """Generate thumbnail for image files"""
        try:
            from PIL import Image

            # Open image
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Create thumbnail
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)

                # Save thumbnail
                thumbnail_filename = f"thumb_{file_id}.jpg"
                thumbnail_path = os.path.join(self.storage_path, 'thumbnails', thumbnail_filename)
                img.save(thumbnail_path, 'JPEG', quality=85)

                return thumbnail_path

        except ImportError:
            logger.warning("PIL not available for thumbnail generation")
            return None
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return None

    def find_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Find document by file hash"""
        try:
            query = "SELECT * FROM attachments WHERE file_hash = ? LIMIT 1"
            result = self.db_manager.execute_query(query, (file_hash,), fetch_one=True)
            return result

        except Exception as e:
            logger.error(f"Failed to find document by hash: {e}")
            return None

    def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Get document information by ID

        Args:
            document_id: Document ID

        Returns:
            Document information
        """
        try:
            query = """
                SELECT a.*, u.username as uploaded_by_name
                FROM attachments a
                LEFT JOIN users u ON a.uploaded_by = u.id
                WHERE a.id = ?
            """
            result = self.db_manager.execute_query(query, (document_id,), fetch_one=True)
            return result

        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None

    def get_document_content(self, document_id: int) -> Optional[bytes]:
        """
        Get document file content

        Args:
            document_id: Document ID

        Returns:
            File content as bytes
        """
        try:
            document = self.get_document(document_id)
            if not document:
                logger.error(f"Document not found: {document_id}")
                return None

            if os.path.exists(document['file_path']):
                with open(document['file_path'], 'rb') as f:
                    return f.read()
            else:
                logger.error(f"File not found: {document['file_path']}")
                return None

        except Exception as e:
            logger.error(f"Failed to get document content: {e}")
            return None

    def get_document_thumbnail(self, document_id: int) -> Optional[bytes]:
        """
        Get document thumbnail

        Args:
            document_id: Document ID

        Returns:
            Thumbnail content as bytes
        """
        try:
            document = self.get_document(document_id)
            if not document or not document.get('thumbnail_path'):
                return None

            if os.path.exists(document['thumbnail_path']):
                with open(document['thumbnail_path'], 'rb') as f:
                    return f.read()
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to get document thumbnail: {e}")
            return None

    def delete_document(self, document_id: int) -> bool:
        """
        Delete document and its files

        Args:
            document_id: Document ID

        Returns:
            True if deleted successfully
        """
        try:
            document = self.get_document(document_id)
            if not document:
                logger.error(f"Document not found: {document_id}")
                return False

            # Delete from database
            affected_rows = self.db_manager.delete_record('attachments', 'id = ?', (document_id,))

            if affected_rows > 0:
                # Delete files
                if os.path.exists(document['file_path']):
                    os.remove(document['file_path'])

                if document.get('thumbnail_path') and os.path.exists(document['thumbnail_path']):
                    os.remove(document['thumbnail_path'])

                logger.info(f"Document deleted: {document_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False

    def search_documents(self, query: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search for documents

        Args:
            query: Search query
            filters: Additional filters

        Returns:
            List of matching documents
        """
        try:
            # Base query
            sql_query = """
                SELECT a.*, u.username as uploaded_by_name
                FROM attachments a
                LEFT JOIN users u ON a.uploaded_by = u.id
                WHERE 1=1
            """

            params = []

            # Add search conditions
            if query:
                sql_query += """
                    AND (a.original_filename LIKE ? OR a.description LIKE ?)
                """
                search_param = f"%{query}%"
                params.extend([search_param, search_param])

            # Add filters
            if filters:
                if 'entry_id' in filters:
                    sql_query += " AND a.entry_id = ?"
                    params.append(filters['entry_id'])

                if 'account_id' in filters:
                    sql_query += " AND a.account_id = ?"
                    params.append(filters['account_id'])

                if 'mime_type' in filters:
                    sql_query += " AND a.mime_type LIKE ?"
                    params.append(f"%{filters['mime_type']}%")

                if 'uploaded_by' in filters:
                    sql_query += " AND a.uploaded_by = ?"
                    params.append(filters['uploaded_by'])

                if 'date_from' in filters:
                    sql_query += " AND a.uploaded_at >= ?"
                    params.append(filters['date_from'])

                if 'date_to' in filters:
                    sql_query += " AND a.uploaded_at <= ?"
                    params.append(filters['date_to'])

            sql_query += " ORDER BY a.uploaded_at DESC"

            results = self.db_manager.execute_query(sql_query, tuple(params), fetch_all=True)
            return results or []

        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []

    def get_entry_documents(self, entry_id: int) -> List[Dict[str, Any]]:
        """
        Get all documents for a journal entry

        Args:
            entry_id: Journal entry ID

        Returns:
            List of documents
        """
        try:
            query = """
                SELECT a.*, u.username as uploaded_by_name
                FROM attachments a
                LEFT JOIN users u ON a.uploaded_by = u.id
                WHERE a.entry_id = ?
                ORDER BY a.uploaded_at DESC
            """
            results = self.db_manager.execute_query(query, (entry_id,), fetch_all=True)
            return results or []

        except Exception as e:
            logger.error(f"Failed to get entry documents: {e}")
            return []

    def get_account_documents(self, account_id: int) -> List[Dict[str, Any]]:
        """
        Get all documents for an account

        Args:
            account_id: Account ID

        Returns:
            List of documents
        """
        try:
            query = """
                SELECT a.*, u.username as uploaded_by_name
                FROM attachments a
                LEFT JOIN users u ON a.uploaded_by = u.id
                WHERE a.account_id = ?
                ORDER BY a.uploaded_at DESC
            """
            results = self.db_manager.execute_query(query, (account_id,), fetch_all=True)
            return results or []

        except Exception as e:
            logger.error(f"Failed to get account documents: {e}")
            return []

    def virus_scan(self, file_path: str) -> bool:
        """
        Scan file for viruses (placeholder implementation)

        Args:
            file_path: Path to file to scan

        Returns:
            True if file is safe
        """
        try:
            # This would integrate with antivirus software
            # For now, just check file size and basic validation
            if not os.path.exists(file_path):
                return False

            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return False

            # Additional basic checks could be added here
            return True

        except Exception as e:
            logger.error(f"Failed to scan file: {e}")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics

        Returns:
            Storage statistics
        """
        try:
            stats = {
                'total_documents': 0,
                'total_size': 0,
                'by_type': {},
                'by_date': {},
                'storage_path': self.storage_path
            }

            # Get documents from database
            query = "SELECT file_size, mime_type, uploaded_at FROM attachments"
            documents = self.db_manager.execute_query(query, fetch_all=True)

            for doc in documents or []:
                stats['total_documents'] += 1
                stats['total_size'] += doc.get('file_size', 0)

                # Group by type
                mime_type = doc.get('mime_type', 'unknown')
                if mime_type in stats['by_type']:
                    stats['by_type'][mime_type] += 1
                else:
                    stats['by_type'][mime_type] = 1

                # Group by date
                if 'uploaded_at' in doc and doc['uploaded_at']:
                    date_key = doc['uploaded_at'].strftime('%Y-%m')
                    if date_key in stats['by_date']:
                        stats['by_date'][date_key] += 1
                    else:
                        stats['by_date'][date_key] = 1

            return stats

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}

    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up temporary files

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of files deleted
        """
        try:
            temp_dir = os.path.join(self.storage_path, 'temp')
            if not os.path.exists(temp_dir):
                return 0

            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            deleted_count = 0

            for file_path in Path(temp_dir).glob('*'):
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete temp file {file_path}: {e}")

            logger.info(f"Cleaned up {deleted_count} temporary files")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
            return 0

    def compress_old_documents(self, days_threshold: int = 365) -> int:
        """
        Compress old documents to save space

        Args:
            days_threshold: Age threshold in days

        Returns:
            Number of files compressed
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_threshold)
            compressed_count = 0

            query = """
                SELECT id, file_path, original_filename
                FROM attachments
                WHERE uploaded_at < ?
                AND file_path NOT LIKE '%.zip'
            """
            old_documents = self.db_manager.execute_query(query, (cutoff_date,), fetch_all=True)

            for doc in old_documents or []:
                try:
                    file_path = doc['file_path']
                    if os.path.exists(file_path):
                        # Create ZIP archive
                        zip_path = file_path + '.zip'
                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            zipf.write(file_path, doc['original_filename'])

                        # Verify ZIP file and delete original
                        if os.path.exists(zip_path) and os.path.getsize(zip_path) > 0:
                            os.remove(file_path)
                            compressed_count += 1
                            logger.info(f"Compressed old document: {doc['id']}")

                except Exception as e:
                    logger.error(f"Failed to compress document {doc['id']}: {e}")

            logger.info(f"Compressed {compressed_count} old documents")
            return compressed_count

        except Exception as e:
            logger.error(f"Failed to compress old documents: {e}")
            return 0

    @property
    def db_manager(self):
        """Get database manager (to be injected)"""
        # This should be injected when the DocumentManager is created
        # For now, we'll assume it's available as a global or passed instance
        if not hasattr(self, '_db_manager'):
            # Try to get from parent or global scope
            import sys
            # This is a temporary solution - proper dependency injection should be used
            pass
        return getattr(self, '_db_manager', None)

    @db_manager.setter
    def db_manager(self, db_manager):
        """Set database manager"""
        self._db_manager = db_manager