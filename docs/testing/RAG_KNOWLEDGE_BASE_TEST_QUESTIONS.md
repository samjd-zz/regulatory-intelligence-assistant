# RAG Knowledge Base Verification Test Questions

## Overview

This document provides test questions to verify that the RAG system has access to all **1,827 regulations** and **277,027 sections** (559,270 total documents) in the knowledge base.

**Current Data Status (from README):**
- PostgreSQL: 1,827 regulations, 277,027 sections, 2,555 amendments
- Elasticsearch: 559,270 documents indexed
- Neo4j: 831,548 Section nodes, 5,557 Regulation nodes
- Bilingual: English + French versions available

---

## Testing Strategy

### 1. Coverage Verification Questions

**Purpose**: Verify RAG can access the full dataset, not just a small subset.

#### A. General Knowledge Base Queries

```
Q1: "How many Canadian federal acts do you have access to?"
Expected: Should mention ~1,827 regulations or ~1,912 acts (bilingual)

Q2: "List 20 different Canadian federal acts you know about"
Expected: Should list 20 diverse acts across different domains

Q3: "What areas of law are covered in your knowledge base?"
Expected: Should mention major categories like employment, immigration, tax, health, privacy, justice, etc.

Q4: "Show me acts related to employment and labor"
Expected: Should list multiple acts (Employment Insurance Act, Canada Labour Code, etc.)

Q5: "What immigration-related acts do you know?"
Expected: Should list Immigration and Refugee Protection Act, Citizenship Act, etc.
```

#### B. Specific Act Verification

**Test if major Canadian federal acts are accessible:**

```
Q6: "Tell me about the Employment Insurance Act"
Expected: Should provide detailed information with sections

Q7: "What is the Income Tax Act?"
Expected: Should access the largest Canadian federal statute

Q8: "Summarize the Canada Pension Plan Act"
Expected: Should provide key provisions and sections

Q9: "What does the Excise Tax Act cover?"
Expected: Should explain GST/HST and other excise taxes

Q10: "Tell me about the Privacy Act"
Expected: Should explain federal privacy protections

Q11: "What is the Access to Information Act?"
Expected: Should explain information access rights

Q12: "Explain the Criminal Code of Canada"
Expected: Should provide overview of criminal law provisions

Q13: "What does the Canada Health Act say?"
Expected: Should explain healthcare principles

Q14: "Tell me about the Official Languages Act"
Expected: Should explain bilingualism requirements

Q15: "What is the Indian Act?"
Expected: Should explain Indigenous peoples' regulations
```

#### C. Obscure/Lesser-Known Acts (Tests Deep Coverage)

```
Q16: "What is the Hazardous Products Act?"
Expected: Should find and explain this act

Q17: "Tell me about the Seeds Act"
Expected: Should access agricultural regulations

Q18: "What does the Aeronautics Act cover?"
Expected: Should explain aviation regulations

Q19: "Explain the Canada Shipping Act"
Expected: Should cover maritime law

Q20: "What is the Migratory Birds Convention Act?"
Expected: Should explain wildlife protection
```

---

### 2. Section-Level Verification Questions

**Purpose**: Verify RAG can access specific sections within acts (277,027 sections).

```
Q21: "What does Section 7 of the Employment Insurance Act say?"
Expected: Should quote specific section text

Q22: "Explain subsection 15(1) of the Immigration and Refugee Protection Act"
Expected: Should provide detailed section content

Q23: "What are the requirements in Section 152 of the Income Tax Act?"
Expected: Should access specific tax filing requirements

Q24: "Quote Section 2 of the Criminal Code"
Expected: Should provide exact definitions section

Q25: "What does Section 4 of the Privacy Act require?"
Expected: Should explain personal information collection rules
```

---

### 3. Cross-Reference Testing

**Purpose**: Verify knowledge graph relationships and cross-references.

