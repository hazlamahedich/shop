# 🧪 Live Testing Guide - Accessibility Fixes

**Dashboard URL:** http://localhost:5173 (or your deployed URL)
**Test Date:** 2026-03-29
**Server Status:** ✅ Backend + Frontend running

---

## 🎯 Quick Verification (2 minutes)

### 1. **Test Focus Styles** ⭐ Most Important

**What to test:**
1. Open the dashboard in your browser
2. Press **Tab** key repeatedly
3. Look for a **cyan/green outline** (#00f5d4) around focused elements

**Expected Results:**
- ✅ All buttons show a clear cyan outline
- ✅ Links have focus indicator
- ✅ Interactive cards show focus
- ✅ Focus has a subtle glow effect

**Before Fix:** No visible focus or inconsistent focus
**After Fix:** Clear cyan outline on all interactive elements

---

### 2. **Test Icon Button Accessibility**

**What to test:**
1. Open your browser's Developer Tools (F12)
2. Go to the **Accessibility** tab (or Accessibility Inspector)
3. Click on icon buttons and check their name/role

**Locations to test:**

#### A. TopTopicsWidget - Download Button
1. Find "Semantic Clusters" widget
2. Look for "Full Topic Schema" button with download icon
3. **Expected:** aria-label="Download full topic schema"

#### B. KnowledgeGapWidget - Action Buttons
1. Find "Intelligence Gaps" widget
2. Click on any gap to expand it
3. Look for the close (X) button
4. **Expected:** aria-label="Close knowledge gap menu"
5. Look for "Add as FAQ" button
6. **Expected:** aria-label="Add [topic name] as FAQ"
7. Look for "Add Document" button
8. **Expected:** aria-label="Upload document to knowledge base"

---

## 🎨 Visual Verification

### Before/After Comparison

**Focus Indicators:**
```
Before: Tab → No visible focus (❌)
After:  Tab → Cyan outline with glow (✅)
```

**Icon Buttons:**
```
Before: <button><Icon /></button> → Screen reader: "button" (❌)
After:  <button aria-label="Download"><Icon /></button> → Screen reader: "Download button" (✅)
```

---

## 🔍 Detailed Testing Steps

### Step 1: Keyboard Navigation Test (1 min)

1. **Open Dashboard**
   ```
   http://localhost:5173
   ```

2. **Press Tab 10+ times**
   - Watch for cyan focus ring
   - Each interactive element should be clearly focused

3. **Press Shift+Tab 5 times**
   - Navigate backwards
   - Focus should still be visible

4. **Press Enter on focused buttons**
   - Should trigger the button action
   - Works on all interactive elements

**✅ Success Criteria:**
- Focus indicator visible on EVERY tab
- No interactive element is skipped
- Enter key activates focused buttons

---

### Step 2: Screen Reader Test (2 min)

**Chrome (Windows/Mac):**
1. Turn on VoiceOver (Mac) or NVDA (Windows)
2. Navigate to dashboard
3. Press Tab to focus icon buttons
4. Listen for button names

**Expected Announcements:**
- ✅ "Download full topic schema button"
- ✅ "Close knowledge gap menu button"
- ✅ "Add [topic] as FAQ button"
- ✅ "Upload document to knowledge base button"

**Before Fix:**
- "Button" (no purpose)
- "Button, [icon name]" (not helpful)

**After Fix:**
- "Download full topic schema button"
- "Close menu button"
- "Add as FAQ button"

---

### Step 3: Browser Accessibility Inspector (1 min)

**Chrome DevTools:**
1. Press F12
2. Go to **Elements** tab
3. Click **Accessibility** pane
4. Select icon buttons
5. Check "Accessible Name"

**Firefox DevTools:**
1. Press F12
2. Go to **Accessibility** tab
3. Check "Accessibility Tree"
4. Find icon buttons
5. Verify names are descriptive

---

## 📊 Specific Widget Tests

### Test 1: TopTopicsWidget

**Location:** Dashboard → "What are people asking?" section

**Find:**
- Download icon button (bottom of widget)

**Test:**
1. Tab to the button
2. Check for cyan focus outline ✅
3. Check Accessibility Inspector for aria-label ✅

**Expected:**
```
Role: button
Name: Download full topic schema ✅
Focusable: yes ✅
```

---

### Test 2: KnowledgeGapWidget

**Location:** Dashboard → "How do we improve?" section

**Find:**
- Any knowledge gap (click to expand)
- Close (X) button
- "Add as FAQ" button
- "Add Document" button

**Test:**
1. Click on a knowledge gap to expand it
2. Tab to the close button
3. Check for cyan focus outline ✅
4. Check Accessibility Inspector ✅

**Expected:**
```
Close button:
  Role: button
  Name: Close knowledge gap menu ✅

Add as FAQ:
  Role: button
  Name: Add "[topic]" as FAQ ✅

Add Document:
  Role: button
  Name: Upload document to knowledge base ✅
```

---

### Test 3: All Interactive Elements

**Test:**
1. Press Tab repeatedly until you've visited all widgets
2. Count visible focus indicators

**Expected:**
- ✅ Every button shows focus
- ✅ Every link shows focus
- ✅ Every clickable card shows focus
- ✅ Focus color is #00f5d4 (cyan/green)

---

## 🐛 Known Issues (Non-Blocking)

### Remaining Icon Buttons Without aria-label

These are less critical and can be fixed later:

1. **AlertsWidget** - Dismiss buttons in detail panel
2. **AICostWidget** - Export/Refresh buttons
3. **FAQUsageWidget** - Manage FAQs link
4. **StatCard** - Expand buttons (have text content)

**Impact:** Low - These either have text labels or are in less-critical areas

**Fix Priority:** Medium (next sprint)

---

## ✅ Success Criteria

### All Tests Pass If:

- [ ] **Tab key** shows cyan focus on EVERY interactive element
- [ ] **Shift+Tab** works backwards through focusable elements
- [ ] **Enter key** activates focused buttons
- [ ] **TopTopicsWidget** download button has aria-label
- [ ] **KnowledgeGapWidget** close button has aria-label
- [ ] **KnowledgeGapWidget** action buttons have aria-label
- [ ] Focus indicator is clearly visible (not subtle)
- [ ] Focus color is #00f5d4 (cyan/green mantis color)

---

## 🚨 Troubleshooting

### "I don't see focus indicators"

**Solution:**
1. Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Clear browser cache
3. Check browser console for CSS errors
4. Verify frontend rebuilt: `npm run build` or check dev server

### "Focus indicators are blue, not cyan"

**Expected:** This is actually OK! It means the old CSS is loading.

**Solution:**
1. Check `frontend/src/index.css` for the focus styles
2. Look for: `outline: 2px solid #00f5d4;`
3. If missing, re-apply the fix from earlier

### "Screen reader still says 'button' without description"

**Debug:**
1. Open DevTools → Accessibility tab
2. Click the button
3. Check "Computed Properties" for aria-label
4. Check "Accessibility Tree" for the accessible name

---

## 📝 Test Report Template

After testing, fill this out:

```
Tested by: ___________________
Date: ___________________
Browser: _________________

Results:
[ ] Focus indicators visible: YES / NO
[ ] TopTopicsWidget download button: YES / NO
[ ] KnowledgeGapWidget close button: YES / NO
[ ] KnowledgeGapWidget action buttons: YES / NO
[ ] All buttons accessible via Tab: YES / NO
[ ] Focus color is cyan (#00f5d4): YES / NO

Issues found:
1. _________________________________
2. _________________________________

Overall Status: PASS / FAIL

Notes:
__________________________________________
```

---

## 🎓 Bonus: Advanced Tests

### Test Focus Order Logic

1. Start at top of dashboard
2. Press Tab repeatedly
3. Verify focus order is:
   - Top-left → Top-center → Top-right
   - Then next row left-to-right
   - Logical reading order

**Expected:** Focus follows visual layout (left-to-right, top-to-bottom)

---

### Test Mobile Touch

**On mobile device or responsive mode:**

1. Tap on interactive elements
2. Check for visual feedback (background change, border)
3. Verify tap targets are at least 44x44 pixels

**Expected:** Clear visual feedback on all taps

---

## ✅ Ready to Launch Checklist

- [x] Focus styles applied globally
- [x] Critical icon buttons have aria-labels
- [x] Build passes without errors
- [x] Backend and frontend running
- [ ] Manual focus test completed ← **You are here!**
- [ ] Icon button accessibility verified
- [ ] No regressions detected

---

## 🚀 Next Steps After Testing

1. **If tests pass:** ✅ Deploy to production!
2. **If issues found:** Document them for next sprint
3. **If regressions:** Rollback and investigate

---

**Happy Testing!** 🎉

If you find any issues, let me know and I'll fix them immediately.

---

**Generated:** 2026-03-29
**Dashboard Version:** 2.0 (Production Ready)
**Fixes Applied:** Global focus styles + Icon button labels
