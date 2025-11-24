# Frontend Testing Guide

This guide provides step-by-step instructions for testing the Regulatory Intelligence Assistant frontend.

## 🧪 Manual Testing Checklist

### Prerequisites
- Backend API running on `http://localhost:8000`
- Frontend dev server running on `http://localhost:3000`
- Browser with developer tools open

### 1. Dashboard Page (`/`)

**Test Case 1.1: Initial Load**
- [ ] Dashboard loads without errors
- [ ] Title "Regulatory Intelligence Assistant" displays
- [ ] Subtitle text is readable
- [ ] Three action cards display: Search, Ask Questions, Check Compliance
- [ ] Icons render correctly with proper colors
- [ ] Statistics section shows three metrics
- [ ] All text is properly formatted

**Test Case 1.2: Navigation**
- [ ] Click "Search Regulations" card → navigates to `/search`
- [ ] Click "Ask Questions" card → navigates to `/chat`
- [ ] Click "Check Compliance" card → navigates to `/compliance`
- [ ] Browser back button returns to dashboard

**Test Case 1.3: Responsive Design**
- [ ] Mobile view (< 640px): Cards stack vertically
- [ ] Tablet view (640-1024px): Grid layout adjusts
- [ ] Desktop view (> 1024px): Full grid layout

### 2. Search Page (`/search`)

**Test Case 2.1: Search Interface**
- [ ] Search input field is visible and functional
- [ ] Placeholder text is helpful
- [ ] Search button is accessible
- [ ] Advanced filters section can be expanded/collapsed
- [ ] Back to dashboard link works

**Test Case 2.2: Search Functionality**
- [ ] Enter query: "employment insurance eligibility"
- [ ] Click Search or press Enter
- [ ] Loading spinner appears
- [ ] Results display with:
  - [ ] Document titles as links
  - [ ] Confidence badges (High/Medium/Low)
  - [ ] Citations (section/clause references)
  - [ ] Excerpt/summary text
  - [ ] Proper formatting and spacing

**Test Case 2.3: Filters**
- [ ] Jurisdiction dropdown shows options
- [ ] Program type dropdown shows options
- [ ] Date range inputs accept dates
- [ ] Applying filters updates search results
- [ ] Clear filters button resets all filters

**Test Case 2.4: Search History**
- [ ] Previous searches appear in history
- [ ] Click history item → executes that search
- [ ] Clear history button works

**Test Case 2.5: Error Handling**
- [ ] Network error → error message displays
- [ ] Empty search → validation message
- [ ] No results → "No results found" message
- [ ] Timeout → appropriate error message

### 3. Chat Page (`/chat`)

**Test Case 3.1: Chat Interface**
- [ ] Chat input field is visible
- [ ] Send button is accessible
- [ ] Chat history area displays
- [ ] Welcome message or instructions show
- [ ] Scroll behavior works correctly

**Test Case 3.2: Asking Questions**
- [ ] Enter question: "What are the requirements for maternity leave?"
- [ ] Click Send or press Enter
- [ ] User message displays on right side
- [ ] Loading indicator shows while waiting
- [ ] AI response displays on left side with:
  - [ ] Answer text properly formatted
  - [ ] Confidence badge
  - [ ] Citations/sources listed
  - [ ] Timestamp

**Test Case 3.3: Conversation Flow**
- [ ] Follow-up questions maintain context
- [ ] Previous messages remain visible
- [ ] Auto-scroll to latest message
- [ ] Copy response text works

**Test Case 3.4: Chat Features**
- [ ] Clear chat button works
- [ ] Chat history persists on page reload
- [ ] Citations are clickable/copyable
- [ ] Long responses are formatted properly

### 4. Compliance Page (`/compliance`)

**Test Case 4.1: Compliance Form**
- [ ] Form displays with clear fields
- [ ] All input fields are accessible
- [ ] Field labels are descriptive
- [ ] Required field indicators display
- [ ] Check Compliance button is visible

**Test Case 4.2: Form Validation**
- [ ] Submit empty form → validation errors show
- [ ] Invalid email → shows error
- [ ] Invalid date format → shows error
- [ ] Required fields → proper error messages
- [ ] Error messages are clear and helpful

