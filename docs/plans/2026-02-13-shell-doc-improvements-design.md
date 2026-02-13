# Shell Interface Documentation Improvements Design

**Date**: 2026-02-13
**Author**: Claude Code
**Project**: Celebi/CelebiChrono
**File**: `interface/shell.py`

## Overview

This document outlines the design for improving documentation strings (docstrings) for all public functions in the `shell.py` module within the CelebiChrono project. The `shell.py` module provides command-line interface functions for managing projects, tasks, algorithms, and directories within the Chern system.

## Current State Analysis

### Documentation Quality Assessment
- **Total functions**: ~70 functions in `shell.py`
- **Well-documented**: ~15 functions with comprehensive docstrings (e.g., `cd`, `mv`, `cp`, `ls`, `submit`, `collect`)
- **Minimally documented**: ~20 functions with brief or incomplete docstrings
- **Undocumented**: ~15 public functions with no docstrings
- **Private functions**: ~20 functions (starting with `_`) with minimal/no documentation

### Inconsistencies Identified
1. **Section headers**: Mixed use of "Args" vs "Arguments"
2. **Returns descriptions**: Often just "Message object" without content description
3. **Examples**: Inconsistent presence and quality
4. **Notes**: Missing from many functions
5. **Formatting**: Inconsistent indentation and spacing

## Design Goals

### Primary Objectives
1. **Standardization**: Consistent Google-style docstrings across all public functions
2. **Completeness**: All required sections (Args, Returns, Examples, Note) present
3. **Clarity**: Clear, concise descriptions focused on content/meaning
4. **Practicality**: Useful examples and important usage notes

### Secondary Objectives
1. **Maintainability**: Easy to update and extend
2. **Consistency**: Uniform terminology and formatting
3. **Accuracy**: Technically correct descriptions matching implementation

## Design Specifications

### 1. Documentation Structure
All public functions will follow this Google Python style format:

```python
"""Brief description.

Extended description if needed.

Args:
    param1 (type): Description
    param2 (type, optional): Description. Defaults to value.

Returns:
    Description of returned content/meaning.

Examples:
    function_name(arg1)  # Example comment
    function_name(arg1, arg2)  # Another example

Note:
    Important notes, constraints, or warnings.
```

### 2. Section Requirements

#### Args Section
- **Required for all functions with parameters**
- Parameter names match function signature
- Type annotations should match docstring types
- Optional parameters marked with "(optional)"
- Default values indicated with "Defaults to value"

#### Returns Section
- **Required for all functions returning values (not None)**
- Describe content/meaning, not just type
- For Message objects: describe what information the message contains
- For None returns: omit Returns section

#### Examples Section
- **Required for all public functions**
- 1-2 practical usage examples
- Show common use cases
- Include comments explaining what each example does
- Use actual command syntax from Chern system

#### Note Section
- **Required for all public functions**
- Important constraints, limitations, or warnings
- Usage considerations
- Dependencies or prerequisites
- Error conditions or edge cases

### 3. Scope Definition

#### Included (Public Functions)
- Functions without leading underscore (`_`)
- Approximately 50 functions
- Examples: `cd`, `ls`, `mv`, `cp`, `submit`, `collect`, etc.

#### Excluded (Private Functions)
- Functions with leading underscore (`_`)
- Internal helper functions
- Examples: `_cd_by_index`, `_normalize_paths`, `_validate_copy_operation`, etc.

### 4. Content Guidelines

#### Detail Level: Standard
- Clear but concise descriptions
- Focus on what the function does, not just what it is
- Use project-specific terminology consistently
- Avoid overly technical language unless necessary

#### Terminology Standards
- Use "Celebi object" for project entities
- Use "task", "algorithm", "directory", "project" consistently
- Use "runner" for execution environments
- Use "DITE" for distributed execution system

#### Example Quality
- Real, testable usage patterns
- Show both simple and advanced usage where appropriate
- Include project-relative paths (`@/path`) examples
- Demonstrate error handling or edge cases in Notes

### 5. Implementation Strategy

