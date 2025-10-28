# Tests

This folder contains test scripts to check, validate, and test various components of the EmpathyScale project.

## Available Scripts

### `check_openai_key.py`
Checks if the OpenAI API key in `config.json` is valid and working.

**Usage:**
```bash
# From project root
python tests/check_openai_key.py

# Or from tests folder
cd tests
python check_openai_key.py
```

**What it does:**
- ✅ Loads configuration from `config.json`
- ✅ Validates API key format (starts with 'sk-', proper length)
- ✅ Makes a test API call to verify the key works
- ✅ Provides detailed error messages for troubleshooting

**Exit codes:**
- `0`: API key is valid and working
- `1`: API key is invalid, missing, or has errors

### `test_interview_simulation.py`
Comprehensive test script that simulates a complete user conversation to test Interview Agent Group functionality.

**Usage:**
```bash
# From project root
python tests/test_interview_simulation.py

# Or from tests folder
cd tests
python test_interview_simulation.py
```

**Features:**
- ✅ Simulates 8 rounds of conversation with realistic assessment scenario data
- ✅ Tests both conversation flow and data saving functionality
- ✅ Provides detailed statistics and classification analysis
- ✅ Includes direct data saving test
- ✅ Shows all collected data in organized format

**Output includes:**
- Configuration loading status
- Agent group creation status
- Complete conversation simulation
- Detailed interview summary
- Data classification analysis
- Summary statistics
- Direct data saving test results

### `quick_test.py`
Simplified test script for quick functionality verification of Interview Agent Group.

**Usage:**
```bash
# From project root
python tests/quick_test.py

# Or from tests folder
cd tests
python quick_test.py
```

**Features:**
- ✅ Simulates key conversation turns
- ✅ Shows truncated agent responses for readability
- ✅ Displays organized summary
- ✅ Quick completion status check

**Output includes:**
- Opening message
- Simulated conversation (truncated)
- Interview summary
- Completion status

## Test Data

Both test scripts use the same comprehensive test scenario:

1. **Assessment Context**: Collaborative robot assisting human workers in industrial assembly tasks
2. **Robot Platform**: Dual-arm manipulator with force feedback sensors and visual perception
3. **Collaboration Pattern**: Peer-to-peer collaboration with shared workspace and real-time coordination
4. **Environmental Setting**: Manufacturing floor with precision assembly stations and safety equipment
5. **Assessment Goals**: Emotional and cognitive support during complex tasks
6. **Expected Empathy Forms**: Adaptive responses, stress recognition, and supportive communication
7. **Assessment Challenges**: Measuring emotional trust and collaboration quality in high-stakes scenarios
8. **Measurement Requirements**: Scale capturing technical coordination and emotional rapport

## Expected Results

### Data Collection
- **assessment_context**: Should collect assembly/manufacturing/workers information
- **robot_platform**: Should collect dual-arm/manipulator/force feedback information
- **collaboration_pattern**: Should collect peer-to-peer/coordination/shared workspace information
- **environmental_setting**: Should collect manufacturing floor/assembly stations information
- **assessment_goals**: Should collect goal/assess/cognitive support information
- **expected_empathy_forms**: Should collect expect/observe/adaptive behavior information
- **assessment_challenges**: Should collect challenge/measuring/trust information
- **measurement_requirements**: Should collect scale/captures/coordination information

### Completion Status
- Should return `True` when sufficient data is collected
- Completion rate should be > 60%

### Agent Behavior
- Agent should use `save_interview_data` tool after each response
- Agent should ask follow-up questions about assessment scenario
- Agent should focus on empathy assessment aspects

## Troubleshooting

### Common Issues

1. **Empty Summary**: Check if agent is using `save_interview_data` tool
2. **Data Misclassification**: Check keyword matching logic in `save_interview_data` function
3. **Unicode Errors**: Ensure all Unicode characters are replaced with ASCII equivalents
4. **API Errors**: Verify OpenAI API key is valid and accessible

### Debug Steps

1. Run `quick_test.py` first for basic verification
2. Run `test_interview_simulation.py` for detailed analysis
3. Check agent tool usage in conversation output
4. Verify data classification in summary output
5. Check completion status and statistics

## Adding New Check Scripts

When adding new check scripts to this folder:

1. Follow the naming convention: `check_<component>.py` for validation scripts
2. Follow the naming convention: `test_<component>.py` for test scripts
3. Include proper error handling and exit codes
4. Add documentation to this README
5. Use the same configuration loading pattern as `check_openai_key.py`

## Notes

- All scripts require valid OpenAI API key in `config.json`
- Test scripts automatically handle non-interactive execution
- All Unicode characters have been replaced with ASCII equivalents for Windows compatibility
- Test data is designed to trigger all classification categories
- Scripts provide comprehensive output for debugging and verification
