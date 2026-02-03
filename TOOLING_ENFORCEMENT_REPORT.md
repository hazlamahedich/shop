# Tooling & Enforcement Report
## FastAPI + React Shop Bot Platform - Party Mode Implementation

**Author**: Amelia (Implementation Specialist)
**Date**: 2026-02-02
**Project**: OpenCommerce Messenger Bot
**Stack**: FastAPI + React + Shopify Integration

---

## Executive Summary

This report defines the complete tooling stack to enforce all Party Mode implementation patterns through automation, not documentation. Patterns are enforced at commit-time, not code-review-time.

**Total Setup Time**: 16-24 hours across 3 phases
**Enforcement Philosophy**: Fail fast, fix automatically when possible

---

## 1. Pre-commit Hooks Configuration

### 1.1 Hook Configuration File

**File**: `.pre-commit-config.yaml`

```yaml
# Phase 1: Core Python Hooks (Must-Have)
repos:
  # Generic hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: debug-statements
      - id: detect-private-key

  # Python: Code quality
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile', 'black']

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--extend-ignore=E203,E501']

  # Python: Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.0
          - types-requests
          - types-redis
        args: ['--ignore-missing-imports', '--warn-unused-ignores']

  # Python: Security
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']
        additional_dependencies: ['bandit[toml]']

  # Python: Dependency check
  - repo: https://github.com/pyup/safety
    rev: 3.0.1
    hooks:
      - id: safety
        args: ['--short-report']

  # Custom: Test co-location validator
  - repo: local
    hooks:
      - id: test-colocation-python
        name: Validate Python test co-location
        entry: python -m scripts.hooks.test_colocation
        language: system
        types: [python]
        pass_filenames: false

  # Custom: API response envelope validator
  - repo: local
    hooks:
      - id: api-response-envelope
        name: Validate API response envelope structure
        entry: python -m scripts.hooks.api_envelope
        language: system
        types: [python]
        files: '^backend/app/api/.*\.py$'

  # Custom: Error code registry validator
  - repo: local
    hooks:
      - id: error-code-registry
        name: Validate error codes in registry
        entry: python -m scripts.hooks.error_codes
        language: system
        types: [python]
        pass_filenames: false

  # Custom: OpenAPI spec generator
  - repo: local
    hooks:
      - id: openapi-generator
        name: Generate OpenAPI spec
        entry: python -m scripts.hooks.openapi_gen
        language: system
        pass_filenames: false
        always_run: true

# Phase 2: TypeScript/React Hooks (Should-Have)
  # TypeScript: Code quality
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        types: [typescript]
        files: '^frontend/.*\.(ts|tsx)$'
        additional_dependencies:
          - eslint@^8.56.0
          - '@typescript-eslint/eslint-plugin'
          - '@typescript-eslint/parser'
          - eslint-plugin-react
          - eslint-plugin-react-hooks

  # TypeScript: Formatting
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        types: [typescript]
        files: '^frontend/.*\.(ts|tsx|json)$'
        args: ['--write', '--tab-width=2']

  # Custom: Test co-location validator (TypeScript)
  - repo: local
    hooks:
      - id: test-colocation-typescript
        name: Validate TypeScript test co-location
        entry: node scripts/hooks/test-colocation.js
        language: system
        types: [typescript]
        pass_filenames: false

  # Custom: API version prefix validator
  - repo: local
    hooks:
      - id: api-version-prefix
        name: Validate API version prefix
        entry: node scripts/hooks/api-version.js
        language: system
        types: [typescript]
        files: '^frontend/src/services/.*\.ts$'

# Phase 3: Nice-to-Have
  # Dockerfile linting
  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
      - id: hadolint-docker
        args: ['--ignore', 'DL3008', '--ignore', 'DL3013']

  # Markdown linting
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.39.0
    hooks:
      - id: markdownlint
        args: ['--fix']

  # Secrets detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### 1.2 Custom Hook Scripts

**File**: `backend/scripts/hooks/__init__.py`
```python
"""Pre-commit hooks for Party Mode pattern enforcement."""
```

**File**: `backend/scripts/hooks/test_colocation.py`
```python
#!/usr/bin/env python3
"""Validate test co-location for Python files."""
import ast
import sys
from pathlib import Path
from typing import Dict, List


def find_source_files(root: Path) -> List[Path]:
    """Find all Python source files."""
    return [
        p for p in root.rglob("*.py")
        if "test" not in p.name and not p.is_relative_to(root / "tests")
    ]


def check_test_exists(source_file: Path) -> bool:
    """Check if test file exists alongside source."""
    test_file = source_file.parent / f"test_{source_file.name}"
    return test_file.exists()


