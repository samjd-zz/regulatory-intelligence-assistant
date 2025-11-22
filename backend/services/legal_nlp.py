"""
Legal NLP Service - Entity Extraction and Text Processing for Regulatory Documents

This module provides natural language processing capabilities specifically designed for
legal and regulatory text, including:
- Legal entity extraction (person types, programs, jurisdictions)
- Named entity recognition (NER) for legal documents
- Text normalization and preprocessing
- Confidence scoring for extracted entities

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Types of legal entities that can be extracted"""
    PERSON_TYPE = "person_type"
    PROGRAM = "program"
    JURISDICTION = "jurisdiction"
    ORGANIZATION = "organization"
    LEGISLATION = "legislation"
    DATE = "date"
    MONEY = "money"
    REQUIREMENT = "requirement"


@dataclass
class ExtractedEntity:
    """Represents an extracted legal entity with metadata"""
    text: str  # Original text of the entity
    entity_type: EntityType  # Type of entity
    normalized: str  # Normalized/canonical form
    confidence: float  # Confidence score (0.0 to 1.0)
    start_pos: int  # Start position in text
    end_pos: int  # End position in text
    context: Optional[str] = None  # Surrounding context
    metadata: Optional[Dict] = None  # Additional metadata

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "text": self.text,
            "entity_type": self.entity_type.value,
            "normalized": self.normalized,
            "confidence": self.confidence,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "context": self.context,
            "metadata": self.metadata or {}
        }


