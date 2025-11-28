# Regulatory Intelligence Assistant MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with direct access to the Regulatory Intelligence Assistant API. This enables natural language interaction with Canadian regulations, compliance checking, and legal analysis.

## Features

### 7 Powerful Tools

1. **search_regulations** - Search Canadian regulations using hybrid semantic + keyword search
2. **get_regulation_detail** - Get complete regulation details including all sections
3. **ask_legal_question** - Answer questions with AI-generated responses and citations
4. **analyze_query** - Parse and analyze legal queries to extract intent and entities
5. **check_compliance** - Check form data for regulatory compliance
6. **validate_field** - Real-time validation of individual form fields
7. **extract_legal_entities** - Extract legal entities from text

## Installation

The server is already installed and configured in your MCP settings. It will start automatically when you begin a conversation.

### Prerequisites

- **Backend API must be running**: The server connects to `http://localhost:8000` by default
- Node.js 18+ (already installed)
- npm packages (already installed)

### Configuration

The server is configured in `.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`:

```json
{
  "regulatory-intelligence": {
    "command": "node",
    "args": ["/home/shawn/Cline/MCP/regulatory-intelligence-mcp/build/index.js"],
    "env": {
      "API_BASE_URL": "http://localhost:8000"
    },
    "disabled": false,
    "autoApprove": []
  }
}
```

### Environment Variables

- `API_BASE_URL`: Backend API URL (default: `http://localhost:8000`)
- `API_TIMEOUT`: Request timeout in milliseconds (default: `30000`)

## Usage Examples

### Example 1: Search for Regulations

```
User: "Find regulations about employment insurance eligibility"

AI Assistant uses: search_regulations
Arguments: {
  "query": "employment insurance eligibility",
  "program": "employment_insurance",
  "size": 5
}

Returns: Top 5 relevant regulations with citations and scores
```

### Example 2: Answer Legal Questions

```
User: "Can a temporary resident apply for employment insurance?"

AI Assistant uses: ask_legal_question
Arguments: {
  "question": "Can a temporary resident apply for employment insurance?",
  "jurisdiction": "federal"
}

Returns: AI-generated answer with legal citations and confidence score
```

### Example 3: Check Compliance

```
User: "Check if this EI application is complete"

AI Assistant uses: check_compliance
Arguments: {
  "program_id": "employment-insurance",
  "form_data": {
    "sin": "123-456-789",
    "employment_status": "unemployed",
    "hours_worked": 700
  }
}

Returns: Detailed compliance report with issues and recommendations
```

### Example 4: Analyze Query Structure

```
User: "Analyze this query: 'What are CPP benefits for seniors?'"

AI Assistant uses: analyze_query
Arguments: {
  "query": "What are CPP benefits for seniors?"
}

Returns: Intent classification, extracted entities, and suggested filters
```

### Example 5: Extract Legal Entities

```
User: "Extract entities from: 'Canadian citizens and permanent residents may apply for OAS benefits'"

AI Assistant uses: extract_legal_entities
Arguments: {
  "text": "Canadian citizens and permanent residents may apply for OAS benefits",
  "entity_types": ["person_type", "program"]
}

Returns: Extracted entities with confidence scores
```

### Example 6: Validate Form Field

```
User: "Validate a SIN field with value '123-456-789'"

AI Assistant uses: validate_field
Arguments: {
  "program_id": "employment-insurance",
  "field_name": "sin",
  "field_value": "123-456-789"
}

Returns: Validation status with errors or warnings
```

### Example 7: Get Regulation Details

```
User: "Show me full details of regulation abc-123-def"

AI Assistant uses: get_regulation_detail
Arguments: {
  "regulation_id": "abc-123-def-456-789"
}

Returns: Complete regulation with all sections and metadata
```

## Tool Reference

### search_regulations

Search Canadian regulations using hybrid search.

**Parameters:**
- `query` (string, required): Search query
- `jurisdiction` (string, optional): Filter by jurisdiction
- `program` (string, optional): Filter by program
- `size` (number, optional): Number of results (default: 10)