```
Q26: "Which acts reference the Employment Insurance Act?"
Expected: Should identify related acts and regulations

Q27: "What regulations are made under the Income Tax Act?"
Expected: Should list Income Tax Regulations and related instruments

Q28: "How does the Canada Pension Plan relate to Old Age Security?"
Expected: Should explain relationships between pension programs

Q29: "Which acts deal with both employment and immigration?"
Expected: Should find acts covering temporary foreign workers

Q30: "What acts reference 'social insurance number'?"
Expected: Should find multiple acts (EI, CPP, Income Tax, etc.)
```

---

### 4. Bilingual Support Testing

**Purpose**: Verify access to both English and French versions.

```
Q31: "Qu'est-ce que la Loi sur l'assurance-emploi?" (French)
Expected: Should respond with French content

Q32: "What is the French title of the Employment Insurance Act?"
Expected: Should know "Loi sur l'assurance-emploi"

Q33: "Trouvez les règlements sur l'immigration" (French)
Expected: Should find French immigration regulations

Q34: "List acts in both English and French"
Expected: Should demonstrate bilingual access
```

---

### 5. Domain-Specific Deep Dives

**Purpose**: Test comprehensive coverage within specific domains.

#### A. Employment & Labour

```
Q35: "What are all the eligibility requirements for Employment Insurance?"
Q36: "How do I calculate my EI benefits?"
Q37: "What is the Canada Labour Code's position on overtime?"
Q38: "What are maternity leave entitlements under EI?"
```

#### B. Immigration & Citizenship

```
Q39: "What are the requirements to become a Canadian citizen?"
Q40: "Can refugees work in Canada?"
Q41: "What is a temporary resident permit?"
Q42: "How does the points system work for immigration?"
```

#### C. Tax Law

```
Q43: "What are the basic personal income tax deductions?"
Q44: "How is GST/HST calculated?"
Q45: "What are RRSP contribution limits?"
Q46: "When must corporations file their tax returns?"
```

#### D. Privacy & Data Protection

```
Q47: "What personal information can the government collect?"
Q48: "How do I access my government records?"
Q49: "What are privacy breach notification requirements?"
Q50: "How is personal information protected in Canada?"
```

#### E. Health & Safety

```
Q51: "What are workplace safety requirements?"
Q52: "What does the Canada Health Act require of provinces?"
Q53: "How are dangerous goods regulated?"
Q54: "What are food safety regulations?"
```

---

### 6. Amendment & Version Testing

**Purpose**: Verify access to current versions and amendments (2,555 amendments).

```
Q55: "What are recent amendments to the Employment Insurance Act?"
Q56: "Has the Immigration Act been amended recently?"
Q57: "What was the last update to the Criminal Code?"
Q58: "Show me the amendment history of the Income Tax Act"
```

---

### 7. Complex Multi-Topic Queries

**Purpose**: Test RAG's ability to synthesize across multiple acts.

```
Q59: "Compare employment insurance eligibility for citizens vs permanent residents"
Expected: Should reference multiple acts and regulations

Q60: "What are the tax implications of receiving EI benefits?"
Expected: Should reference both EI Act and Income Tax Act

Q61: "How do immigration status and employment rights interact?"
Expected: Should synthesize immigration and labour law

Q62: "What government benefits require a Social Insurance Number?"
Expected: Should identify multiple programs across acts

Q63: "How do federal and provincial responsibilities differ for healthcare?"
Expected: Should explain constitutional division of powers
```

---

### 8. Negative Testing (Coverage Gaps)

**Purpose**: Identify what's NOT in the knowledge base.

```
Q64: "Tell me about Ontario's Employment Standards Act"
Expected: Should indicate this is PROVINCIAL (not in federal database)

Q65: "What does Quebec's Civil Code say?"
Expected: Should indicate provincial law is not covered

Q66: "Explain British Columbia's human rights law"
Expected: Should clarify scope is federal only

Q67: "What are municipal bylaws for Toronto?"
Expected: Should indicate municipal law is out of scope
```

---

### 9. Elasticsearch Document Count Verification

**Purpose**: Directly verify document access via MCP server tools.

#### Using MCP Server Tools (from mcp-server/README.md)