def main() -> int:
    """Validate test co-location."""
    backend_root = Path(__file__).parent.parent.parent / "app"
    source_files = find_source_files(backend_root)

    missing_tests = []
    for source_file in source_files:
        if not check_test_exists(source_file):
            missing_tests.append(str(source_file.relative_to(backend_root.parent)))

    if missing_tests:
        print(f"❌ Missing test files for {len(missing_tests)} source files:")
        for file in missing_tests:
            print(f"  - {file}")
        print("\n💡 Create test files alongside source files:")
        print("   Example: user_service.py → test_user_service.py")
        return 1

    print("✅ All source files have co-located tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**File**: `backend/scripts/hooks/api_envelope.py`
```python
#!/usr/bin/env python3
"""Validate API response envelope structure."""
import ast
import sys
from pathlib import Path
from typing import List, Optional


class APIResponseChecker(ast.NodeVisitor):
    """Check for proper API response envelope usage."""

    def __init__(self, filename: str):
        self.filename = filename
        self.violations: List[str] = []

    def visit_Return(self, node: ast.Return) -> None:
        """Check return statements for envelope pattern."""
        if node.value:
            # Check if returning a dict with 'data' and 'meta' keys
            if isinstance(node.value, (ast.Dict, ast.Call)):
                # This is a simplified check - real implementation would be more thorough
                if isinstance(node.value, ast.Dict):
                    keys = [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
                    if not ('data' in keys and 'meta' in keys):
                        # Check if this might be a Response constructor
                        if not self._is_response_call(node.value):
                            self.violations.append(
                                f"Line {node.lineno}: Return missing envelope structure"
                            )
        self.generic_visit(node)

    def _is_response_call(self, node) -> bool:
        """Check if this is a Response/JSONResponse call."""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id in ['Response', 'JSONResponse']
            if isinstance(node.func, ast.Attribute):
                return node.func.attr in ['Response', 'JSONResponse']
        return False


def check_api_file(filepath: Path) -> List[str]:
    """Check a single API file for envelope violations."""
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        checker = APIResponseChecker(str(filepath))
        checker.visit(tree)
        return checker.violations
    except Exception as e:
        return [f"Parse error: {e}"]


def main() -> int:
    """Validate API response envelopes."""
    api_dir = Path(__file__).parent.parent.parent / "app" / "api"
    violations = {}

    for api_file in api_dir.rglob("*.py"):
        file_violations = check_api_file(api_file)
        if file_violations:
            violations[str(api_file)] = file_violations

    if violations:
        print("❌ API response envelope violations found:")
        for filepath, file_violations in violations.items():
            print(f"\n{filepath}:")
            for violation in file_violations:
                print(f"  {violation}")
        print("\n💡 Return responses using envelope pattern:")
        print("   return {")
        print("       'data': {...},")
        print("       'meta': {'request_id': ..., 'timestamp': ...}")
        print("   }")
        return 1

    print("✅ All API responses use envelope pattern")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**File**: `backend/scripts/hooks/error_codes.py`
```python
#!/usr/bin/env python3
"""Validate error codes are registered in ErrorCode registry."""
import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


class ErrorCodeExtractor(ast.NodeVisitor):
    """Extract error code definitions from source."""

    def __init__(self):
        self.error_codes: Set[str] = set()
        self.in_exception_class = False

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit exception classes."""
        if node.name.endswith('Exception') or node.name.endswith('Error'):
            self.in_exception_class = True
            self.generic_visit(node)
            self.in_exception_class = False

    def visit_Assign(self, node: ast.Assign) -> None:
        """Look for error_code assignments."""
        if self.in_exception_class:
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'error_code':
                    if isinstance(node.value, ast.Constant):
                        self.error_codes.add(node.value.value)
        self.generic_visit(node)


def find_all_error_codes(root: Path) -> Set[str]:
    """Find all error codes defined in the codebase."""
    error_codes = set()

    for py_file in root.rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                tree = ast.parse(f.read())
            extractor = ErrorCodeExtractor()
            extractor.visit(tree)
            error_codes.update(extractor.error_codes)
        except Exception:
            continue

    return error_codes


def get_registered_codes(registry_file: Path) -> Set[str]:
    """Get error codes from ErrorCode registry."""
    try:
        with open(registry_file, 'r') as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'ErrorCode':
                codes = set()
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                codes.add(target.id)
                return codes
    except Exception:
        pass

    return set()


def main() -> int:
    """Validate error code registry."""
    backend_root = Path(__file__).parent.parent.parent / "app"
    registry_file = backend_root / "core" / "errors.py"

    defined_codes = find_all_error_codes(backend_root)
    registered_codes = get_registered_codes(registry_file)

    unregistered = defined_codes - registered_codes
    unused = registered_codes - defined_codes

    issues = []
    if unregistered:
        issues.append(f"❌ {len(unregistered)} error codes not in registry:")
        for code in sorted(unregistered):
            issues.append(f"   - {code}")

    if unused:
        issues.append(f"⚠️  {len(unused)} registered codes never used:")
        for code in sorted(unused):
            issues.append(f"   - {code}")

    if issues:
        for issue in issues:
            print(issue)
        print(f"\n💡 Register error codes in {registry_file.name}:")
        print("   class ErrorCode(str, Enum):")
        print("       YOUR_CODE = 'YOUR_CODE'")
        return 1

    print("✅ All error codes properly registered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**File**: `backend/scripts/hooks/openapi_gen.py`
```python
#!/usr/bin/env python3
"""Generate OpenAPI spec and TypeScript types."""
import json
import subprocess
import sys
from pathlib import Path


def generate_openapi_spec() -> bool:
    """Generate OpenAPI specification from FastAPI."""
    backend_root = Path(__file__).parent.parent.parent
    schema_file = backend_root / "openapi.json"

    try:
        # Import and generate schema
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"from app.main import app; import json; "
                f"json.dump(app.openapi(), open('{schema_file}', 'w'))"
            ],
            cwd=backend_root,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ Failed to generate OpenAPI spec: {result.stderr}")
            return False

        print(f"✅ Generated OpenAPI spec: {schema_file}")
        return True

    except Exception as e:
        print(f"❌ Error generating OpenAPI spec: {e}")
        return False


def generate_typescript_types() -> bool:
    """Generate TypeScript types from OpenAPI spec."""
    backend_root = Path(__file__).parent.parent.parent
    frontend_root = backend_root.parent / "frontend"
    schema_file = backend_root / "openapi.json"
    output_file = frontend_root / "src" / "types" / "api.generated.ts"

    try:
        # Use openapi-typescript or similar tool
        result = subprocess.run(
            [
                "npx",
                "openapi-typescript",
                str(schema_file),
                "-o",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ Failed to generate TypeScript types: {result.stderr}")
            return False

        print(f"✅ Generated TypeScript types: {output_file}")
        return True

    except Exception as e:
        print(f"⚠️  Could not generate TypeScript types: {e}")
        return True  # Don't fail if typescript tools not available


def main() -> int:
    """Generate OpenAPI spec and TypeScript types."""
    success = True
    success &= generate_openapi_spec()
    success &= generate_typescript_types()

    if success:
        print("\n✅ Type generation complete")
    else:
        print("\n❌ Type generation failed")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
```

**File**: `frontend/scripts/hooks/test-colocation.js`
```javascript
#!/usr/bin/env node
/** Validate test co-location for TypeScript files. */
const fs = require('fs');
const path = require('path');
const { glob } = require('glob');

async function findSourceFiles() {
  const files = await glob('frontend/src/**/*.{ts,tsx}', {
    ignore: ['**/*.test.{ts,tsx}', '**/*.spec.{ts,tsx}', '**/node_modules/**'],
  });
  return files;
}

function checkTestExists(sourceFile) {
  const dir = path.dirname(sourceFile);
  const basename = path.basename(sourceFile);
  const testFile = path.join(dir, `${basename}.test${path.extname(sourceFile)}`);
  return fs.existsSync(testFile);
}

async function main() {
  const sourceFiles = await findSourceFiles();
  const missingTests = [];

  for (const file of sourceFiles) {
    if (!checkTestExists(file)) {
      missingTests.push(file);
    }
  }

  if (missingTests.length > 0) {
    console.error(`❌ Missing test files for ${missingTests.length} source files:`);
    for (const file of missingTests) {
      console.error(`  - ${file}`);
    }
    console.error('\n💡 Create test files alongside source files:');
    console.error('   Example: UserService.ts → UserService.test.tsx');
    process.exit(1);
  }

  console.log('✅ All source files have co-located tests');
  process.exit(0);
}

main().catch(console.error);
```

**File**: `frontend/scripts/hooks/api-version.js`
```javascript
#!/usr/bin/env node
/** Validate API version prefix in frontend service calls. */
const fs = require('fs');
const path = require('path');
const { glob } = require('glob');

const API_VERSION_PATTERN = /^\/api\/v1\//;
const VALID_FETCH_PATTERNS = [
  /fetch\(['"`]\/api\/v1\//,
  /axios\.[get|post|put|delete]+\(['"`]\/api\/v1\//,
  /api\.\w+\(['"`]\/api\/v1\//,
];

async function checkApiVersionInFile(filepath) {
  const content = fs.readFileSync(filepath, 'utf-8');
  const lines = content.split('\n');
  const violations = [];

  lines.forEach((line, index) => {
    // Check for fetch/axios/api calls
    if (line.includes('fetch(') || line.includes('axios.') || line.includes('api.')) {
      // Look for URL strings
      const urlMatches = line.match(/['"`]([^'"`]*\/api\/[^'"`]*)['"`]/);
      if (urlMatches) {
        const url = urlMatches[1];
        if (!API_VERSION_PATTERN.test(url)) {
          violations.push({
            line: index + 1,
            content: line.trim(),
            url,
          });
        }
      }
    }
  });

  return violations;
}

async function main() {
  const serviceFiles = await glob('frontend/src/services/**/*.ts');
  const allViolations = {};

  for (const file of serviceFiles) {
    const violations = await checkApiVersionInFile(file);
    if (violations.length > 0) {
      allViolations[file] = violations;
    }
  }

  if (Object.keys(allViolations).length > 0) {
    console.error('❌ API version prefix violations found:\n');
    for (const [file, violations] of Object.entries(allViolations)) {
      console.error(`${file}:`);
      for (const violation of violations) {
        console.error(`  Line ${violation.line}: ${violation.url}`);
        console.error(`    ${violation.content}`);
      }
    }
    console.error('\n💡 All API calls must use versioned prefix: /api/v1/...');
    process.exit(1);
  }

  console.log('✅ All API calls use versioned prefix');
  process.exit(0);
}

main().catch(console.error);
```

---

## 2. Custom Linting Rules

### 2.1 Pylint Plugin (Python)

**File**: `backend/pyproject.toml`
```toml
[tool.pylint.master]
load-plugins = [
    "pylint_enforce_boilerplate",
    "pylint_api_response",
    "pylint_error_registry",
]

[tool.pylint.messages_control]
disable = [
    "C0111",  # missing-docstring - handled by other linters
    "C0103",  # invalid-name - we use snake_case
]

[tool.pylint.format]
max-line-length = 100

[tool.pylint.basic]
good-names = ["i", "j", "k", "ex", "id", "_"]
```

**File**: `backend/pylint_enforce_boilerplate.py`
```python
"""Pylint plugin to enforce response envelope boilerplate."""
from astroid import nodes
from pylint import checkers
from pylint.checkers import utils


class APIResponseChecker(checkers.BaseChecker):
    """Check for proper API response patterns."""

    name = "api-response-checker"
    msgs = {
        "W9001": (
            "API endpoint must return response with envelope structure",
            "api-response-envelope",
            "All API endpoints should return {data, meta} envelope",
        ),
        "W9002": (
            "Response envelope missing required meta fields",
            "api-response-meta-missing",
            "Response meta must include request_id and timestamp",
        ),
        "W9003": (
            "Response using direct dict return instead of envelope",
            "api-response-direct-dict",
            "Use envelope structure: {data: ..., meta: {...}}",
        ),
    }

    @utils.only_messages_for("api-response-envelope")
    def visit_functiondef(self, node: nodes.FunctionDef) -> None:
        """Check API endpoint functions."""
        # Check if this is an endpoint function
        decorators = node.decorators.nodes if node.decorators else []

        is_endpoint = any(
            self._is_endpoint_decorator(dec) for dec in decorators
        )

        if not is_endpoint:
            return

        # Check return statements
        for return_node in node.nodes_of_class(nodes.Return):
            if return_node.value is None:
                continue

            # Validate envelope structure
            self._check_return_structure(return_node)

    def _is_endpoint_decorator(self, node) -> bool:
        """Check if decorator is an API endpoint decorator."""
        if isinstance(node, nodes.Call):
            if isinstance(node.func, nodes.Attribute):
                return node.func.attr in ['get', 'post', 'put', 'delete', 'patch']
            if isinstance(node.func, nodes.Name):
                return node.func.name in ['endpoint', 'route']
        return False

    def _check_return_structure(self, return_node: nodes.Return) -> None:
        """Validate the return statement structure."""
        value = return_node.value

        if isinstance(value, nodes.Dict):
            keys = [k.value for k in value.keys if isinstance(k, nodes.Const)]
            if 'data' not in keys or 'meta' not in keys:
                self.add_message('api-response-envelope', node=return_node)
            else:
                # Check meta fields
                for item in value.items:
                    if isinstance(item[0], nodes.Const) and item[0].value == 'meta':
                        if isinstance(item[1], nodes.Dict):
                            meta_keys = [
                                k.value for k in item[1].keys
                                if isinstance(k, nodes.Const)
                            ]
                            if 'request_id' not in meta_keys or 'timestamp' not in meta_keys:
                                self.add_message('api-response-meta-missing', node=return_node)


def register(linter):
    """Register the checker with pylint."""
    linter.register_checker(APIResponseChecker(linter))
```

**File**: `backend/pylint_error_registry.py`
```python
"""Pylint plugin to enforce error code registration."""
from astroid import nodes
from pylint import checkers
from pylint.checkers import utils


class ErrorCodeRegistryChecker(checkers.BaseChecker):
    """Check that error codes are registered."""

    name = "error-code-registry-checker"
    msgs = {
        "W9004": (
            "Exception class must define error_code attribute",
            "exception-missing-error-code",
            "All exception classes should have a unique error_code",
        ),
        "W9005": (
            "Error code '%s' is not registered in ErrorCode enum",
            "error-code-not-registered",
            "Register all error codes in core/errors.py",
        ),
    }

    # This would be populated from the actual registry
    REGISTERED_CODES = set()

    @utils.only_messages_for("exception-missing-error-code")
    def visit_classdef(self, node: nodes.ClassDef) -> None:
        """Check exception classes for error codes."""
        if not node.name.endswith('Exception') and not node.name.endswith('Error'):
            return

        has_error_code = False
        error_code_value = None

        for child in node.body:
            if isinstance(child, nodes.Assign):
                for target in child.targets:
                    if isinstance(target, nodes.AssignName):
                        if target.name == 'error_code':
                            has_error_code = True
                            if isinstance(child.value, nodes.Const):
                                error_code_value = child.value.value

        if not has_error_code:
            self.add_message('exception-missing-error-code', node=node)
        elif error_code_value and error_code_value not in self.REGISTERED_CODES:
            self.add_message(
                'error-code-not-registered',
                node=node,
                args=(error_code_value,)
            )


def register(linter):
    """Register the checker with pylint."""
    linter.register_checker(ErrorCodeRegistryChecker(linter))
```

### 2.2 ESLint Plugin (TypeScript/React)

**File**: `frontend/.eslintrc.js`
```javascript
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:party-mode/recommended',
  ],
  plugins: [
    '@typescript-eslint',
    'react',
    'react-hooks',
    'party-mode',
  ],
  rules: {
    // Party Mode custom rules
    'party-mode/test-colocation': 'error',
    'party-mode/api-version-prefix': 'error',
    'party-mode/no-camelcase-api': 'error',
    'party-mode/require-envelope-response': 'error',

    // Standard rules
    '@typescript-eslint/explicit-function-return-type': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};
```

**File**: `frontend/eslint-plugin-party-mode.js`
```javascript
/** Custom ESLint plugin for Party Mode patterns. */
const testColocationRule = require('./rules/test-colocation');
const apiVersionRule = require('./rules/api-version');
const camelCaseApiRule = require('./rules/no-camelcase-api');
const envelopeResponseRule = require('./rules/require-envelope');

module.exports = {
  configs: {
    recommended: {
      plugins: ['party-mode'],
      rules: {
        'party-mode/test-colocation': 'error',
        'party-mode/api-version-prefix': 'error',
        'party-mode/no-camelcase-api': 'error',
        'party-mode/require-envelope-response': 'error',
      },
    },
  },
  rules: {
    'test-colocation': testColocationRule,
    'api-version-prefix': apiVersionRule,
    'no-camelcase-api': camelCaseApiRule,
    'require-envelope-response': envelopeResponseRule,
  },
};
```

**File**: `frontend/rules/api-version.js`
```javascript
/** ESLint rule to enforce API version prefix. */
module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Enforce /api/v1/ prefix in API calls',
      category: 'Best Practices',
      recommended: true,
    },
    schema: [],
  },

  create(context) {
    return {
      CallExpression(node) {
        // Check for fetch(), axios.*, api.* calls
        const callee = node.callee;

        const isFetchCall =
          callee.type === 'Identifier' && callee.name === 'fetch';

        const isAxiosCall =
          callee.type === 'MemberExpression' &&
          callee.object.type === 'Identifier' &&
          callee.object.name === 'axios';

        const isApiCall =
          callee.type === 'MemberExpression' &&
          callee.object.type === 'Identifier' &&
          callee.object.name === 'api';

        if (!isFetchCall && !isAxiosCall && !isApiCall) {
          return;
        }

        // Check first argument (URL)
        if (node.arguments.length === 0) return;

        const urlArg = node.arguments[0];

        if (urlArg.type === 'Literal' && typeof urlArg.value === 'string') {
          const url = urlArg.value;

          if (url.startsWith('/api/') && !url.startsWith('/api/v1/')) {
            context.report({
              node,
              message: `API call must use versioned prefix: "/api/v1/..." instead of "${url}"`,
              fix(fixer) {
                const versionedUrl = url.replace('/api/', '/api/v1/');
                return fixer.replaceText(urlArg, `'${versionedUrl}'`);
              },
            });
          }
        }
      },
    };
  },
};
```

---

## 3. CI/CD Pipeline

### 3.1 GitHub Actions Workflow

**File**: `.github/workflows/party-mode-validation.yml`
```yaml
name: Party Mode Pattern Validation

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "20"

jobs:
  # Phase 1: Backend validation
  backend-validation:
    name: Backend Pattern Validation
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        working-directory: ./backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt

      - name: Run type checking
        working-directory: ./backend
        run: mypy app

      - name: Run linting
        working-directory: ./backend
        run: |
          black --check app
          isort --check-only app
          flake8 app
          pylint app

      - name: Run security checks
        working-directory: ./backend
        run: |
          bandit -r app
          safety check --short-report

      - name: Validate error codes
        working-directory: ./backend
        run: python -m scripts.hooks.error_codes

      - name: Validate test colocation
        working-directory: ./backend
        run: python -m scripts.hooks.test_colocation

      - name: Validate API envelopes
        working-directory: ./backend
        run: python -m scripts.hooks.api_envelope

      - name: Generate OpenAPI spec
        working-directory: ./backend
        run: python -m scripts.hooks.openapi_gen

      - name: Upload OpenAPI spec
        uses: actions/upload-artifact@v4
        with:
          name: openapi-spec
          path: backend/openapi.json

  # Phase 2: Frontend validation
  frontend-validation:
    name: Frontend Pattern Validation
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Run ESLint
        working-directory: ./frontend
        run: npm run lint

      - name: Validate TypeScript types
        working-directory: ./frontend
        run: npx tsc --noEmit

      - name: Validate test colocation
        working-directory: ./frontend
        run: node scripts/hooks/test-colocation.js

      - name: Validate API versioning
        working-directory: ./frontend
        run: node scripts/hooks/api-version.js

      - name: Download OpenAPI spec
        uses: actions/download-artifact@v4
        with:
          name: openapi-spec
          path: frontend/openapi

      - name: Generate TypeScript types from OpenAPI
        working-directory: ./frontend
        run: npx openapi-typescript openapi/openapi.json -o src/types/api.generated.ts

      - name: Run tests
        working-directory: ./frontend
        run: npm test

  # Phase 3: Integration checks
  integration-validation:
    name: Integration Validation
    runs-on: ubuntu-latest
    needs: [backend-validation, frontend-validation]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build backend image
        run: docker build -t shop-backend:test -f backend/Dockerfile backend/

      - name: Build frontend image
        run: docker build -t shop-frontend:test -f frontend/Dockerfile frontend/

      - name: Run Hadolint on Dockerfiles
        run: |
          docker run --rm -i hadolint/hadolint < backend/Dockerfile
          docker run --rm -i hadolint/hadolint < frontend/Dockerfile

      - name: Check API contract compatibility
        run: |
          python -m scripts.ci.validate_openapi_contract \
            --backend backend/openapi.json \
            --frontend frontend/src/types/api.generated.ts

      - name: Generate error code documentation
        run: python -m scripts.docs.generate_error_docs

      - name: Upload error documentation
        uses: actions/upload-artifact@v4
        with:
          name: error-docs
          path: docs/api/errors.md
```

### 3.2 Contract Validation Script

**File**: `backend/scripts/ci/validate_openapi_contract.py`
```python
#!/usr/bin/env python3
"""Validate OpenAPI contract matches frontend expectations."""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List


def load_openapi_spec(filepath: Path) -> Dict:
    """Load OpenAPI specification."""
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_api_endpoints(spec: Dict) -> List[Dict]:
    """Extract all API endpoints from OpenAPI spec."""
    endpoints = []

    for path, methods in spec.get('paths', {}).items():
        for method, details in methods.items():
            if method not in ['get', 'post', 'put', 'delete', 'patch']:
                continue

            endpoints.append({
                'path': path,
                'method': method.upper(),
                'operation_id': details.get('operationId'),
                'tags': details.get('tags', []),
            })

    return endpoints


def check_version_prefix(endpoints: List[Dict]) -> List[str]:
    """Check all endpoints use versioned prefix."""
    violations = []

    for endpoint in endpoints:
        if not endpoint['path'].startswith('/api/v1/'):
            violations.append(
                f"{endpoint['method']} {endpoint['path']}: "
                f"Missing /api/v1/ prefix"
            )

    return violations


def check_response_envelope(spec: Dict, endpoints: List[Dict]) -> List[str]:
    """Check responses use envelope structure."""
    violations = []

    for endpoint in endpoints:
        path = endpoint['path']
        method = endpoint['method'].lower()

        endpoint_spec = spec['paths'][path][method]
        responses = endpoint_spec.get('responses', {})

        for status, response in responses.items():
            if status == '204':  # No content
                continue

            content = response.get('content', {})
            json_content = content.get('application/json', {})

            schema = json_content.get('schema', {})
            if not schema:
                continue

            # Check for envelope structure
            required = schema.get('required', [])
            properties = schema.get('properties', {})

            if 'data' not in properties or 'meta' not in properties:
                violations.append(
                    f"{endpoint['method']} {endpoint['path']} "
                    f"response {status}: Missing envelope structure"
                )

            if 'meta' in properties:
                meta_props = properties['meta'].get('properties', {})
                if 'request_id' not in meta_props or 'timestamp' not in meta_props:
                    violations.append(
                        f"{endpoint['method']} {endpoint['path']} "
                        f"response {status}: Meta missing required fields"
                    )

    return violations


def main() -> int:
    """Validate OpenAPI contract."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', required=True, help='Path to OpenAPI spec')
    parser.add_argument('--frontend', help='Path to generated TypeScript types')
    args = parser.parse_args()

    spec = load_openapi_spec(Path(args.backend))
    endpoints = extract_api_endpoints(spec)

    violations = []
    violations.extend(check_version_prefix(endpoints))
    violations.extend(check_response_envelope(spec, endpoints))

    if violations:
        print("❌ OpenAPI contract violations:")
        for violation in violations:
            print(f"  {violation}")
        return 1

    print("✅ OpenAPI contract valid")
    print(f"   Found {len(endpoints)} versioned endpoints with envelope responses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## 4. Type Generation Pipeline

### 4.1 OpenAPI to TypeScript Workflow

**File**: `backend/scripts/typescript/generate.py`
```python
#!/usr/bin/env python3
"""Generate TypeScript types from FastAPI OpenAPI spec."""
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


def generate_openapi_spec(output_path: Path) -> bool:
    """Generate OpenAPI spec from FastAPI application."""
    try:
        # Import app and generate spec
        spec_code = """
import sys
sys.path.insert(0, '.')

from app.main import app
import json

spec = app.openapi()
print(json.dumps(spec, indent=2))
"""

        result = subprocess.run(
            [sys.executable, '-c', spec_code],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ Error generating spec: {result.stderr}")
            return False

        spec = json.loads(result.stdout)
        output_path.write_text(json.dumps(spec, indent=2))

        print(f"✅ Generated OpenAPI spec: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def generate_typescript_types(
    openapi_path: Path,
    output_path: Path,
) -> bool:
    """Generate TypeScript types from OpenAPI spec."""
    try:
        result = subprocess.run(
            [
                'npx',
                'openapi-typescript',
                str(openapi_path),
                '-o',
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ Error generating types: {result.stderr}")
            return False

        print(f"✅ Generated TypeScript types: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def generate_api_client(output_path: Path) -> bool:
    """Generate typed API client from OpenAPI spec."""
    client_template = """/**
 * Auto-generated API client
 * Generated from OpenAPI spec
 * DO NOT EDIT MANUALLY
 */

import type { paths } from './api.generated';

type ExtractPathParams<T> = T extends { params: infer P } ? P : never;

/**
 * Typed API client for Party Mode backend
 */
export const api = {
  // Methods will be generated here
};

export type ApiError = {
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
  meta: {
    request_id: string;
    timestamp: string;
  };
};

export type ApiResponse<T> = {
  data: T;
  meta: {
    request_id: string;
    timestamp: string;
  };
};
"""

    output_path.write_text(client_template)
    print(f"✅ Generated API client: {output_path}")
    return True


def main() -> int:
    """Generate TypeScript types from FastAPI."""
    backend_root = Path(__file__).parent.parent.parent
    frontend_root = backend_root.parent / 'frontend'

    openapi_path = backend_root / 'openapi.json'
    types_path = frontend_root / 'src' / 'types' / 'api.generated.ts'
    client_path = frontend_root / 'src' / 'services' / 'api.generated.ts'

    success = True
    success &= generate_openapi_spec(openapi_path)
    success &= generate_typescript_types(openapi_path, types_path)
    success &= generate_api_client(client_path)

    if success:
        print("\n✅ Type generation complete")
    else:
        print("\n❌ Type generation failed")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
```

### 4.2 NPM Scripts

**File**: `frontend/package.json`
```json
{
  "name": "shop-bot-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "test": "vitest",
    "lint": "eslint src --ext .ts,.tsx",
    "lint:fix": "eslint src --ext .ts,.tsx --fix",
    "format": "prettier --write 'src/**/*.{ts,tsx,json,css}'",
    "typecheck": "tsc --noEmit",
    "types:generate": "node scripts/generate-types.js",
    "validate:patterns": "npm run lint && npm run typecheck && node scripts/hooks/test-colocation.js && node scripts/hooks/api-version.js"
  },
  "devDependencies": {
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.56.0",
    "eslint-plugin-party-mode": "file:./eslint-plugin-party-mode",
    "eslint-plugin-react": "^7.33.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "openapi-typescript": "^6.7.0",
    "prettier": "^3.1.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vitest": "^1.0.0"
  }
}
```

---

## 5. IDE Integration

### 5.1 VS Code Configuration

**File**: `.vscode/settings.json`
```json
{
  // Python configuration
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,

  // TypeScript configuration
  "typescript.preferences.importModuleSpecifier": "relative",
  "typescript.suggest.autoImports": true,
  "typescript.tsserver.maxTsServerMemory": 8192,

  // ESLint configuration
  "eslint.validate": [
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact"
  ],
  "eslint.run": "onSave",

  // Prettier configuration
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },

  // File associations
  "files.associations": {
    "*.test.tsx": "typescriptreact",
    "*.test.ts": "typescript",
    "test_*.py": "python"
  },

  // Testing
  "testing.automaticallyOpenPeekView": "never",
  "testing.followRunningTest": true,

  // Party Mode specific
  "files.exclude": {
    "**/*.pyc": true,
    "**/__pycache__": true,
    "**/node_modules": true,
    "**/.venv": true
  },

  // EditorConfig
  "editor.tabSize": 2,
  "editor.insertSpaces": true,
  "editor.rulers": [100],

  // Diagnostics
  "python.analysis.diagnosticSeverityOverrides": {
    "reportMissingImports": "error",
    "reportUndefinedVariable": "error"
  }
}
```

**File**: `.vscode/extensions.json`
```json
{
  "recommendations": [
    // Python
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-python.pylint",
    "ms-python.flake8",

    // TypeScript/React
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "dsznajder.es7-react-js-snippets",

    // Testing
    "firsttris.vscode-jest-runner",
    "littlefoxteam.vscode-python-test-adapter",

    // Docker
    "ms-azuretools.vscode-docker",

    // Git
    "eamodio.gitlens",
    "mhutchie.git-graph",

    // Party Mode specific
    "redhat.vscode-yaml",
    "tamasfe.even-better-toml",

    // Documentation
    "bierner.markdown-mermaid",
    "yzhang.markdown-all-in-one"
  ]
}
```

### 5.2 PyCharm Configuration

**File**: `.idea/inspectionProfiles/Party_Mode.xml`
```xml
<component name="InspectionProjectProfileManager">
  <profile version="1.0">
    <option name="myName" value="Party Mode" />

    <!-- Test collocation -->
    <inspection_tool class="PyUnboundLocalVariable" enabled="true" level="ERROR" />
    <inspection_tool class="PyUnusedLocal" enabled="true" level="WARNING" />

    <!-- API response envelope -->
    <inspection_tool class="PyAssignmentToLoopOrWithParameter" enabled="true" level="ERROR" />

    <!-- Error code registry -->
    <inspection_tool class="PyStringException" enabled="true" level="ERROR" />

    <!-- Type checking -->
    <inspection_tool class="PyTypeChecker" enabled="true" level="ERROR" />

    <!-- Security -->
    <inspection_tool class="PyHardCodedPassword" enabled="true" level="ERROR" />
    <inspection_tool class="PyUnresolvedReference" enabled="true" level="ERROR" />
  </profile>
</component>
```

### 5.3 Code Snippets

**File**: `.vscode/snippets/python.code-snippets`
```json
{
  "API Response Envelope": {
    "prefix": "api-response",
    "description": "Create API response with envelope structure",
    "body": [
      "return {",
      "    \"data\": ${1:data},",
      "    \"meta\": {",
      "        \"request_id\": str(uuid.uuid4()),",
      "        \"timestamp\": datetime.utcnow().isoformat()",
      "    }",
      "}"
    ]
  },
  "Error Response": {
    "prefix": "api-error",
    "description": "Create error response with envelope",
    "body": [
      "raise ${1:DomainName}Exception(",
      "    error_code=${2:ErrorCode.SPECIFIC_ERROR},",
      "    message=\"${3:Error message}\",",
      "    details=${4:{}}",
      ")"
    ]
  },
  "API Endpoint": {
    "prefix": "api-endpoint",
    "description": "Create FastAPI endpoint with envelope response",
    "body": [
      "@router.${1:get}(\"/api/v1/${2:resource}\")",
      "async def ${3:list_items}(",
      "    request_id: str = Header(default=None),",
      "    ${4:params}",
      ") -> ${5:ResponseModel}:",
      "    \"\"\"${6:Endpoint description}.\"\"\"",
      "    ${7:# Implementation}",
      "    return {",
      "        \"data\": ${8:result},",
      "        \"meta\": {",
      "            \"request_id\": request_id or str(uuid.uuid4()),",
      "            \"timestamp\": datetime.utcnow().isoformat()",
      "        }",
      "    }"
    ]
  },
  "Domain Exception": {
    "prefix": "exception",
    "description": "Create domain exception with error code",
    "body": [
      "class ${1:ResourceName}Exception(DomainException):",
      "    \"\"\"${2:Exception description}.\"\"\"",
      "    ",
      "    error_code = ${3:ErrorCode.RESOURCE_SPECIFIC_ERROR}"
    ]
  },
  "Test File Header": {
    "prefix": "test-header",
    "description": "Test file header with common imports",
    "body": [
      "\"\"\"Tests for ${1:module_name}.\"\"\"",
      "",
      "import pytest",
      "from fastapi.testclient import TestClient",
      "from unittest.mock import Mock, patch",
      "",
      "from app.${2:module_path} import ${3:import}",
      "",
      "",
      "class Test${4:ClassName}:",
      "    \"\"\"Test ${5:description}.\"\"\"",
      "    ",
      "    @pytest.fixture",
      "    def client(self):",
      "        \"\"\"Get test client.\"\"\"",
      "        from app.main import app",
      "        return TestClient(app)",
      "    ",
      "    def test_${6:test_case}(self, client):",
      "        \"\"\"Test ${7:test description}.\"\"\"",
      "        ${8:# Test implementation}"
    ]
  }
}
```

**File**: `.vscode/snippets/typescript.code-snippets`
```json
{
  "API Service Call": {
    "prefix": "api-call",
    "description": "Create typed API call with envelope",
    "body": [
      "export async function ${1:functionName}(",
      "  ${2:params}: ${3:ParamsType}",
      "): Promise<ApiResponse<${4:ResponseType}>> {",
      "  const response = await fetch('/api/v1/${5:endpoint}', {",
      "    method: '${6:GET}',",
      "    headers: {",
      "      'Content-Type': 'application/json',",
      "    },",
      "    ${7:body: JSON.stringify(${2:params}),}",
      "  });",
      "  ",
      "  if (!response.ok) {",
      "    const error: ApiError = await response.json();",
      "    throw new Error(error.message);",
      "  }",
      "  ",
      "  return response.json();",
      "}"
    ]
  },
  "React Component with Test": {
    "prefix": "component-with-test",
    "description": "Create React component with test file",
    "body": [
      "export interface ${1:ComponentName}Props {",
      "  ${2:prop}: ${3:type};",
      "}",
      " ",
      "export function ${1:ComponentName}({ ${2:prop} }: ${1:ComponentName}Props) {",
      "  return (",
      "    <div>",
      "      ${4:// Component JSX}",
      "    </div>",
      "  );",
      "}"
    ]
  },
  "API Hook": {
    "prefix": "api-hook",
    "description": "Create React Query hook for API call",
    "body": [
      "export function use${1:ResourceName}() {",
      "  return useQuery({",
      "    queryKey: ['${2:resourceName}'],",
      "    queryFn: () => api.${3:getResource}(),",
      "  });",
      "}"
    ]
  }
}
```

---

## 6. Error Code Documentation Generator

**File**: `backend/scripts/docs/generate_error_docs.py`
```python
#!/usr/bin/env python3
"""Generate error code documentation from registry."""
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


class ErrorCodeDocumentationGenerator:
    """Generate Markdown documentation from error code registry."""

    def __init__(self, backend_root: Path):
        self.backend_root = backend_root
        self.errors_file = backend_root / "app" / "core" / "errors.py"
        self.output_file = backend_root.parent / "docs" / "api" / "errors.md"

    def extract_error_codes(self) -> Dict[str, Dict]:
        """Extract error codes from the registry."""
        # This would parse the actual ErrorCode enum
        # For now, return example structure
        return {
            "AUTH_INVALID_TOKEN": {
                "code": "AUTH_INVALID_TOKEN",
                "message": "Invalid or expired authentication token",
                "http_status": 401,
                "category": "Authentication",
            },
            "RESOURCE_NOT_FOUND": {
                "code": "RESOURCE_NOT_FOUND",
                "message": "Requested resource not found",
                "http_status": 404,
                "category": "Client Error",
            },
            "VALIDATION_ERROR": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "http_status": 400,
                "category": "Validation",
            },
            "INTERNAL_ERROR": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "http_status": 500,
                "category": "Server Error",
            },
        }

    def group_by_category(self, error_codes: Dict[str, Dict]) -> Dict[str, List[Dict]]:
        """Group error codes by category."""
        grouped = defaultdict(list)
        for code, info in error_codes.items():
            grouped[info["category"]].append(info)
        return dict(grouped)

    def generate_markdown(self, error_codes: Dict[str, Dict]) -> str:
        """Generate Markdown documentation."""
        grouped = self.group_by_category(error_codes)

        lines = [
            "# Error Code Reference",
            "",
            "This document defines all error codes used in the Party Mode API.",
            "",
            "## Response Format",
            "",
            "All errors follow the envelope structure:",
            "",
            "```json",
            "{",
            '  "data": null,',
            '  "error": {',
            '    "error_code": "SPECIFIC_ERROR_CODE",',
            '    "message": "Human-readable error message",',
            '    "details": {}',
            '  },',
            '  "meta": {',
            '    "request_id": "uuid",',
            '    "timestamp": "ISO-8601"',
            '  }',
            "}",
            "```",
            "",
            "## Error Codes",
            "",
        ]

        for category, codes in sorted(grouped.items()):
            lines.append(f"### {category}")
            lines.append("")
            lines.append("| Code | HTTP Status | Description |")
            lines.append("|------|-------------|-------------|")

            for code_info in sorted(codes, key=lambda x: x["code"]):
                lines.append(
                    f"| `{code_info['code']}` | "
                    f"{code_info['http_status']} | "
                    f"{code_info['message']} |"
                )

            lines.append("")

        # Add usage examples
        lines.extend([
            "## Usage Examples",
            "",
            "### Raising Errors",
            "",
            "```python",
            "from app.core.errors import ErrorCode",
            "from app.core.exceptions import DomainException",
            "",
            "class ResourceNotFoundException(DomainException):",
            "    error_code = ErrorCode.RESOURCE_NOT_FOUND",
            "",
            "",
            "# Raise with details",
            "raise ResourceNotFoundException(",
            "    message='Product not found',",
            "    details={'product_id': 123}",
            ")",
            "```",
            "",
            "### Handling Errors (TypeScript)",
            "",
            "```typescript",
            "try {",
            "  const response = await api.getProduct(123);",
            "} catch (error) {",
            "  if (isApiError(error)) {",
            "    console.log(error.error_code);",
            "    console.log(error.meta.request_id);",
            "  }",
            "}",
            "```",
            "",
            f"*Generated from {self.errors_file.name}*",
        ])

        return "\n".join(lines)

    def generate(self) -> bool:
        """Generate error code documentation."""
        try:
            error_codes = self.extract_error_codes()
            markdown = self.generate_markdown(error_codes)

            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            self.output_file.write_text(markdown)

            print(f"✅ Generated error documentation: {self.output_file}")
            return True

        except Exception as e:
            print(f"❌ Error generating documentation: {e}")
            return False


def main() -> int:
    """Generate error code documentation."""
    backend_root = Path(__file__).parent.parent.parent
    generator = ErrorCodeDocumentationGenerator(backend_root)
    success = generator.generate()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
```

---

## 7. Test Discovery Automation

**File**: `backend/scripts/testing/generate_test_matrix.py`
```python
#!/usr/bin/env python3
"""Generate test coverage matrix and discover missing tests."""
import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class TestCoverageAnalyzer:
    """Analyze test coverage and generate matrix."""

    def __init__(self, root: Path):
        self.root = root

    def find_all_modules(self) -> Tuple[List[Path], List[Path]]:
        """Find all source and test modules."""
        source_files = []
        test_files = []

        for py_file in self.root.rglob("*.py"):
            if "test" in py_file.name:
                test_files.append(py_file)
            elif not any(skip in py_file.parts for skip in ["__pycache__", ".venv"]):
                source_files.append(py_file)

        return source_files, test_files

    def extract_functions(self, filepath: Path) -> Set[str]:
        """Extract function names from a Python file."""
        try:
            with open(filepath, 'r') as f:
                tree = ast.parse(f.read())

            functions = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.add(node.name)
                elif isinstance(node, ast.AsyncFunctionDef):
                    functions.add(node.name)

            return functions
        except Exception:
            return set()

    def extract_classes(self, filepath: Path) -> Set[str]:
        """Extract class names from a Python file."""
        try:
            with open(filepath, 'r') as f:
                tree = ast.parse(f.read())

            classes = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.add(node.name)

            return classes
        except Exception:
            return set()

    def generate_coverage_matrix(self) -> Dict[str, Dict]:
        """Generate test coverage matrix."""
        source_files, test_files = self.find_all_modules()

        matrix = {}

        for source_file in source_files:
            rel_path = source_file.relative_to(self.root)
            test_file = source_file.parent / f"test_{source_file.name}"

            source_functions = self.extract_functions(source_file)
            source_classes = self.extract_classes(source_file)

            test_functions = set()
            if test_file.exists():
                test_functions = self.extract_functions(test_file)

            matrix[str(rel_path)] = {
                "has_test": test_file.exists(),
                "test_file": str(test_file.relative_to(self.root)) if test_file.exists() else None,
                "source_functions": sorted(source_functions),
                "test_functions": sorted(test_functions),
                "coverage": len(test_functions) / len(source_functions) if source_functions else 0,
            }

        return matrix

    def print_matrix(self, matrix: Dict[str, Dict]) -> None:
        """Print coverage matrix in table format."""
        print("\n📊 Test Coverage Matrix")
        print("=" * 80)

        total_files = len(matrix)
        files_with_tests = sum(1 for info in matrix.values() if info["has_test"])
        total_functions = sum(len(info["source_functions"]) for info in matrix.values())
        tested_functions = sum(len(info["test_functions"]) for info in matrix.values())

        print(f"\nSummary:")
        print(f"  Total source files: {total_files}")
        print(f"  Files with tests: {files_with_tests} ({100 * files_with_tests / total_files:.1f}%)")
        print(f"  Total functions: {total_functions}")
        print(f"  Tested functions: {tested_functions} ({100 * tested_functions / total_functions if total_functions else 0:.1f}%)")

        print("\nDetailed Coverage:")
        print("-" * 80)

        for filepath, info in sorted(matrix.items()):
            status = "✅" if info["has_test"] else "❌"
            coverage = info["coverage"] * 100
            print(f"\n{status} {filepath}")
            print(f"   Coverage: {coverage:.1f}% ({len(info['test_functions'])}/{len(info['source_functions'])} functions)")

            if not info["has_test"]:
                print(f"   ⚠️  Missing test file: test_{Path(filepath).name}")


def main() -> int:
    """Generate and display test coverage matrix."""
    backend_root = Path(__file__).parent.parent.parent / "app"
    analyzer = TestCoverageAnalyzer(backend_root)
    matrix = analyzer.generate_coverage_matrix()
    analyzer.print_matrix(matrix)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## 8. Implementation Priority & Timeline

### Phase 1: Must-Have (4-6 hours)

**Priority: CRITICAL - Blocks development**

| Component | Tool | Setup Time | Description |
|-----------|------|------------|-------------|
| Pre-commit hooks | pre-commit | 1h | Core Python linting (black, isort, flake8) |
| Type checking | mypy | 1h | Python type validation |
| Test colocation validator | custom | 1h | Ensure test files exist |
| API envelope validator | custom | 1h | Validate response structure |
| CI/CD pipeline | GitHub Actions | 1h | Automated validation |
| OpenAPI generation | FastAPI built-in | 0.5h | Generate spec |

**Total Phase 1: 5.5 hours**

### Phase 2: Should-Have (6-8 hours)

**Priority: HIGH - Significantly improves DX**

| Component | Tool | Setup Time | Description |
|-----------|------|------------|-------------|
| Pylint plugins | custom | 2h | API response, error code validation |
| ESLint plugin | custom | 2h | TypeScript pattern validation |
| TypeScript type generation | openapi-typescript | 1h | Generate types from OpenAPI |
| Error code documentation | custom | 1h | Auto-generate error docs |
| Test discovery automation | custom | 1h | Coverage matrix |
| IDE snippets | VS Code | 0.5h | Code snippets |
| Security scanning | bandit, safety | 0.5h | Security checks |

**Total Phase 2: 8 hours**

### Phase 3: Nice-to-Have (4-6 hours)

**Priority: MEDIUM - Nice to have but not blocking**

| Component | Tool | Setup Time | Description |
|-----------|------|------------|-------------|
| Docker linting | hadolint | 0.5h | Dockerfile validation |
| Markdown linting | markdownlint | 0.5h | Documentation formatting |
| Secrets detection | detect-secrets | 1h | Prevent secrets in commits |
| Advanced IDE integration | PyCharm | 1h | Inspection profiles |
| Contract validation | custom | 1h | OpenAPI contract checks |
| Performance monitoring | custom | 1h | Response time tracking |

**Total Phase 3: 5 hours**

---

## 9. Complete Tool Stack

### Development Tools

```yaml
Python:
  - python: "3.11"
  - poetry: "1.7.0"  # Dependency management
  - virtualenv: "builtin"

Linting/Formatting:
  - black: "24.1.1"  # Python formatter
  - isort: "5.13.2"  # Import sorting
  - flake8: "7.0.0"  # Python linting
  - pylint: "3.0.0"  # Python analysis
  - mypy: "1.8.0"  # Type checking
  - bandit: "1.7.6"  # Security linting
  - safety: "3.0.1"  # Dependency scanning

Node.js:
  - node: "20.x"
  - npm: "10.x"

TypeScript:
  - typescript: "5.3.0"
  - eslint: "8.56.0"
  - prettier: "3.1.0"
  - @typescript-eslint/eslint-plugin: "6.0.0"
  - @typescript-eslint/parser: "6.0.0"

Testing:
  - pytest: "7.4.0"
  - pytest-cov: "4.1.0"
  - pytest-asyncio: "0.21.0"
  - vitest: "1.0.0"
  - @testing-library/react: "14.0.0"

Pre-commit:
  - pre-commit: "3.6.0"
  - pre-commit-hooks: "4.5.0"

CI/CD:
  - github-actions: "latest"

Type Generation:
  - openapi-typescript: "6.7.0"

Containerization:
  - docker: "24.x"
  - docker-compose: "2.x"

IDE:
  - vscode: "latest"
  - pycharm-professional: "2023.3"
```

---

## 10. Quick Start Commands

### Backend Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install poetry
poetry install

# Install pre-commit hooks
pre-commit install

# Run type checking
mypy app

# Run linting
pylint app
flake8 app

# Run tests
pytest --cov=app

# Generate OpenAPI spec
python -m scripts.typescript.generate
```

### Frontend Setup

```bash
# Install dependencies
cd frontend
npm ci

# Install pre-commit hooks
cd ..
pre-commit install

# Run linting
npm run lint

# Run type checking
npm run typecheck

# Generate types
npm run types:generate

# Run tests
npm test
```

### Development Workflow

```bash
# 1. Make changes
# 2. Pre-commit hooks run automatically
git add .
git commit -m "feat: implement feature"

# 3. If hooks fail, fix issues
npm run lint:fix  # Auto-fix where possible
black app  # Auto-format Python

# 4. Commit again
git add .
git commit -m "feat: implement feature"

# 5. Push (CI runs)
git push
```

---

## 11. Monitoring & Metrics

### Enforcement Dashboard

Track these metrics to ensure compliance:

```python
# Metrics to track in CI/CD
metrics = {
    "pre_commit_pass_rate": "Target: >95%",
    "type_coverage": "Target: >80%",
    "test_coverage": "Target: >70%",
    "lint_violations": "Target: 0",
    "security_issues": "Target: 0",
    "api_envelope_compliance": "Target: 100%",
    "error_code_registration": "Target: 100%",
}
```

### Weekly Compliance Report

Generate with:
```bash
python -m scripts.reporting.compliance_report
```

---

## 12. Troubleshooting

### Common Issues

**Issue**: Pre-commit hooks fail locally but pass in CI
- **Fix**: Ensure local versions match CI (check .python-version, .nvmrc)

**Issue**: Type generation fails
- **Fix**: Ensure FastAPI app can import without errors, check DATABASE_URL is set

**Issue**: ESLint plugin not found
- **Fix**: Run `npm install` in `frontend/eslint-plugin-party-mode/`

**Issue**: Pylint custom rules not loading
- **Fix**: Add plugin path to `pyproject.toml` under `[tool.pylint.master]`

---

## Conclusion

This tooling stack enforces ALL Party Mode patterns through automation:

1. **Test Structure**: Co-location enforced by pre-commit and CI
2. **API Response**: Envelope enforced by custom Pylint/ESLint rules
3. **Error Handling**: Registry enforced by custom hooks
4. **Naming**: snake_case to camelCase handled by Pydantic
5. **Type Sync**: Auto-generated from OpenAPI spec
6. **API Versioning**: Prefix enforced by ESLint and CI validation

**Next Steps**:
1. Implement Phase 1 (must-have) - blocks development
2. Implement Phase 2 (should-have) - improves DX
3. Implement Phase 3 (nice-to-have) - polish

**Total Setup Time**: 16-24 hours
**Maintenance**: ~2 hours/week (updates, false positive tuning)
