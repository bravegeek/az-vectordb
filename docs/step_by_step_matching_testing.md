# Step-by-Step Guide: Starting the Customer Matching Testing Plan

This guide summarizes exactly where to start and what to do first, based on your matching testing plan and current project setup.

---

## 1. Generate Test Data

Use the script to create a set of "exact match" test cases:

```bash
python scripts/generate_incoming_customers.py --count 20 --intensity low --output-json data/test_cases/exact_match_test_data.json
```

This will generate controlled test data for validating exact matching.

---

## 2. Write/Run Exact Matching Tests

- Focus on **exact matching** for the first phase.
- The test file should be:
  - `tests/unit/test_exact_matching.py`
- If it doesn't exist, create it using the test case outlines in your plan (company name, email, phone, multiple fields, case sensitivity, etc.).
- Run the tests:

```bash
python -m pytest tests/unit/test_exact_matching.py -v
```

---

## 3. Validate Results

- Check that your matching logic finds the correct matches.
- Review confidence scores (should be 0.8–1.0 for exact matches).
- Confirm that the match criteria are correct.

---

## 4. Iterate

- If any tests fail, update your matching logic or test data as needed.
- Once exact matching is solid, move to vector and fuzzy matching in subsequent weeks.

---

## Summary Table

| Step | What to Do                  | Where/How                                      |
|------|-----------------------------|------------------------------------------------|
| 1    | Generate test data          | `scripts/generate_incoming_customers.py`        |
| 2    | Write/run exact match tests | `tests/unit/test_exact_matching.py`             |
| 3    | Validate results            | Review pytest output                            |
| 4    | Iterate/fix                 | Update code/tests as needed                     |

---

**Start with test data and exact matching tests, then proceed through the phases in your plan.**

## ✅ Current Status: Phase 1 Complete

**Exact Matching Tests: 10/10 PASSED** ✅

All exact matching functionality is working correctly:
- ✅ Company name matching
- ✅ Email matching  
- ✅ Phone matching
- ✅ Multiple field matching
- ✅ Case sensitivity handling
- ✅ Null value handling
- ✅ Whitespace handling (normalized)
- ✅ Confidence scoring
- ✅ No match scenarios
- ✅ Database integration

**Next Steps:**
1. Move to **Phase 2: Vector Matching** (Week 2)
2. Create `tests/unit/test_vector_matching.py`
3. Test semantic similarity matching

If you need help scaffolding the test file or reviewing your matching logic, just ask! 