```python
# Use search_regulations tool to test coverage
search_regulations(query="*", size=50)
# Should return diverse results from across the knowledge base

# Test program-specific searches
search_regulations(query="employment insurance", program="employment_insurance", size=10)
search_regulations(query="income tax", program="tax", size=10)
search_regulations(query="immigration", program="immigration", size=10)

# Test jurisdiction filtering
search_regulations(query="federal regulations", jurisdiction="federal", size=20)

# Get specific regulation details
get_regulation_detail(regulation_id="<actual-uuid>")
# Should return full regulation with all sections
```

---

### 10. Performance Benchmarking Questions

**Purpose**: Test retrieval quality and ranking across large dataset.

```
Q68: "Find the most relevant section about maternity benefits"
Expected: Should prioritize EI Act Section 23

Q69: "What section defines 'insurable employment'?"
Expected: Should find EI Act Section 5

Q70: "Which act governs tax collection?"
Expected: Should rank Income Tax Act highest

Q71: "Find all mentions of 'reasonable accommodation'"
Expected: Should search across multiple acts

Q72: "What acts mention 'discrimination'?"
Expected: Should find Human Rights Act, Criminal Code, etc.
```

---

## Verification Checklist

Use this checklist to verify RAG has full knowledge base access:

### ✅ Basic Coverage

- [ ] RAG acknowledges ~1,800-1,900 regulations in knowledge base
- [ ] Can list 20+ diverse federal acts
- [ ] Can access major acts (EI, Income Tax, Criminal Code, Immigration)
- [ ] Can access obscure acts (Seeds Act, Aeronautics Act, etc.)
- [ ] Can retrieve specific section text with citations

### ✅ Advanced Coverage

- [ ] Can identify cross-references between acts
- [ ] Can access both English and French versions
- [ ] Can explain amendment history
- [ ] Can synthesize across multiple acts
- [ ] Can handle 10+ queries without repeating same limited sources

### ✅ Breadth Testing

- [ ] Employment law queries (5 different acts)
- [ ] Immigration law queries (3+ different acts)
- [ ] Tax law queries (Income Tax Act + Excise Tax Act + GST)
- [ ] Privacy law queries (Privacy Act + Access to Information Act)
- [ ] Health & safety queries (3+ different acts)
- [ ] Justice/criminal queries (Criminal Code + related acts)

### ✅ Depth Testing

- [ ] Can quote specific sections verbatim
- [ ] Can explain subsections and clauses
- [ ] Can identify specific section numbers for requirements
- [ ] Can distinguish between similar provisions in different acts
- [ ] Can access definitions sections

### ✅ Quality Indicators

- [ ] Citations include act names, section numbers, and years
- [ ] Confidence scores are reasonable (0.7-0.95)
- [ ] No hallucinations or made-up acts
- [ ] Acknowledges when information is not in database
- [ ] Correctly identifies provincial/municipal law as out of scope

---

## Red Flags (RAG Has Limited Access)

⚠️ **Warning Signs** that RAG only has access to a small subset:

1. **Repetitive Sources**: Always cites same 5-10 acts regardless of query
2. **Generic Answers**: Provides general knowledge instead of specific citations
3. **Missing Major Acts**: Cannot find Income Tax Act, Criminal Code, or other major statutes
4. **No Section Details**: Cannot quote specific section text
5. **Claims Small Dataset**: Says "I have access to 5 regulations" or similar
6. **No Bilingual Content**: Cannot access French versions
7. **No Obscure Acts**: Cannot find lesser-known acts like Seeds Act or Migratory Birds Act
8. **No Cross-References**: Cannot identify relationships between acts

---

## Diagnostic Commands

### Check Elasticsearch Index

```bash
# Verify document count
curl -s http://localhost:9200/regulations/_count | jq

# Expected: ~559,270 documents

# Sample documents
curl -s http://localhost:9200/regulations/_search?size=10 | jq '.hits.hits[] | {title: ._source.title, type: ._source.document_type}'

# Should show diverse regulations, not just 5-10 repeated ones
```

### Check PostgreSQL