**Test Case 4.3: Compliance Checking**
- [ ] Fill form with test data
- [ ] Click "Check Compliance"
- [ ] Loading state displays
- [ ] Results display with:
  - [ ] Overall status (Compliant/Non-Compliant/Warning)
  - [ ] Individual field results
  - [ ] Pass/fail indicators
  - [ ] Explanations for each field
  - [ ] Relevant citations

**Test Case 4.4: Results Display**
- [ ] Visual indicators match status
- [ ] Color coding is clear (green/yellow/red)
- [ ] All required fields checked
- [ ] Download report button works (if implemented)
- [ ] Clear form button resets everything

### 5. Cross-Page Features

**Test Case 5.1: Navigation**
- [ ] Browser back/forward buttons work
- [ ] URL updates correctly
- [ ] Deep links work (direct URL access)
- [ ] 404 redirects to dashboard

**Test Case 5.2: API Integration**
- [ ] Backend connection works
- [ ] API errors display properly
- [ ] Loading states show consistently
- [ ] Timeout handling works
- [ ] Retry logic functions

**Test Case 5.3: Performance**
- [ ] Initial page load < 3 seconds
- [ ] Search results appear < 3 seconds
- [ ] Chat responses arrive promptly
- [ ] Smooth scrolling and animations
- [ ] No memory leaks on long sessions

### 6. Accessibility Testing

**Test Case 6.1: Keyboard Navigation**
- [ ] Tab key navigates through elements
- [ ] Enter key activates buttons
- [ ] Escape key closes modals/dropdowns
- [ ] Focus indicators are visible
- [ ] Skip to content link works

**Test Case 6.2: Screen Reader**
- [ ] All images have alt text
- [ ] ARIA labels are present
- [ ] Form fields have proper labels
- [ ] Error messages are announced
- [ ] Page titles are descriptive

**Test Case 6.3: Color Contrast**
- [ ] Text meets WCAG AA standards
- [ ] Confidence badges are distinguishable
- [ ] Interactive elements are clear
- [ ] Focus states are visible

### 7. Browser Compatibility

Test in the following browsers:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### 8. Mobile Testing

**Test Case 8.1: Responsive Layout**
- [ ] All pages adapt to mobile screens
- [ ] Text is readable without zooming
- [ ] Buttons are tap-friendly (44x44px min)
- [ ] No horizontal scrolling
- [ ] Images scale appropriately

**Test Case 8.2: Touch Interactions**
- [ ] Tap targets are adequate
- [ ] Swipe gestures work if implemented
- [ ] Form inputs work with mobile keyboards
- [ ] Dropdowns function on touch devices

## 🤖 Automated Testing (Future)

### Unit Tests (Jest + React Testing Library)
```bash
npm run test
```

- Component rendering tests
- Store logic tests
- Utility function tests
- Form validation tests

### Integration Tests
- API service integration
- Store-component interaction
- Multi-page workflows

### End-to-End Tests (Playwright/Cypress)
- Complete user journeys
- Cross-browser testing
- Visual regression testing

## 📊 Performance Testing

### Lighthouse Audit
Run Chrome DevTools Lighthouse:
- Performance: Target > 90
- Accessibility: Target 100
- Best Practices: Target > 90
- SEO: Target > 90

### Bundle Size
```bash
npm run build
```
Check `dist/` folder size (should be < 500KB gzipped)

## 🐛 Known Issues

Document any known issues here during testing:

1. Issue description
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Workaround (if any)

## ✅ Test Results

| Date | Tester | Browser | Pass/Fail | Notes |
|------|--------|---------|-----------|-------|
|      |        |         |           |       |

## 📝 Test Report Template

```
Date: [Date]
Tester: [Name]
Environment: [Dev/Staging/Production]
Browser: [Browser + Version]

Test Results:
- Dashboard: ✅/❌
- Search: ✅/❌
- Chat: ✅/❌
- Compliance: ✅/❌
- Accessibility: ✅/❌

Issues Found: [Count]
Critical: [Count]
Major: [Count]
Minor: [Count]

Notes:
[Additional observations]
