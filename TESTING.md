# Testing Setup and Fixes

## Tailwind CSS Fix

We've updated the configuration files to work with Tailwind CSS v4:

1. Updated `postcss.config.js` to use the separate `@tailwindcss/postcss` package
2. Updated `tailwind.config.js` to use the new plugin format without require()

## Test Infrastructure

We've set up a comprehensive testing framework:

1. **Static Tests** (`test-static.js`):
   - Checks that all required files exist
   - Performs basic syntax validation
   - Tests the build process

2. **Vitest Tests**:
   - Unit tests for hooks (`useSocket`)
   - Integration tests for context (`ChatContext`)
   
3. **Manual Test Scripts**:
   - `test.js`: Verifies frontend setup and dependencies
   - `start-dev.bat`: Runs both backend and frontend together

## Running Tests

You can use the following commands from the frontend directory:

```bash
# Run static checks
npm run test:static

# Run unit and integration tests
npm run test

# Run tests in watch mode
npm run test:watch

# Verify setup and start dev server
npm run verify
```

## Dependencies

If any test dependencies are missing, you can install them with:

```bash
# From the project root
.\install-test-deps.bat
```

## Common Issues

1. **Tailwind CSS PostCSS Error**: Fixed by updating to use `@tailwindcss/postcss`
2. **Missing Dependencies**: Install required dependencies with the batch file
3. **ESLint Configuration**: If you encounter linting issues, a basic eslint config might be needed