```bash
# Count regulations
docker compose exec backend python -c "
from database import SessionLocal
from models.models import Regulation, Section
db = SessionLocal()
print(f'Regulations: {db.query(Regulation).count()}')
print(f'Sections: {db.query(Section).count()}')
"

# Expected: 1,827 regulations, 277,027 sections
```

### Check Neo4j

```cypher
// In Neo4j Browser (http://localhost:7474)
MATCH (n:Regulation) RETURN count(n) as regulations
MATCH (n:Section) RETURN count(n) as sections

// Expected: 5,557 Regulation nodes, 831,548 Section nodes
```

### Test RAG Retrieval

```bash
# Test how many unique sources RAG uses
curl -X POST "http://localhost:8000/api/rag/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What federal acts do you have in your knowledge base?",
    "num_context_docs": 20
  }' | jq '.sources | length'

# Should retrieve 20 diverse documents
```

---

## Reindexing if Access is Limited

If RAG shows limited access (e.g., only 5-10 acts), the issue is likely **Elasticsearch indexing failed** during data ingestion. See README.md "Troubleshooting" section:

```bash
# Reindex Elasticsearch from PostgreSQL
docker compose exec backend python scripts/reindex_elasticsearch.py

# This will index all 1,827 regulations + 277,027 sections
# Takes ~10-20 minutes for full dataset
```

---

## Expected Results

### Good RAG Performance ✅

- Answers 90%+ of questions with specific citations
- Cites 50+ different acts across 70 questions
- Provides section-level details consistently
- Handles obscure acts and specific sections
- Confidence scores 0.75-0.95 for most answers
- Acknowledges scope limitations appropriately

### Limited RAG Performance ⚠️

- Only cites 5-10 acts repeatedly
- Generic answers without citations
- Cannot find specific sections
- Low confidence scores (<0.5)
- Cannot access major federal acts
- Run reindexing script to fix

---

## Automated Testing Script

Create a test script to verify coverage systematically:

```python
# test_rag_coverage.py
import requests
import json

RAG_ENDPOINT = "http://localhost:8000/api/rag/ask"

test_questions = [
    "How many Canadian federal acts do you have?",
    "Tell me about the Employment Insurance Act",
    "What is the Income Tax Act?",
    "Explain the Criminal Code",
    "What is the Seeds Act?",  # Obscure act
    "Quote Section 7 of the Employment Insurance Act",  # Specific section
    "Which acts reference social insurance numbers?",  # Cross-reference
    # Add all 70+ questions from above
]

def test_rag_coverage():
    cited_acts = set()
    results = []
    
    for question in test_questions:
        response = requests.post(RAG_ENDPOINT, json={"question": question})
        data = response.json()
        
        # Extract cited acts from response
        if "citations" in data:
            for citation in data["citations"]:
                cited_acts.add(citation.get("source", ""))
        
        results.append({
            "question": question,
            "confidence": data.get("confidence", 0),
            "sources_used": len(data.get("sources", []))
        })
    
    print(f"Total unique acts cited: {len(cited_acts)}")
    print(f"Average confidence: {sum(r['confidence'] for r in results) / len(results):.2f}")
    print(f"Average sources per question: {sum(r['sources_used'] for r in results) / len(results):.1f}")
    
    if len(cited_acts) < 20:
        print("⚠️ WARNING: RAG only citing {len(cited_acts)} acts. Expected 50+")
        print("Run: docker compose exec backend python scripts/reindex_elasticsearch.py")

if __name__ == "__main__":
    test_rag_coverage()
```

---

## Summary

To verify RAG has access to all 559,270 documents:

1. **Ask diverse questions** across all 10 categories above
2. **Verify unique sources**: Should cite 50+ different acts across 70 questions
3. **Test section-level access**: Can quote specific sections verbatim
4. **Check bilingual**: Can access French versions
5. **Verify cross-references**: Can identify relationships between acts
6. **Diagnostic commands**: Check Elasticsearch document count directly

**Success Criteria**: RAG should confidently answer 90%+ of questions with specific citations from diverse sources across the entire federal legal corpus.
