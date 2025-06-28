# Expert Prompts Reference

This directory contains expert persona prompts that can be used with Cursor. The `.cursorrules` file in the root directory automatically loads these prompts based on context.

## Quick Reference

### 🐍 Python Principal Developer
**File**: `python_principal_dev_prompt.md`
**Use for**: Python development, architecture, code review, technical leadership
**Keywords**: Python, development, architecture, testing, performance, code review

**Quick activation**: Just ask about Python development and I'll automatically adopt this persona.

### ☁️ Azure Architect  
**File**: `azure_architect_prompt.md`
**Use for**: Azure infrastructure, cloud architecture, deployment, DevOps
**Keywords**: Azure, cloud, infrastructure, deployment, Bicep, ARM templates

**Quick activation**: Ask about Azure services or cloud architecture.

## How to Use

### Automatic Mode (Recommended)
Simply ask your question normally. I'll automatically detect the context and use the appropriate expert persona:

```
"Help me optimize this Python function"
→ Automatically uses Python Principal Developer persona

"Design an Azure deployment for this app"
→ Automatically uses Azure Architect persona
```

### Manual Mode
You can explicitly request a specific expert:

```
"Act as a Python Principal Developer and review this code"
"Switch to Azure Architect mode for this infrastructure question"
```

## Adding New Prompts

1. Create a new `.md` file in this directory
2. Define the expert's expertise and communication style
3. Update the `.cursorrules` file in the root directory
4. Add keywords and usage guidelines

## Example Prompts

### For Code Review
```
"Act as a Python Principal Developer and review this code for best practices"
```

### For Architecture Design
```
"From an Azure Architect perspective, how would you design this system?"
```

### For Performance Optimization
```
"As a Python Principal Developer, help me optimize this function for better performance"
```

## Benefits

- **Context-Aware**: Automatically uses the right expertise
- **Seamless**: No need to remember specific commands
- **Flexible**: Can switch between personas in the same conversation
- **Comprehensive**: Each persona has deep, specialized knowledge
- **Maintainable**: Easy to add new expert personas

The system is designed to be intuitive - just ask your question and I'll provide expert-level guidance using the most appropriate persona! 