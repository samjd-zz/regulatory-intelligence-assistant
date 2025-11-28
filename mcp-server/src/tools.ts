/**
 * MCP Tools Implementation for Regulatory Intelligence Assistant
 */

import {
  CallToolRequest,
  CallToolResult,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { apiClient } from './api-client.js';

/**
 * Define all available tools
 */
export const tools: Tool[] = [
  // ============================================================================
  // SEARCH TOOLS
  // ============================================================================
  {
    name: 'search_regulations',
    description: 'Search Canadian regulations using hybrid semantic + keyword search. Best for finding relevant regulations across the knowledge base.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Search query (e.g., "employment insurance eligibility")',
        },
        jurisdiction: {
          type: 'string',
          description: 'Optional jurisdiction filter (e.g., "federal")',
        },
        program: {
          type: 'string',
          description: 'Optional program filter (e.g., "employment_insurance")',
        },
        size: {
          type: 'number',
          description: 'Number of results to return (default: 10, max: 50)',
          default: 10,
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'get_regulation_detail',
    description: 'Get complete details of a specific regulation including all sections and full text. Use the regulation ID from search results.',
    inputSchema: {
      type: 'object',
      properties: {
        regulation_id: {
          type: 'string',
          description: 'UUID of the regulation to retrieve',
        },
      },
      required: ['regulation_id'],
    },
  },

  // ============================================================================
  // Q&A TOOLS
  // ============================================================================
  {
    name: 'ask_legal_question',
    description: 'Ask a question about Canadian regulations and get an AI-generated answer with legal citations. Uses RAG (Retrieval-Augmented Generation) for accurate, cited responses.',
    inputSchema: {
      type: 'object',
      properties: {
        question: {
          type: 'string',
          description: 'Natural language question about regulations (e.g., "Can a temporary resident apply for employment insurance?")',
        },
        jurisdiction: {
          type: 'string',
          description: 'Optional jurisdiction to focus on (e.g., "federal")',
        },
        num_context_docs: {
          type: 'number',
          description: 'Number of context documents to use (default: 5, max: 20)',
          default: 5,
        },
      },
      required: ['question'],
    },
  },
  {
    name: 'analyze_query',
    description: 'Analyze a legal query using NLP to extract intent, entities, and suggested filters without answering it. Useful for understanding query structure.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Query to analyze',
        },
      },
      required: ['query'],
    },
  },

  // ============================================================================
  // COMPLIANCE TOOLS
  // ============================================================================
  {
    name: 'check_compliance',
    description: 'Check form data for compliance against regulatory requirements. Returns detailed compliance report with issues, recommendations, and citations.',
    inputSchema: {
      type: 'object',
      properties: {
        program_id: {
          type: 'string',
          description: 'Program identifier (e.g., "employment-insurance", "cpp", "oas")',
        },
        form_data: {
          type: 'object',
          description: 'Form fields and their values as key-value pairs',
        },
        workflow_type: {
          type: 'string',
          description: 'Type of workflow (default: "application")',
          default: 'application',
        },
      },
      required: ['program_id', 'form_data'],
    },
  },
  {
    name: 'validate_field',
    description: 'Validate a single form field in real-time against regulatory requirements. Provides immediate feedback on field validity.',
    inputSchema: {
      type: 'object',
      properties: {
        program_id: {
          type: 'string',
          description: 'Program identifier',
        },
        field_name: {
          type: 'string',
          description: 'Name of the field to validate',
        },
        field_value: {
          description: 'Value to validate (any type)',
        },
        form_context: {
          type: 'object',
          description: 'Optional context from other form fields',
        },
      },
      required: ['program_id', 'field_name', 'field_value'],
    },
  },

  // ============================================================================
  // NLP TOOLS
  // ============================================================================
  {
    name: 'extract_legal_entities',
    description: 'Extract legal entities from text including person types, programs, jurisdictions, requirements, and more. Useful for analyzing legal documents.',
    inputSchema: {
      type: 'object',
      properties: {
        text: {
          type: 'string',
          description: 'Text to analyze and extract entities from',
        },
        entity_types: {
          type: 'array',
          items: {
            type: 'string',
          },
          description: 'Optional list of specific entity types to extract (person_type, program, jurisdiction, organization, legislation, date, money, requirement)',
        },
      },
      required: ['text'],
    },
  },
];

