# Documentation

This directory contains comprehensive documentation for the EmpathyScale project.

## Quick Navigation

### Getting Started
- **[Main README](../README.md)**: Project overview, quick start, installation

### Core Documentation
- **[ARCHITECTURE.md](./ARCHITECTURE.md)**: System architecture, design patterns, technical structure
- **[WORKFLOW.md](./WORKFLOW.md)**: Agent workflows, responsibilities, execution flow
- **[DATA_STORAGE.md](./DATA_STORAGE.md)**: Data storage structure, file organization, access patterns

### Development Guides
- **[HOW_TO_ADD_AGENTS.md](./HOW_TO_ADD_AGENTS.md)**: Step-by-step guide for extending the system

### Historical Documentation
This documentation has been consolidated into the core guides above for better organization. See WORKFLOW.md for literature search agent capabilities.

## Documentation Overview

### Architecture Guide
**Location**: [ARCHITECTURE.md](./ARCHITECTURE.md)  
**Purpose**: Technical deep-dive into system design

**Contents**:
- Agent group structure and patterns
- Prompt management system
- Sub-agent design patterns
- File organization conventions
- Best practices and troubleshooting

**Best for**: Developers extending the system, understanding design decisions

### Workflow Guide
**Location**: [WORKFLOW.md](./WORKFLOW.md)  
**Purpose**: Understand how agents work together

**Contents**:
- Agent group responsibilities
- Execution flow (interview → literature search)
- Data flow between agents
- Error handling strategies
- Optimization approaches

**Best for**: Understanding system behavior, debugging workflows, planning extensions

### Data Storage Guide
**Location**: [DATA_STORAGE.md](./DATA_STORAGE.md)  
**Purpose**: Complete reference for data organization

**Contents**:
- Directory structure
- File formats and schemas
- Access patterns (DataManager usage)
- Run lifecycle management
- Cleanup and maintenance

**Best for**: Accessing results, managing data, understanding storage structure

### Development Guide
**Location**: [HOW_TO_ADD_AGENTS.md](./HOW_TO_ADD_AGENTS.md)  
**Purpose**: Step-by-step instructions for adding new agent groups

**Contents**:
- Complete templates and examples
- Naming conventions
- Registration process
- Testing guidelines
- Common issues and fixes

**Best for**: Adding new capabilities, extending functionality

## Documentation Updates

When updating documentation:
1. Keep it concise and focused
2. Include code examples where helpful
3. Update cross-references if structure changes
4. Test any code examples before committing
5. Maintain consistent formatting

## Related Resources

- **Tests**: See [../tests/README.md](../tests/README.md) for testing documentation
- **Configuration**: See [../README.md](../README.md#configuration) for setup details
- **Tools**: See [../README.md](../README.md#additional-tools) for utility scripts
