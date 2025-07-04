# Customer Matching Service - Modular Architecture

This directory contains the refactored, modular customer matching service that follows SOLID principles and best practices for maintainable code.

## Architecture Overview

The matching service has been broken down into focused, single-responsibility classes:

```
app/services/matching/
├── __init__.py              # Package exports
├── base_matcher.py          # Abstract base class for matchers
├── exact_matcher.py         # Exact matching strategy
├── vector_matcher.py        # Vector similarity matching
├── fuzzy_matcher.py         # Fuzzy string matching
├── business_rules.py        # Business rules engine
├── result_processor.py      # Result processing and storage
├── utils.py                 # Common utility functions
├── matching_service.py      # Main orchestrator service
└── README.md               # This file
```

## Components

### 1. BaseMatcher (Abstract Base Class)
- Defines the interface for all matching strategies
- Ensures consistent API across different matchers
- Enables easy addition of new matching strategies

### 2. ExactMatcher
- Handles exact matching based on company name, email, and phone
- Uses SQLAlchemy queries for efficient database lookups
- Calculates weighted scores based on matched fields

### 3. VectorMatcher
- Performs vector similarity matching using embeddings
- Executes PostgreSQL pgvector queries
- Integrates with business rules engine for confidence adjustment

### 4. FuzzyMatcher
- Implements fuzzy string matching for company names
- Uses Python's difflib.SequenceMatcher
- Provides configurable similarity thresholds

### 5. BusinessRulesEngine
- Applies business rules to adjust confidence scores
- Handles industry, location, and revenue-based adjustments
- Configurable boost/penalty multipliers

### 6. ResultProcessor
- Deduplicates matches based on customer_id
- Sorts results by confidence level
- Handles database storage of matching results

### 7. MatchingUtils
- Common utility functions used across matchers
- Exact matching helper functions
- Match type determination logic

### 8. MatchingService (Main Orchestrator)
- Coordinates all matching strategies
- Provides unified interface for different matching approaches
- Maintains backward compatibility

## Benefits of This Architecture

### 1. Single Responsibility Principle
Each class has one clear purpose:
- `ExactMatcher` only handles exact matching
- `VectorMatcher` only handles vector similarity
- `BusinessRulesEngine` only applies business rules

### 2. Open/Closed Principle
- Easy to add new matching strategies by implementing `BaseMatcher`
- Existing code doesn't need modification to support new matchers

### 3. Dependency Inversion
- High-level modules don't depend on low-level modules
- Both depend on abstractions (BaseMatcher interface)

### 4. Testability
- Each component can be unit tested in isolation
- Mock dependencies easily for testing
- Clear interfaces make testing straightforward

### 5. Maintainability
- Smaller, focused classes are easier to understand and modify
- Changes to one strategy don't affect others
- Clear separation of concerns

### 6. Extensibility
- Add new matching strategies without changing existing code
- Configure which strategies to use via settings
- Easy to add new business rules

## Usage

### Basic Usage
```python
from app.services.matching import MatchingService

# Use the main service
matching_service = MatchingService()
results = matching_service.find_matches(incoming_customer, db)
```

### Using Individual Matchers
```python
from app.services.matching import ExactMatcher, VectorMatcher

# Use specific matchers
exact_matcher = ExactMatcher()
exact_results = exact_matcher.find_matches(incoming_customer, db)

vector_matcher = VectorMatcher()
vector_results = vector_matcher.find_matches(incoming_customer, db)
```

### Adding New Matchers
```python
from app.services.matching.base_matcher import BaseMatcher

class NewMatcher(BaseMatcher):
    def is_enabled(self) -> bool:
        return settings.enable_new_matching
    
    def find_matches(self, incoming_customer, db):
        # Implement new matching logic
        pass
```

## Migration from Old Service

The old `app/services/matching_service.py` has been deprecated but maintains backward compatibility:

- All existing code will continue to work
- Warnings are logged when using the deprecated service
- Gradually migrate to the new modular service

## Configuration

Each matcher respects the existing configuration settings:
- `settings.enable_exact_matching`
- `settings.enable_vector_matching`
- `settings.enable_fuzzy_matching`
- `settings.enable_business_rules`

## Testing

Each component can be tested independently:

```python
# Test exact matcher
def test_exact_matcher():
    matcher = ExactMatcher()
    results = matcher.find_matches(incoming_customer, mock_db)
    assert len(results) > 0

# Test business rules
def test_business_rules():
    engine = BusinessRulesEngine()
    confidence = engine.apply_rules(0.8, incoming_customer, customer_row)
    assert confidence > 0.8
```

## Performance Considerations

- Each matcher can be enabled/disabled independently
- Vector queries use efficient pgvector operations
- Fuzzy matching is limited by `settings.fuzzy_max_results`
- Database connections are reused across matchers

## Future Enhancements

1. **Caching Layer**: Add Redis caching for frequently matched customers
2. **Async Support**: Make matchers async for better performance
3. **Machine Learning**: Add ML-based matching strategies
4. **A/B Testing**: Support for testing different matching configurations
5. **Metrics**: Add detailed performance and accuracy metrics 