**Returns:** Search results with relevance scores

### get_regulation_detail

Get complete details of a specific regulation.

**Parameters:**
- `regulation_id` (string, required): UUID of regulation

**Returns:** Full regulation details including all sections

### ask_legal_question

Answer questions using RAG with legal citations.

**Parameters:**
- `question` (string, required): Question to answer
- `jurisdiction` (string, optional): Filter by jurisdiction
- `num_context_docs` (number, optional): Context documents (default: 5)

**Returns:** AI answer with citations and confidence score

### analyze_query

Analyze query structure using NLP.

**Parameters:**
- `query` (string, required): Query to analyze

**Returns:** Intent, entities, keywords, and filters

### check_compliance

Check form data against regulatory requirements.

**Parameters:**
- `program_id` (string, required): Program identifier
- `form_data` (object, required): Form fields and values
- `workflow_type` (string, optional): Workflow type (default: "application")

**Returns:** Compliance report with issues and recommendations

### validate_field

Validate a single form field in real-time.

**Parameters:**
- `program_id` (string, required): Program identifier
- `field_name` (string, required): Field to validate
- `field_value` (any, required): Value to validate
- `form_context` (object, optional): Other form fields

**Returns:** Validation result with errors/warnings

### extract_legal_entities

Extract legal entities from text.

**Parameters:**
- `text` (string, required): Text to analyze
- `entity_types` (array, optional): Specific entity types to extract

**Returns:** Extracted entities with confidence scores

## Development

### Project Structure

```
regulatory-intelligence-mcp/
├── src/
│   ├── index.ts           # Main server implementation
│   ├── api-client.ts      # API client for backend communication
│   ├── tools.ts           # Tool definitions and handlers
│   └── types.ts           # TypeScript type definitions
├── build/                 # Compiled JavaScript output
├── package.json           # Project dependencies
├── tsconfig.json          # TypeScript configuration
└── README.md             # This file
```

### Building

```bash
npm run build
```

### Modifying the Server

1. Edit files in `src/`
2. Rebuild: `npm run build`
3. Restart Cline to reload the server

### Adding New Tools

1. Add tool definition to `tools` array in `src/tools.ts`
2. Add API client method in `src/api-client.ts` if needed
3. Add handler in `handleToolCall` function in `src/tools.ts`
4. Add types in `src/types.ts` if needed
5. Rebuild and test

## Troubleshooting

### "Cannot connect to backend API" Warning

**Cause**: Backend server is not running

**Solution**: Start the backend server:
```bash
cd /path/to/regulatory-intelligence-assistant/backend
docker-compose up
# OR
python -m uvicorn main:app --reload
```

### Tools Failing with Network Errors

**Cause**: Backend URL is incorrect or backend is down

**Solution**: 
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify API_BASE_URL in MCP settings
3. Check Docker containers: `docker ps`

### TypeScript Errors After Modifying Code

**Cause**: Type definitions are out of sync

**Solution**:
```bash
cd /home/shawn/Cline/MCP/regulatory-intelligence-mcp
npm run build
```

### Server Not Appearing in Available Tools

**Cause**: Server may be disabled or misconfigured

**Solution**:
1. Check MCP settings file
2. Ensure `"disabled": false`
3. Restart Cline

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│   AI Assistant  │─────>│   MCP Server     │─────>│   FastAPI Backend   │
│   (Claude, etc) │<─────│  (Proxy Layer)   │<─────│   (Our API)         │
└─────────────────┘      └──────────────────┘      └─────────────────────┘
      ↑                          ↑
      └──────────────────────────┘
         MCP Protocol           HTTP/REST
```

The MCP server acts as a translation layer between the MCP protocol and our REST API, enabling AI assistants to use our regulatory intelligence capabilities.

## License

MIT License - See main project for details

## Support

For issues or questions:
1. Check the main project documentation
2. Review troubleshooting section above
3. Check backend logs for API errors

## Credits

Part of the Regulatory Intelligence Assistant project - G7 GovAI Challenge submission.
