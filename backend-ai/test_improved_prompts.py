#!/usr/bin/env python3
"""
Test script for improved prompt engineering
This script tests the enhanced prompts for better code indentation
"""

import asyncio
from langchain_ollama import OllamaLLM

# Test configuration for CodeLlama with improved prompts
CODECLLAMA_CONFIG = {
    "num_gpu": 1,
    "num_thread": 8,
    "temperature": 0.3,
    "top_p": 0.9,
    "repeat_penalty": 1.1,
    "top_k": 40,
    "num_ctx": 4096,
}

def create_enhanced_prompt(task: str, context: str = "") -> str:
    """Create an enhanced prompt with explicit indentation instructions"""
    return f"""
You are an expert Python developer. Generate clean, properly indented Python code.

TASK: {task}
CONTEXT: {context}

CRITICAL REQUIREMENTS:
1. Use 4 spaces for indentation (NOT tabs)
2. Follow PEP 8 style guidelines strictly
3. Include proper error handling with try/except blocks
4. Add comprehensive type hints for all functions
5. Include detailed docstrings for all functions and classes
6. Make the code complete and runnable
7. Use proper Python naming conventions (snake_case for functions/variables)

CODE FORMATTING RULES:
- Indent with exactly 4 spaces per level
- No tabs allowed
- Proper spacing around operators
- Maximum line length of 79 characters
- Use f-strings for string formatting
- Import statements at the top

EXAMPLE OF PROPER FORMATTING:
```python
def calculate_factorial(n: int) -> int:
    """
    Calculate the factorial of a number.
    
    Args:
        n (int): The number to calculate factorial for
        
    Returns:
        int: The factorial of n
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    
    return result
```

Generate ONLY the Python code with proper indentation. Do not include explanations, markdown formatting, or any text outside the code block.
"""

def extract_code(response: str) -> str:
    """Extract code from response"""
    import re
    
    # Look for code blocks
    code_patterns = [
        r'```python\n(.*?)\n```',  # Markdown code blocks
        r'```\n(.*?)\n```',        # Generic code blocks
        r'```(.*?)```',            # Code blocks without language
        r'`(.*?)`'                 # Inline code
    ]
    
    for pattern in code_patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    # If no code blocks found, return the whole response
    return response.strip()

async def test_enhanced_prompts():
    """Test enhanced prompts for better code generation"""
    print("🧪 Testing enhanced prompt engineering...")
    
    try:
        # Initialize the model
        print("📦 Initializing CodeLlama:7b-instruct...")
        llm = OllamaLLM(model="codellama:7b-instruct", **CODECLLAMA_CONFIG)
        
        # Test cases
        test_cases = [
            {
                "name": "Simple function with proper indentation",
                "task": "Write a Python function that calculates the sum of all even numbers in a list"
            },
            {
                "name": "Class with methods and proper indentation",
                "task": "Create a Python class called Calculator with methods for add, subtract, multiply, and divide operations"
            },
            {
                "name": "Complex function with error handling",
                "task": "Write a Python function that reads a JSON file, validates the data, and returns a processed result with proper error handling"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 Test {i}: {test_case['name']}")
            print(f"Task: {test_case['task']}")
            
            # Create enhanced prompt
            prompt = create_enhanced_prompt(test_case['task'])
            
            # Get response
            response = llm.invoke(prompt)
            print(f"Response length: {len(response)} characters")
            
            # Extract code
            code = extract_code(response)
            print(f"Extracted code length: {len(code)} characters")
            
            # Show first few lines
            lines = code.split('\n')
            print("First 10 lines of generated code:")
            for j, line in enumerate(lines[:10], 1):
                print(f"  {j:2d}: {line}")
            
            # Check indentation
            indentation_issues = []
            for j, line in enumerate(lines, 1):
                if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    # Check if this line should be indented
                    if j > 1 and lines[j-2].strip().endswith(':'):
                        indentation_issues.append(f"Line {j}: '{line.strip()}' should be indented")
            
            if indentation_issues:
                print("⚠️ Indentation issues found:")
                for issue in indentation_issues:
                    print(f"  - {issue}")
            else:
                print("✅ No obvious indentation issues found")
        
        print("\n✅ Enhanced prompt testing completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing enhanced prompts: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting enhanced prompt engineering tests...")
    
    success = await test_enhanced_prompts()
    
    if success:
        print("\n🎉 Enhanced prompt engineering test completed successfully!")
        print("💡 The improved prompts should generate better indented code!")
    else:
        print("\n❌ Enhanced prompt engineering test failed!")
        print("🔧 Please check your Ollama installation and model")

if __name__ == "__main__":
    asyncio.run(main()) 