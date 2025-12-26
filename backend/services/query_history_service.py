"""
Query History Service - Track and Log User Queries

This service provides functionality for logging user queries to the database
for analytics, quality improvement, and user interaction tracking.

Author: AI Assistant
Created: 2025-12-23
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from models.models import QueryHistory, User

logger = logging.getLogger(__name__)


class QueryHistoryService:
    """Service for logging and managing query history."""
    
    # Default citizen user ID (cached for performance)
    CITIZEN_USER_ID = "4b472957-46b0-45c0-a76f-fa093421190b"
    _cached_citizen_user: Optional[User] = None
    
    def get_default_citizen_user(self, db: Session) -> Optional[User]:
        """
        Get or cache the default citizen user.
        
        Args:
            db: Database session
            
        Returns:
            User object or None if not found
        """
        # Return cached user if available
        if self._cached_citizen_user is not None:
            return self._cached_citizen_user
        
        try:
            # Query for citizen user
            user = db.query(User).filter_by(
                id=UUID(self.CITIZEN_USER_ID)
            ).first()
            
            if user:
                # Cache the user for future requests
                self._cached_citizen_user = user
                logger.info(f"Loaded default citizen user: {user.email}")
                return user
            else:
                logger.warning(f"Default citizen user not found: {self.CITIZEN_USER_ID}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading default citizen user: {e}")
            return None
    
    def log_query(
        self,
        db: Session,
        user_id: UUID,
        query: str,
        entities: dict,
        intent: Optional[str],
        results: list,
        rating: Optional[int] = None
    ) -> Optional[QueryHistory]:
        """
        Log a user query to the database.
        
        Args:
            db: Database session
            user_id: UUID of the user who made the query
            query: The query text
            entities: Extracted entities from the query
            intent: Query intent (search, compliance, etc.)
            results: Search/RAG results
            rating: Optional user rating
            
        Returns:
            QueryHistory object if successful, None otherwise
        """
        try:
            # Create query history record
            query_history = QueryHistory(
                user_id=user_id,
                query=query,
                entities=entities or {},
                intent=intent,
                results=results or [],
                rating=rating
            )
            
            # Add to database
            db.add(query_history)
            db.commit()
            db.refresh(query_history)
            
            logger.debug(
                f"Logged query: {query[:50]}... | Intent: {intent} | "
                f"Entities: {len(entities or {})} | Results: {len(results or [])}"
            )
            
            return query_history
            
        except Exception as e:
            logger.error(f"Failed to log query history: {e}")
            db.rollback()
            return None
    
    def format_search_results(self, search_response: dict) -> list:
        """
        Format search results for storage in query history.
        
        Extracts essential information (id, score, title) from search hits
        to keep the stored data manageable.
        
        Args:
            search_response: The search response dictionary
            
        Returns:
            List of formatted result dictionaries
        """
        try:
            formatted_results = []
            
            # Get hits from response
            hits = search_response.get('hits', [])
            
            for hit in hits[:10]:  # Limit to top 10 results
                result = {
                    'id': hit.get('id'),
                    'score': hit.get('score'),
                }
                
                # Extract title from source
                source = hit.get('source', {})
                if 'title' in source:
                    result['title'] = source['title'][:200]  # Truncate long titles
                
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error formatting search results: {e}")
            return []
    
    def format_rag_results(self, rag_answer) -> list:
        """
        Format RAG results for storage in query history.
        
        Extracts source documents with essential information.
        
        Args:
            rag_answer: RAGAnswer object from RAG service
            
        Returns:
            List of formatted result dictionaries
        """
        try:
            formatted_results = []
            
            # Get source documents from RAG answer
            for doc in rag_answer.source_documents[:10]:  # Limit to top 10
                result = {
                    'id': doc.get('id'),
                    'score': doc.get('score'),
                    'title': doc.get('title', '')[:200],  # Truncate long titles
                }
                
                # Add citation if available
                if 'citation' in doc:
                    result['citation'] = doc['citation'][:100]
                
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error formatting RAG results: {e}")
            return []
    
    def extract_entities_from_parsed_query(self, parsed_query) -> dict:
        """
        Extract entities from LegalQueryParser result.
        
        Args:
            parsed_query: ParsedQuery object from query parser
            
        Returns:
            Dictionary of entities grouped by type
        """
        try:
            entities_dict = {}
            
            # Group entities by type
            for entity in parsed_query.entities:
                entity_type = entity.entity_type.value if hasattr(entity.entity_type, 'value') else str(entity.entity_type)
                
                if entity_type not in entities_dict:
                    entities_dict[entity_type] = []
                
                entities_dict[entity_type].append(entity.text)
            
            return entities_dict
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {}
