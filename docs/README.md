# Documentation

This directory contains technical documentation for the TinyTroupe Brainstorming application.

## Documents

### [ARCHITECTURE.md](./ARCHITECTURE.md)
Complete analysis of the current codebase structure, including:
- Overview of discussion implementation approaches (REST API, SSE, WebSocket)
- Analysis of code duplication issues
- Component responsibilities and current usage status
- Detailed breakdown of where duplicate code exists

### [REFACTOR_PLAN.md](./REFACTOR_PLAN.md)
Comprehensive refactoring strategy to eliminate code duplication:
- Specific examples of redundant implementations
- Step-by-step integration recommendations
- Estimated effort and benefits
- Migration strategy with backward compatibility

## Key Issues Identified

### Code Duplication
- **「議論テーマ「」** string appears in 4 locations
- Discussion generation logic duplicated across normal and streaming implementations
- Multiple unused frontend page components

### Recommended Actions
1. **High Priority**: Consolidate system message generation (30 min effort)
2. **Medium Priority**: Integrate discussion generation methods (2 hour effort)  
3. **Low Priority**: Clean up unused components and files (1 hour effort)

## Usage
These documents should be consulted before:
- Making changes to discussion-related functionality
- Adding new discussion features
- Debugging discussion implementation issues
- Planning architectural improvements

Last updated: August 2025