class LegalTerminology:
    """
    Legal terminology database with synonyms and canonical forms.

    This class maintains dictionaries of legal terms, programs, person types,
    and jurisdictions specific to Canadian government regulations.
    """

    # Person types - Canadian immigration and residency statuses
    PERSON_TYPES = {
        "citizen": ["canadian citizen", "citizen of canada", "citizenship"],
        "permanent_resident": ["permanent resident", "pr", "landed immigrant", "perm resident"],
        "temporary_resident": ["temporary resident", "temp resident", "visitor", "temporary foreign worker", "tfr"],
        "foreign_national": ["foreign national", "foreign citizen", "non-resident"],
        "refugee": ["refugee", "protected person", "asylum seeker"],
        "indigenous_person": ["indigenous person", "first nations", "métis", "inuit", "aboriginal"],
        "veteran": ["veteran", "former member", "ex-military"],
        "senior": ["senior", "elderly", "older adult", "65+", "pensioner"],
        "youth": ["youth", "young person", "minor", "under 18"],
        "student": ["student", "full-time student", "part-time student", "learner"],
        "worker": ["worker", "employee", "employed person", "labourer"],
        "employer": ["employer", "business owner", "company"],
        "self_employed": ["self-employed", "independent contractor", "freelancer"],
    }

    # Government programs and services
    PROGRAMS = {
        "employment_insurance": ["employment insurance", "ei", "unemployment insurance", "ei benefits"],
        "canada_pension_plan": ["canada pension plan", "cpp", "pension"],
        "old_age_security": ["old age security", "oas", "old age pension"],
        "guaranteed_income_supplement": ["guaranteed income supplement", "gis"],
        "canada_child_benefit": ["canada child benefit", "ccb", "child benefit"],
        "disability_tax_credit": ["disability tax credit", "dtc"],
        "registered_disability_savings_plan": ["rdsp", "registered disability savings plan"],
        "workers_compensation": ["workers compensation", "wsib", "workplace safety insurance"],
        "social_assistance": ["social assistance", "welfare", "income assistance"],
        "public_health_insurance": ["public health insurance", "medicare", "health care"],
        "immigration": ["immigration", "citizenship and immigration"],
        "express_entry": ["express entry", "economic immigration"],
        "family_sponsorship": ["family sponsorship", "spouse sponsorship"],
        "provincial_nominee": ["provincial nominee program", "pnp"],
    }

    # Jurisdictions - Canadian government levels
    JURISDICTIONS = {
        "federal": ["federal", "canada", "government of canada", "national"],
        "provincial": ["provincial", "province", "territorial"],
        "alberta": ["alberta", "ab"],
        "british_columbia": ["british columbia", "bc", "b.c."],
        "manitoba": ["manitoba", "mb"],
        "new_brunswick": ["new brunswick", "nb", "n.b."],
        "newfoundland_and_labrador": ["newfoundland and labrador", "nl", "nfld"],
        "northwest_territories": ["northwest territories", "nwt", "nt"],
        "nova_scotia": ["nova scotia", "ns", "n.s."],
        "nunavut": ["nunavut", "nu"],
        "ontario": ["ontario", "on", "ont"],
        "prince_edward_island": ["prince edward island", "pei", "p.e.i."],
        "quebec": ["quebec", "qc", "qué"],
        "saskatchewan": ["saskatchewan", "sk", "sask"],
        "yukon": ["yukon", "yt"],
        "municipal": ["municipal", "city", "town", "municipality"],
    }

    # Common legal terms and requirements
    REQUIREMENTS = {
        "social_insurance_number": ["social insurance number", "sin", "sin number"],
        "work_permit": ["work permit", "employment authorization", "authorized to work"],
        "study_permit": ["study permit", "student visa", "authorized to study"],
        "proof_of_residency": ["proof of residency", "proof of address", "residence proof"],
        "identification": ["identification", "id", "identity document", "government id"],
        "birth_certificate": ["birth certificate", "certificate of birth"],
        "passport": ["passport", "travel document"],
        "tax_return": ["tax return", "income tax return", "t1"],
        "notice_of_assessment": ["notice of assessment", "noa"],
        "employment_letter": ["employment letter", "letter of employment", "job letter"],
        "pay_stub": ["pay stub", "pay slip", "salary statement"],
        "bank_statement": ["bank statement", "financial statement"],
    }

    @classmethod
    def get_canonical_form(cls, text: str, entity_type: EntityType) -> Optional[str]:
        """
        Get the canonical form of a legal term.

        Args:
            text: The text to normalize
            entity_type: Type of entity

        Returns:
            Canonical form of the term, or None if not found
        """
        text_lower = text.lower().strip()

        # Select appropriate dictionary based on entity type
        if entity_type == EntityType.PERSON_TYPE:
            term_dict = cls.PERSON_TYPES
        elif entity_type == EntityType.PROGRAM:
            term_dict = cls.PROGRAMS
        elif entity_type == EntityType.JURISDICTION:
            term_dict = cls.JURISDICTIONS
        elif entity_type == EntityType.REQUIREMENT:
            term_dict = cls.REQUIREMENTS
        else:
            return None

        # Find canonical form by checking synonyms
        for canonical, synonyms in term_dict.items():
            if text_lower in synonyms or text_lower == canonical:
                return canonical

        return None

    @classmethod
    def get_all_patterns(cls, entity_type: EntityType) -> List[str]:
        """Get all patterns for a given entity type"""
        if entity_type == EntityType.PERSON_TYPE:
            term_dict = cls.PERSON_TYPES
        elif entity_type == EntityType.PROGRAM:
            term_dict = cls.PROGRAMS
        elif entity_type == EntityType.JURISDICTION:
            term_dict = cls.JURISDICTIONS
        elif entity_type == EntityType.REQUIREMENT:
            term_dict = cls.REQUIREMENTS
        else:
            return []

        # Flatten all synonyms
        all_patterns = []
        for canonical, synonyms in term_dict.items():
            all_patterns.extend(synonyms)
        return all_patterns


