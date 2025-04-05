# Private AI Proxy Test Suite

This directory contains unit tests and integration tests for the Private AI Proxy core modules.

## Test Files

### Unit Tests
- `test_pii_transform.py`: Tests for the PII transformation module
- `test_utils.py`: Tests for utility functions
- `test_codename_generator.py`: Tests for the codename generation module

### Integration Tests
- `test_integration_proxy.py`: Integration tests for the proxy request/response lifecycle with PII transformation
- `test_integration_api.py`: Integration tests for API endpoint functionality in `app.py`
- `test_integration_config.py`: Integration tests for configuration loading and saving

## Running Tests

### Running All Tests

To run all tests, use the provided test runner script:

```bash
./tests/run_tests.py
```

Or using Python directly:

```bash
python tests/run_tests.py
```

### Running Individual Test Files

To run tests for a specific module:

```bash
python -m unittest tests/test_pii_transform.py
python -m unittest tests/test_utils.py
python -m unittest tests/test_codename_generator.py
python -m unittest tests/test_integration_proxy.py
python -m unittest tests/test_integration_api.py
python -m unittest tests/test_integration_config.py
```

### Running Specific Test Cases

To run a specific test case:

```bash
python -m unittest tests.test_pii_transform.TestPIITransform.test_get_replacement_existing
```

## Test Coverage

The tests cover the following core functionality:

### Unit Tests Coverage

#### PII Transform Tests
- Replacement generation and retrieval
- Placeholder generation
- Text and JSON transformation
- Presidio integration
- Original value restoration

#### Utils Tests
- Database encryption
- Presidio initialization
- Pattern detection
- URL parameter transformation
- AI format detection and adaptation

#### Codename Generator Tests
- Industry detection
- Organization and domain codename generation
- Mapping import/export
- Database operations

### Integration Tests Coverage

#### Proxy Integration Tests
- Proxy request/response lifecycle
- PII detection and transformation in requests
- PII detection and transformation in responses
- Bidirectional transformation (request to response)
- Component integration without full proxy server

#### API Integration Tests
- API endpoint functionality
- Configuration management through API
- PII transformation through API
- Proxy control through API
- Domain and pattern management through API

#### Configuration Integration Tests
- Environment settings management
- Custom patterns loading and saving
- Domain blocklist loading and saving
- AI server configurations loading and saving
- AI domains loading and saving
- Database encryption functionality
- Configuration loading order and precedence

## Adding New Tests

When adding new functionality to the core modules, please add corresponding tests following these guidelines:

1. Create test methods in the appropriate test class
2. Use descriptive method names that explain what is being tested
3. Include assertions that verify the expected behavior
4. Use mocks for external dependencies when appropriate
5. Test both success and failure cases

## Test Dependencies

The tests require the following dependencies:

- unittest (standard library)
- sqlite3 (standard library)
- tempfile (standard library)
- unittest.mock (standard library)

No additional packages are required beyond what's already in the project's requirements.txt.