#### Phase 1: Standardization (30%)
- Standardize well-documented functions first
- Fix section headers to Google style
- Update Returns descriptions to focus on content
- Ensure consistent formatting

#### Phase 2: Completion (40%)
- Add missing sections to minimally documented functions
- Create docstrings for undocumented functions
- Verify all required sections are present
- Check type consistency between signatures and docstrings

#### Phase 3: Quality Enhancement (20%)
- Improve example quality and relevance
- Add important usage notes
- Cross-reference related functions
- Ensure technical accuracy

#### Phase 4: Verification (10%)
- Review all docstrings for consistency
- Test examples for validity
- Verify no regressions in existing documentation
- Final quality check

### 6. Quality Standards

#### Completeness Checklist
- [ ] Brief description present
- [ ] Args section complete (if parameters exist)
- [ ] Returns section present (if returns value)
- [ ] Examples section with 1-2 examples
- [ ] Note section with important information
- [ ] Consistent formatting and indentation

#### Accuracy Requirements
- Parameter names match function signature
- Type descriptions match actual types
- Examples are valid and testable
- Notes reflect actual constraints/limitations
- Terminology consistent with project usage

## Success Criteria

### Primary Success Metrics
1. **100% of public functions** have complete docstrings
2. **Consistent formatting** across all functions
3. **Useful examples** for all functions
4. **Content-focused Returns** descriptions

### Secondary Success Metrics
1. **Improved readability** and understanding
2. **Easier maintenance** of documentation
3. **Better developer experience** for API users
4. **Foundation for automated documentation** generation

## Risks and Mitigations

### Risk 1: Over-documentation
- **Risk**: Documentation becomes verbose and hard to maintain
- **Mitigation**: Adhere to "Standard" detail level, focus on clarity over completeness

### Risk 2: Inconsistent Implementation
- **Risk**: Different functions documented to different standards
- **Mitigation**: Use template-based approach, thorough review process

### Risk 3: Technical Inaccuracies
- **Risk**: Documentation doesn't match actual behavior
- **Mitigation**: Verify against implementation, test examples

### Risk 4: Scope Creep
- **Risk**: Attempting to document private functions or expand beyond requirements
- **Mitigation**: Strict adherence to "public functions only" scope

## Next Steps

1. **Approval**: Get user sign-off on this design
2. **Implementation**: Create detailed implementation plan using writing-plans skill
3. **Execution**: Implement documentation improvements according to plan
4. **Review**: Verify all success criteria are met
5. **Integration**: Ensure documentation works with existing tools and processes

## Appendix

### A. Function Categories for Implementation

#### Navigation Functions
- `cd_project`, `shell_cd_project`, `cd`, `navigate`

#### File Operations
- `mv`, `cp`, `ls`, `short_ls`, `successors`, `rm`, `rm_file`, `mv_file`, `import_file`

#### Object Creation
- `mkalgorithm`, `mktask`, `mkdata`, `mkdir`

#### Task Configuration
- `add_source`, `add_input`, `add_algorithm`, `add_parameter`, `add_parameter_subtask`
- `set_environment`, `set_memory_limit`, `rm_parameter`, `remove_input`

#### Execution Management
- `jobs`, `status`, `submit`, `collect`, `collect_outputs`, `collect_logs`
- `purge`, `purge_old_impressions`

#### Communication
- `add_host`, `hosts`, `dite`, `set_dite`, `runners`, `register_runner`
- `remove_runner`, `request_runner`, `search_impression`, `send`

#### Visualization
- `view`, `viewurl`, `impress`, `trace`

#### Utilities
- `get_script_path`, `config`, `danger_call`, `workaround_preshell`
- `workaround_postshell`, `history`, `watermark`, `changes`, `doctor`
- `bookkeep`, `bookkeep_url`, `tree`, `error_log`

### B. Google Style Docstring Reference

Key elements:
- **Triple double quotes** for docstrings
- **First line**: Brief description ending with period
- **Blank line** after brief description
- **Args section**: Parameter documentation
- **Returns section**: Return value description
- **Examples section**: Usage examples
- **Note section**: Important information
- **Indentation**: 4 spaces for section content
- **Line length**: 72-79 characters recommended