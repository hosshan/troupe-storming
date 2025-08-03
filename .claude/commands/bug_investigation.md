## Bug Investigation Process

When users report the same bug multiple times, follow this structured investigation process to avoid redundant work and ensure thorough analysis.

### Investigation Template

Create a structured analysis using this format:

```markdown
## Bug Report: [Issue Description]

### 🐛 Issue Summary
- **Reported by**: [User/Context]
- **Frequency**: [First time / Previously reported]
- **Severity**: [Critical/High/Medium/Low]
- **Environment**: [Browser/OS/Setup details if relevant]

### 📋 Current Behavior
[Detailed description of what is happening]

### ✅ Expected Behavior  
[What should happen instead]

### 🔍 Investigation Results

#### Root Cause Analysis
- **Primary Hypothesis**: [Most likely cause]
- **Secondary Hypotheses**: [Alternative explanations]
- **Evidence**: [Supporting data/logs/observations]

#### Attempted Solutions
- ✅ **Tried**: [What was attempted and outcome]
- ✅ **Tried**: [Another attempt and result]
- ❌ **Failed**: [What didn't work and why]

#### System Impact
- **Affected Components**: [List of impacted parts]
- **Upstream/Downstream Effects**: [Related issues]
- **Data Integrity**: [Any data concerns]

### 🎯 Next Action Options

#### Option A: [Quick Fix] (Recommended)
- **Description**: [Brief explanation]
- **Effort**: [Time estimate]
- **Risk**: [Low/Medium/High]
- **Pros**: [Benefits]
- **Cons**: [Drawbacks]

#### Option B: [Comprehensive Solution]
- **Description**: [Detailed approach]  
- **Effort**: [Time estimate]
- **Risk**: [Low/Medium/High]
- **Pros**: [Benefits]
- **Cons**: [Drawbacks]

#### Option C: [Alternative Approach]
- **Description**: [Different strategy]
- **Effort**: [Time estimate] 
- **Risk**: [Low/Medium/High]
- **Pros**: [Benefits]
- **Cons**: [Drawbacks]

### 📝 Decision & Implementation
- **Selected Option**: [A/B/C and rationale]
- **Implementation Plan**: [Step-by-step approach]
- **Testing Strategy**: [How to verify the fix]
- **Rollback Plan**: [How to undo if needed]
```

### Investigation Guidelines

1. **First Occurrence**: Investigate immediately and document findings
2. **Repeat Reports**: Reference previous investigation, update with new information
3. **Escalation Criteria**: 
   - Critical bugs affecting core functionality
   - Bugs reported by multiple users
   - Data corruption or security issues
4. **Documentation Location**: Create investigation files in `docs/investigations/`
5. **Communication**: Update users with structured findings and timeline

### Example Investigation

```markdown
## Bug Report: Infinite Loading in Discussion Results

### 🐛 Issue Summary
- **Reported by**: User (http://localhost:3000/discussions/6/results/17)
- **Frequency**: Previously reported - backend termination issues
- **Severity**: High (blocks core functionality)

### 🔍 Investigation Results

#### Root Cause Analysis
- **Primary Hypothesis**: SSE connection hanging due to TinyTroupe "Action similarity" errors
- **Evidence**: TinyTroupe logs show "Action similarity too high (1), replacing with DONE"

#### Attempted Solutions
- ✅ **Tried**: Created DiscussionResultsPageSimple with polling - SUCCESSFUL
- ✅ **Tried**: Added timeout mechanisms - PARTIALLY SUCCESSFUL  
- ❌ **Failed**: SSE streaming approach - too complex for current needs

### 🎯 Next Action Options

#### Option A: Use Simple Polling Approach (Recommended)
- **Effort**: Already implemented
- **Risk**: Low
- **Pros**: Reliable, easy to debug
- **Cons**: Less real-time than streaming

#### Option B: Fix TinyTroupe Configuration
- **Effort**: 2-4 hours
- **Risk**: Medium
- **Pros**: Solves root cause
- **Cons**: May introduce other issues
```

This process ensures consistent investigation quality and prevents repeated work on the same issues.