class LegalEntityExtractor:
    """
    Extract legal entities from regulatory text using pattern matching and NLP.

    This class combines rule-based pattern matching with statistical NLP to identify
    and extract legal entities from Canadian government regulations and documents.
    """

    def __init__(self, use_spacy: bool = False):
        """
        Initialize the legal entity extractor.

        Args:
            use_spacy: Whether to use spaCy for additional NER (requires spaCy model)
        """
        self.use_spacy = use_spacy
        self.nlp = None

        if use_spacy:
            try:
                import spacy
                # Try to load English model (requires: python -m spacy download en_core_web_sm)
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model loaded successfully")
            except (ImportError, OSError) as e:
                logger.warning(f"spaCy not available: {e}. Using pattern-based extraction only.")
                self.use_spacy = False

        # Compile regex patterns for faster matching
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for entity extraction"""
        self.patterns = {}

        # Compile patterns for each entity type
        for entity_type in [EntityType.PERSON_TYPE, EntityType.PROGRAM,
                           EntityType.JURISDICTION, EntityType.REQUIREMENT]:
            patterns = LegalTerminology.get_all_patterns(entity_type)
            # Sort by length (descending) to match longer phrases first
            patterns = sorted(patterns, key=len, reverse=True)
            # Escape special regex characters and create pattern
            escaped_patterns = [re.escape(p) for p in patterns]
            combined_pattern = r'\b(' + '|'.join(escaped_patterns) + r')\b'
            self.patterns[entity_type] = re.compile(combined_pattern, re.IGNORECASE)

        # Additional regex patterns for structured data
        self.date_pattern = re.compile(
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|'
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b',
            re.IGNORECASE
        )

        self.money_pattern = re.compile(
            r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars|CAD)',
            re.IGNORECASE
        )

        self.legislation_pattern = re.compile(
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Act|Regulation|Code|Law|Statute|Bill))\b'
        )

    def extract_entities(self, text: str, entity_types: Optional[List[EntityType]] = None) -> List[ExtractedEntity]:
        """
        Extract legal entities from text.

        Args:
            text: The text to analyze
            entity_types: List of entity types to extract (None = all types)

        Returns:
            List of extracted entities with metadata
        """
        if not text:
            return []

        if entity_types is None:
            entity_types = list(EntityType)

        entities = []

        # Extract pattern-based entities
        for entity_type in entity_types:
            if entity_type in self.patterns:
                entities.extend(self._extract_pattern_entities(text, entity_type))

        # Extract structured data (dates, money, legislation)
        if EntityType.DATE in entity_types:
            entities.extend(self._extract_dates(text))
        if EntityType.MONEY in entity_types:
            entities.extend(self._extract_money(text))
        if EntityType.LEGISLATION in entity_types:
            entities.extend(self._extract_legislation(text))

        # Use spaCy for additional entities if available
        if self.use_spacy and self.nlp:
            entities.extend(self._extract_spacy_entities(text, entity_types))

        # Remove duplicates and sort by position
        entities = self._deduplicate_entities(entities)
        entities.sort(key=lambda e: e.start_pos)

        return entities

    def _extract_pattern_entities(self, text: str, entity_type: EntityType) -> List[ExtractedEntity]:
        """Extract entities using compiled regex patterns"""
        entities = []
        pattern = self.patterns.get(entity_type)

        if not pattern:
            return entities

        for match in pattern.finditer(text):
            matched_text = match.group(0)
            start_pos = match.start()
            end_pos = match.end()

            # Get canonical form
            canonical = LegalTerminology.get_canonical_form(matched_text, entity_type)

            # Calculate confidence based on match quality
            confidence = self._calculate_confidence(matched_text, canonical, entity_type)

            # Extract context (50 chars before and after)
            context_start = max(0, start_pos - 50)
            context_end = min(len(text), end_pos + 50)
            context = text[context_start:context_end].strip()

            entity = ExtractedEntity(
                text=matched_text,
                entity_type=entity_type,
                normalized=canonical or matched_text.lower(),
                confidence=confidence,
                start_pos=start_pos,
                end_pos=end_pos,
                context=context
            )
            entities.append(entity)

        return entities

    def _extract_dates(self, text: str) -> List[ExtractedEntity]:
        """Extract date entities"""
        entities = []
        for match in self.date_pattern.finditer(text):
            entity = ExtractedEntity(
                text=match.group(0),
                entity_type=EntityType.DATE,
                normalized=match.group(0),
                confidence=0.9,
                start_pos=match.start(),
                end_pos=match.end()
            )
            entities.append(entity)
        return entities

    def _extract_money(self, text: str) -> List[ExtractedEntity]:
        """Extract monetary amounts"""
        entities = []
        for match in self.money_pattern.finditer(text):
            entity = ExtractedEntity(
                text=match.group(0),
                entity_type=EntityType.MONEY,
                normalized=match.group(0),
                confidence=0.95,
                start_pos=match.start(),
                end_pos=match.end()
            )
            entities.append(entity)
        return entities

    def _extract_legislation(self, text: str) -> List[ExtractedEntity]:
        """Extract references to legislation"""
        entities = []
        for match in self.legislation_pattern.finditer(text):
            entity = ExtractedEntity(
                text=match.group(0),
                entity_type=EntityType.LEGISLATION,
                normalized=match.group(0),
                confidence=0.85,
                start_pos=match.start(),
                end_pos=match.end()
            )
            entities.append(entity)
        return entities

    def _extract_spacy_entities(self, text: str, entity_types: List[EntityType]) -> List[ExtractedEntity]:
        """Extract entities using spaCy NER"""
        if not self.nlp:
            return []

        entities = []
        doc = self.nlp(text)

        # Map spaCy entity types to our EntityType
        spacy_mapping = {
            "ORG": EntityType.ORGANIZATION,
            "DATE": EntityType.DATE,
            "MONEY": EntityType.MONEY,
            "LAW": EntityType.LEGISLATION,
        }

        for ent in doc.ents:
            entity_type = spacy_mapping.get(ent.label_)
            if entity_type and entity_type in entity_types:
                entity = ExtractedEntity(
                    text=ent.text,
                    entity_type=entity_type,
                    normalized=ent.text.lower(),
                    confidence=0.8,  # spaCy entities get lower confidence
                    start_pos=ent.start_char,
                    end_pos=ent.end_char,
                    metadata={"spacy_label": ent.label_}
                )
                entities.append(entity)

        return entities

    def _calculate_confidence(self, matched_text: str, canonical: Optional[str],
                            entity_type: EntityType) -> float:
        """Calculate confidence score for an entity match"""
        if not canonical:
            return 0.5  # Low confidence if no canonical form found

        # Higher confidence for exact canonical matches
        if matched_text.lower() == canonical:
            return 0.95

        # Medium-high confidence for known synonyms
        if canonical in [EntityType.PERSON_TYPE, EntityType.PROGRAM,
                        EntityType.JURISDICTION, EntityType.REQUIREMENT]:
            return 0.85

        # Default confidence
        return 0.75

    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove duplicate entities, keeping highest confidence"""
        if not entities:
            return []

        # Group by position
        position_map = {}
        for entity in entities:
            key = (entity.start_pos, entity.end_pos)
            if key not in position_map or entity.confidence > position_map[key].confidence:
                position_map[key] = entity

        return list(position_map.values())

    def extract_entities_by_type(self, text: str, entity_type: EntityType) -> List[ExtractedEntity]:
        """
        Extract entities of a specific type.

        Args:
            text: The text to analyze
            entity_type: The type of entity to extract

        Returns:
            List of extracted entities of the specified type
        """
        return self.extract_entities(text, entity_types=[entity_type])

    def get_entity_summary(self, entities: List[ExtractedEntity]) -> Dict[str, int]:
        """
        Get a summary count of entities by type.

        Args:
            entities: List of extracted entities

        Returns:
            Dictionary mapping entity type to count
        """
        summary = {}
        for entity in entities:
            entity_type = entity.entity_type.value
            summary[entity_type] = summary.get(entity_type, 0) + 1
        return summary