/**
 * Handle tool execution
 */
export async function handleToolCall(
  request: CallToolRequest
): Promise<CallToolResult> {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      // ========================================================================
      // SEARCH TOOLS
      // ========================================================================
      case 'search_regulations': {
        const { query, jurisdiction, program, size } = args as {
          query: string;
          jurisdiction?: string;
          program?: string;
          size?: number;
        };

        const filters: Record<string, any> = {};
        if (jurisdiction) filters.jurisdiction = jurisdiction;
        if (program) filters.program = program;

        const result = await apiClient.searchRegulations(
          query,
          filters,
          size || 10
        );

        // Format results for display
        const formattedResults = result.hits.map((hit) => ({
          id: hit.id,
          score: hit.score.toFixed(3),
          title: hit.source.title || 'Untitled',
          citation: hit.source.citation || 'N/A',
          jurisdiction: hit.source.jurisdiction || 'N/A',
          document_type: hit.source.document_type || 'N/A',
          content_preview:
            hit.source.content?.substring(0, 200) + '...' || 'No content',
        }));

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  total_results: result.total,
                  search_type: result.search_type,
                  processing_time_ms: result.processing_time_ms.toFixed(1),
                  results: formattedResults,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case 'get_regulation_detail': {
        const { regulation_id } = args as { regulation_id: string };
        const result = await apiClient.getRegulationDetail(regulation_id);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      // ========================================================================
      // Q&A TOOLS
      // ========================================================================
      case 'ask_legal_question': {
        const { question, jurisdiction, num_context_docs } = args as {
          question: string;
          jurisdiction?: string;
          num_context_docs?: number;
        };

        const result = await apiClient.askLegalQuestion(
          question,
          jurisdiction,
          num_context_docs || 5
        );

        // Format answer for better readability
        const formatted = {
          question: result.question,
          answer: result.answer,
          confidence_score: result.confidence_score.toFixed(2),
          citations: result.citations.map((c) => ({
            text: c.text,
            document: c.document_title || 'Unknown',
            section: c.section || 'N/A',
            confidence: c.confidence.toFixed(2),
          })),
          source_documents: result.source_documents.map((d) => ({
            title: d.title,
            citation: d.citation || 'N/A',
            relevance_score: d.score.toFixed(3),
          })),
          intent: result.intent,
          cached: result.cached,
          processing_time_ms: result.processing_time_ms.toFixed(1),
        };

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(formatted, null, 2),
            },
          ],
        };
      }

      case 'analyze_query': {
        const { query } = args as { query: string };
        const result = await apiClient.analyzeQuery(query);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      // ========================================================================
      // COMPLIANCE TOOLS
      // ========================================================================
      case 'check_compliance': {
        const { program_id, form_data, workflow_type } = args as {
          program_id: string;
          form_data: Record<string, any>;
          workflow_type?: string;
        };

        const result = await apiClient.checkCompliance(
          program_id,
          form_data,
          workflow_type || 'application'
        );

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'validate_field': {
        const { program_id, field_name, field_value, form_context } = args as {
          program_id: string;
          field_name: string;
          field_value: any;
          form_context?: Record<string, any>;
        };

        const result = await apiClient.validateField(
          program_id,
          field_name,
          field_value,
          form_context
        );

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      // ========================================================================
      // NLP TOOLS
      // ========================================================================
      case 'extract_legal_entities': {
        const { text, entity_types } = args as {
          text: string;
          entity_types?: string[];
        };

        const result = await apiClient.extractLegalEntities(text, entity_types);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error occurred';

    return {
      content: [
        {
          type: 'text',
          text: `Error executing tool ${name}: ${errorMessage}`,
        },
      ],
      isError: true,
    };
  }
}
