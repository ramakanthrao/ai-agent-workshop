import json
from src.agent.agent import clean_json_response

# Test the problematic JSON
test_json = r'''
{
  "analysis": "test",
  "actions": [
    {"tool": "get", "params": {"code": $result_last}, "desc": "test"},
    {"tool": "write", "params": {"code": $result_-2}, "desc": "test"}
  ]
}
'''

print('Original:')
print(test_json)
print('\nCleaned:')
cleaned = clean_json_response(test_json)
print(cleaned)
print('\nTrying to parse...')
try:
    parsed = json.loads(cleaned)
    print('✓ Successfully parsed!')
    print(parsed)
except json.JSONDecodeError as e:
    print(f'✗ Parse error: {e}')
