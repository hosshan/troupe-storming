# Bug Investigations

This directory contains structured investigations of reported bugs and issues.

## Investigation Files

### [infinite-loading-discussion-results.md](./infinite-loading-discussion-results.md)
**Status**: ✅ RESOLVED  
**Severity**: High  
**Summary**: Discussion results page showed infinite loading due to SSE connection hangs and missing UI elements for pending discussions.

**Resolution**: Implemented simple polling approach in `DiscussionResultsPageSimple.tsx` with timeout mechanisms and proper button states.

## Investigation Guidelines

When creating new investigation files:

1. **Naming Convention**: `[brief-description].md`
2. **Use Template**: Follow the template in CLAUDE.md 
3. **Status Tracking**: Update status as investigation progresses
4. **Cross-Reference**: Link related issues and commits
5. **Update README**: Add summary to this file

## Investigation Status Codes

- 🔍 **INVESTIGATING**: Active investigation in progress
- ⏳ **PENDING**: Waiting for more information or resources
- ✅ **RESOLVED**: Issue fixed and verified
- ❌ **CLOSED**: Issue could not be resolved or is no longer relevant
- 🔄 **MONITORING**: Resolution implemented, monitoring for recurrence

## Quick Reference

| Issue | Status | Priority | Last Updated |
|-------|--------|----------|--------------|
| Infinite Loading Discussion Results | ✅ RESOLVED | High | 2025-08-04 |

## Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture and component relationships
- [REFACTOR_PLAN.md](../REFACTOR_PLAN.md) - Code improvement plans
- [CLAUDE.md](../../CLAUDE.md) - Development guidelines and processes