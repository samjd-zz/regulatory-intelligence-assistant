#!/usr/bin/env node

/**
 * Regulatory Intelligence Assistant MCP Server
 * 
 * This MCP server provides AI assistants with direct access to the
 * Regulatory Intelligence Assistant API, enabling them to:
 * - Search Canadian regulations
 * - Answer legal questions with citations
 * - Check compliance against requirements
 * - Analyze legal queries
 * - Extract legal entities from text
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { tools, handleToolCall } from './tools.js';
import { apiClient } from './api-client.js';

/**
 * Create an MCP server with tools for regulatory intelligence
 */
const server = new Server(
  {
    name: "regulatory-intelligence-mcp",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

/**
 * Handler for listing available tools
 */
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools };
});

/**
 * Handler for tool execution
 */
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  return await handleToolCall(request);
});

/**
 * Start the server using stdio transport
 */
async function main() {
  // Verify API connection before starting
  console.error('Regulatory Intelligence MCP Server starting...');
  console.error('Checking connection to backend API...');
  
  const isHealthy = await apiClient.healthCheck();
  if (!isHealthy) {
    console.error('WARNING: Cannot connect to backend API. Tools will fail until backend is running.');
    console.error(`Expected backend at: ${process.env.API_BASE_URL || 'http://localhost:8000'}`);
  } else {
    console.error('✓ Connected to backend API');
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('Regulatory Intelligence MCP Server running');
  console.error('Available tools: 7');
  console.error('  - search_regulations: Search Canadian regulations');
  console.error('  - get_regulation_detail: Get full regulation details');
  console.error('  - ask_legal_question: Answer questions with citations');
  console.error('  - analyze_query: Analyze query structure');
  console.error('  - check_compliance: Check regulatory compliance');
  console.error('  - validate_field: Validate form fields');
  console.error('  - extract_legal_entities: Extract entities from text');
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
