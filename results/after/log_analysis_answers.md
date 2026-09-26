# AI diagnoses of seeded build failures

Auto-score = the answer mentions the real cause. Read each one and correct the score by hand if needed.

## S1_logic_bug (run 1): Discount formula adds instead of subtracts

**Actual cause:** apply_discount uses (100 + percent) instead of (100 - percent)  
**Auto-score:** correct  
**Time:** 9.41s  

```
ROOT CAUSE: The function `apply_discount` is not correctly calculating the discounted price.
LOCATION: tests\test_app.py:35
FIX: Modify the apply_discount function to subtract the discount from the original price instead of adding it.
CONFIDENCE: high
```

## S2_syntax_error (run 1): Missing colon after function definition

**Actual cause:** SyntaxError: missing ':' after def get_port()  
**Auto-score:** correct  
**Time:** 10.31s  

```
ROOT CAUSE: Syntax error in the app.py file due to missing a colon after the function definition.
LOCATION: /var/jenkins_home/workspace/devops-ai-lab\app.py, line 22
FIX: Add a colon (':') after the def statement for the get_port() function in app.py.
CONFIDENCE: high
```

## S3_missing_dependency (run 1): New import not added to requirements

**Actual cause:** flask_cors (Flask-Cors) imported but not installed / not in requirements.txt  
**Auto-score:** correct  
**Time:** 6.39s  

```
ROOT CAUSE: The log indicates a missing module 'flask_cors'.
LOCATION: app.py at line 5
FIX: Install the flask_cors package.
CONFIDENCE: high
```

## S4_key_typo (run 1): Typo in dictionary key causes 500 error

**Actual cause:** KeyError: 'nmae' typo in get_product, should be 'name'  
**Auto-score:** correct  
**Time:** 10.55s  

```
ROOT CAUSE: The test for product_found is failing due to a KeyError: 'nmae'.
LOCATION: app.py:36
FIX: Check the spelling of the key in the product dictionary, it should be "name" instead of "nmae".
CONFIDENCE: high
```

## S5_config_typo (run 1): Default PORT '50OO' uses letter O instead of zero

**Actual cause:** Default port string '50OO' contains letter O, int() fails  
**Auto-score:** NOT matched  
**Time:** 9.06s  

```
ROOT CAUSE: The script `get_port()` is trying to convert a string '50OO' into an integer, causing a ValueError.
LOCATION: tests\test_app.py:52
FIX: Change the string '50OO' to '5000' in the line where it is used.
CONFIDENCE: high
```

## S6_wrong_status (run 1): Missing product returns 200 instead of 404

**Actual cause:** get_product returns status 200 instead of 404 for a missing product  
**Auto-score:** correct  
**Time:** 12.21s  

```
ROOT CAUSE: The test for checking if a missing product returns a 404 HTTP status code is failing because it's asserting that the response status code is 200, which is the correct status code for successful requests. However, in this case, a 404 (Not Found) should be expected.

LOCATION: tests/test_app.py:31

FIX: Change the assertion to check for a 404 HTTP status code instead of 200.

CONFIDENCE: high
```

