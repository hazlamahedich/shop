# Widget Release Process

This document describes the process for releasing new versions of the ShopBot widget to the CDN.

## Release Checklist

### Pre-Release

1. **Update Version Number**
   ```bash
   cd frontend
   # Update version in package.json (e.g., "0.1.0" → "1.0.0")
   npm version major|minor|patch
   ```

2. **Run Full Test Suite**
   ```bash
   npm run test
   npm run test:e2e
   npm run lint
   ```

3. **Build Widget**
   ```bash
   npm run build:widget
   ```

4. **Verify Bundle Size**
   ```bash
   npm run build:widget:size
   # Bundle must be < 100KB gzipped
   ```

5. **Verify Version Embedded**
   ```bash
   grep -r "VITE_WIDGET_VERSION" dist/widget/widget.umd.js || echo "Version not found!"
   ```

5b. **Copy Bundle for E2E Testing** (Optional)
   ```bash
   # Copy fresh bundle to public/dist for E2E tests
   mkdir -p public/dist/widget
   cp dist/widget/widget.umd.js public/dist/widget/
   cp dist/widget/widget.es.js public/dist/widget/
   ```
   > **Note:** Build output is `dist/widget/`. The `public/dist/widget/` directory is a manual copy for E2E testing only. This directory is git-ignored.

### Deployment

6. **Upload to CDN**
   ```bash
   VERSION=$(node -p "require('./package.json').version")
   
   # Upload versioned files (example for S3)
   aws s3 sync dist/widget/ s3://cdn-bucket/widget/v/$VERSION/ \
     --cache-control "public, max-age=31536000, immutable"
   
   # Update latest symlink
   aws s3 sync dist/widget/ s3://cdn-bucket/widget/latest/ \
     --delete \
     --cache-control "public, max-age=3600, must-revalidate"
   ```

7. **Tag Git Release**
   ```bash
   git tag -a "widget-v$VERSION" -m "Widget release v$VERSION"
   git push origin "widget-v$VERSION"
   ```

### Post-Release

8. **Verify Deployment**
   - Test versioned URL loads correctly
   - Test latest URL points to new version
   - Check browser console for version: `window.ShopBotWidget.version`

9. **Update Documentation** (if needed)
   - Update integration examples with new version number
   - Document any new configuration options

10. **Notify Stakeholders**
    - Announce release in team channel
    - Update changelog/release notes

## CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/widget-release.yml`:

```yaml
name: Widget Release

on:
  push:
    tags: ['widget-v*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: cd frontend && npm ci
      
      - name: Run tests
        run: cd frontend && npm run test
      
      - name: Build widget
        run: cd frontend && npm run build:widget
      
      - name: Verify bundle size
        run: cd frontend && npm run build:widget:size
      
      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/widget-v}" >> $GITHUB_OUTPUT
      
      - name: Deploy to CDN
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.CDN_AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.CDN_AWS_SECRET_ACCESS_KEY }}
        run: |
          VERSION=${{ steps.version.outputs.VERSION }}
          
          # Upload versioned files
          aws s3 sync frontend/dist/widget/ s3://${{ secrets.CDN_BUCKET }}/widget/v/$VERSION/ \
            --cache-control "public, max-age=31536000, immutable"
          
          # Update latest
          aws s3 sync frontend/dist/widget/ s3://${{ secrets.CDN_BUCKET }}/widget/latest/ \
            --delete \
            --cache-control "public, max-age=3600, must-revalidate"
      
      - name: Invalidate CDN Cache
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CDN_DISTRIBUTION_ID }} \
            --paths "/widget/latest/*"
```

### Triggering a Release

```bash
# Create and push a tag to trigger CI/CD
cd frontend
npm version patch  # or minor, or major
git push origin main --tags
```

## Breaking Change Migration

When releasing a version with breaking changes (MAJOR version increment):

### Pre-Release Preparation

1. **Create Migration Guide**
   - Create `docs/widget-migration-v{OLD}-to-v{NEW}.md`
   - Document all deprecated APIs and their replacements
   - Provide code examples for migration

2. **Add Deprecation Warnings** (in previous MINOR release)
   ```typescript
   // In loader.ts, before removing an API
   if (config.deprecatedOption) {
     console.warn('[ShopBot Widget] deprecatedOption is deprecated. Use newOption instead.');
   }
   ```

### Release Process

3. **Keep Old Version Available**
   - Do NOT delete old versioned files from CDN
   - Minimum 90-day overlap period
   - Announce deprecation timeline

4. **Announce Breaking Changes**
   - Update documentation with migration guide links
   - Send notification to all merchants using the widget
   - Include deprecation timeline in release notes

### Example Migration Guide Structure

```markdown
# Migration Guide: v1.x to v2.0

## Breaking Changes

### Configuration Changes
- `theme.buttonColor` → `theme.primaryColor`
- `position` removed → use `theme.position`

### API Changes
- `window.ShopBotWidget.init()` removed → use `window.ShopBotConfig`

## Migration Steps

1. Update configuration object
2. Replace deprecated options
3. Test thoroughly before deploying to production

## Timeline
- v1.x support ends: [DATE]
- Migration period: 90 days
```

## Version Support Policy

| Version | Support Status | End of Support |
|---------|---------------|----------------|
| Latest | Full support | N/A |
| Previous MAJOR | Security fixes only | 90 days after new MAJOR |
| Older versions | No support | Ended |

## Rollback Procedure

If a critical issue is discovered after release:

1. **Immediate Rollback**
   ```bash
   # Restore previous version as "latest"
   aws s3 sync s3://cdn-bucket/widget/v/PREVIOUS_VERSION/ s3://cdn-bucket/widget/latest/ \
     --delete \
     --cache-control "public, max-age=3600, must-revalidate"
   
   # Invalidate cache
   aws cloudfront create-invalidation \
     --distribution-id $DISTRIBUTION_ID \
     --paths "/widget/latest/*"
   ```

2. **Communicate Issue**
   - Notify team of rollback
   - Document issue in changelog

3. **Fix and Re-release**
   - Fix the issue in development
   - Follow standard release process
   - Consider patch version increment

## Changelog Format

Maintain a `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [1.1.0] - 2026-02-20

### Added
- New theme customization options

### Changed
- Improved message rendering performance

### Fixed
- Session persistence bug on page refresh

## [1.0.0] - 2026-02-19

### Added
- Initial widget release
```

## Related Documentation

- [Widget CDN Setup](./widget-cdn-setup.md) - URL patterns and provider config
- [Widget CDN Caching](./widget-cdn-caching.md) - Cache header configuration