# Convenience function for quick entity extraction
def extract_legal_entities(text: str,
                          entity_types: Optional[List[EntityType]] = None,
                          use_spacy: bool = False) -> List[ExtractedEntity]:
    """
    Quick function to extract legal entities from text.

    Args:
        text: The text to analyze
        entity_types: List of entity types to extract (None = all)
        use_spacy: Whether to use spaCy for additional NER

    Returns:
        List of extracted entities

    Example:
        >>> text = "Can a temporary resident apply for employment insurance?"
        >>> entities = extract_legal_entities(text)
        >>> for e in entities:
        ...     print(f"{e.text} ({e.entity_type}): {e.normalized}")
    """
    extractor = LegalEntityExtractor(use_spacy=use_spacy)
    return extractor.extract_entities(text, entity_types)


if __name__ == "__main__":
    # Test the entity extractor
    test_cases = [
        "Can a temporary resident apply for employment insurance?",
        "Permanent residents are eligible for Canada Pension Plan benefits.",
        "The Employment Insurance Act requires a valid social insurance number.",
        "Applications must be submitted before January 15, 2025.",
        "The benefit amount is $2,500 per month.",
        "This is governed by the Immigration and Refugee Protection Act.",
    ]

    extractor = LegalEntityExtractor(use_spacy=False)

    print("=" * 80)
    print("Legal NLP Service - Entity Extraction Test")
    print("=" * 80)

    for i, text in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {text}")
        print("-" * 80)

        entities = extractor.extract_entities(text)

        if entities:
            for entity in entities:
                print(f"  [{entity.entity_type.value}] {entity.text} → {entity.normalized}")
                print(f"    Confidence: {entity.confidence:.2f}, Position: {entity.start_pos}-{entity.end_pos}")
        else:
            print("  No entities found")

        summary = extractor.get_entity_summary(entities)
        if summary:
            print(f"\n  Summary: {summary}")

    print("\n" + "=" * 80)
    print("Test complete!")
