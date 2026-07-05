import os
import glob
import re

agent_dir = "d:/To_do_list_agent/app/agents"
for filepath in glob.glob(os.path.join(agent_dir, "*.py")):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # We want to replace LLMService.generate( ... ) with LLMService.generate(base_url=self.base_url, ... )
    # But some might be multi-line: 
    # LLMService.generate(
    #     model=self.model,
    
    # Regex approach: look for LLMService.generate( and check if base_url is already there
    new_content = re.sub(
        r'LLMService\.generate\(\s*(?!base_url=)',
        r'LLMService.generate(base_url=self.base_url, ',
        content
    )
    
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Patched {os.path.basename(filepath)}")
