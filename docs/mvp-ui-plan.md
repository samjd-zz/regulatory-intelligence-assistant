# MVP UI Implementation Plan
**Regulatory Intelligence Assistant - 2-Week MVP**

**Version:** 1.0  
**Date:** November 24, 2025  
**Current Status:** ~40% Complete  
**Target:** Production-Ready MVP in 1-2 Weeks

---

## Executive Summary

This plan focuses **exclusively on MVP requirements** from docs/design.md. No extra features, no polish - just core functionality needed for the G7 GovAI Challenge demo.

**MVP Scope (4 Pages Only):**
1. ✅ **Dashboard** - Quick stats and navigation (mostly done)
2. ⚠️ **Search** - Hybrid search with basic filters (needs work)
3. ✅ **Chat/Q&A** - Ask questions, get answers with citations (mostly done)
4. ⚠️ **Compliance** - Check form compliance (needs enhancement)

**What We're NOT Building (Future Phases):**
- ❌ Workflows page
- ❌ RegulationDetail page  
- ❌ Updates/Monitoring page
- ❌ Expert Validation interface
- ❌ Settings page
- ❌ Advanced dashboard features
- ❌ Knowledge graph visualization
- ❌ Mobile optimization (desktop-first)

---

## Current State Analysis

### What's Working ✅
- React 19 + TypeScript + Vite setup
- Zustand state management (4 stores)
- API service layer with axios
- 3 shared components (ConfidenceBadge, CitationTag, LoadingSpinner)
- Basic routing (4 routes)
- Basic styling with Tailwind

### What's Missing ❌
- No navigation layout (header/sidebar)
- No filter panel in Search
- No real-time validation in Compliance
- Limited accessibility features
- No error boundaries
- Basic styling only

---

## Week 1: Core Functionality (5 Days)

### Day 1: Setup & Navigation (Monday) ✅ COMPLETE
**Goal:** Get basic navigation working

**Tasks:**
1. ✅ Create simple Header component
   - Logo/title
   - Basic nav links (Dashboard, Search, Chat, Compliance)
   - No user menu, no notifications (MVP doesn't need it)

2. ✅ Create minimal Layout wrapper
   - Header at top
   - Content area
   - No sidebar, no footer (keep it simple)

3. ✅ Update App.tsx
   - Wrap routes in Layout
   - Keep existing routes

**Acceptance:**
- [x] Can navigate between all 4 pages
- [x] Header visible on all pages
- [x] Layout looks clean

**Files Created/Edited:**
- ✅ `frontend/src/components/layout/Header.tsx` (created)
- ✅ `frontend/src/components/layout/MainLayout.tsx` (created)
- ✅ `frontend/src/App.tsx` (edited)

---

### Day 2: Search Filters (Tuesday) ✅ COMPLETE
**Goal:** Add basic filtering to Search page

**Tasks:**
1. ✅ Create FilterPanel component
   - Jurisdiction checkboxes (Federal, Provincial, Municipal)
   - Document type checkboxes (Act, Regulation, Policy)
   - "Clear Filters" button
   - Simple, no fancy UI

2. ✅ Update Search page layout
   - Filters on left (sidebar)
   - Results on right
   - Basic grid layout

3. ✅ Connect filters to searchStore
   - Update search when filters change
   - Clear functionality

**Acceptance:**
- [x] Filters display in Search page
- [x] Checking filters updates results
- [x] Clear button works
- [x] Basic desktop layout (3/9 columns)

**Files Created/Edited:**
- ✅ `frontend/src/components/search/FilterPanel.tsx` (created)
- ✅ `frontend/src/pages/Search.tsx` (edited)

---

### Day 3: Search Results Enhancement (Wednesday) ✅ COMPLETE
**Goal:** Better result display

**Tasks:**
1. ✅ Enhance ResultCard component
   - Add hover effect
   - Display all metadata (jurisdiction, date, document type)
   - Add "View Details" button (even if it doesn't work yet)
   - Show confidence badge

2. ✅ Add result count display
   - "Found X results in Y seconds"
   - Display at top of results

3. ✅ Add loading skeleton
   - Show while searching
   - Better UX than spinner

**Acceptance:**
- [x] Results look professional
- [x] All metadata displays
- [x] Hover effects work
- [x] Loading states clear
- [x] Confidence badges show

**Files Created/Edited:**
- ✅ `frontend/src/components/shared/SearchSkeleton.tsx` (created)
- ✅ `frontend/src/pages/Search.tsx` (edited)

---

### Day 4: Compliance Real-time Validation (Thursday) ✅ COMPLETE
**Goal:** Add field validation to Compliance

**Tasks:**
1. ✅ Install React Hook Form + Zod
   ```bash
   npm install react-hook-form @hookform/resolvers zod
   ```

2. ✅ Create validation schema
   - Name: required, min 2 chars
   - SIN: required, valid format
   - Residency: required, enum
   - Hours: required, >= 420

3. ✅ Update Compliance page
   - Integrate React Hook Form
   - Show validation errors inline
   - Validate on blur
   - Red borders for errors

4. ✅ Enhance compliance report display
   - Better visual hierarchy
   - Color-coded sections (red/yellow/green)
   - Clear issue descriptions

**Acceptance:**
- [x] Fields validate on blur
- [x] Error messages display
- [x] Visual feedback (red borders)
- [x] Compliance report looks professional

**Files Edited:**
- ✅ `frontend/src/pages/Compliance.tsx` (edited)

---

### Day 5: Polish & Error Handling (Friday) ✅ COMPLETE
**Goal:** Make it production-ready

**Tasks:**
1. ✅ Add Error Boundary
   - Wrap app in error boundary
   - Show friendly error message
   - Prevent crashes

2. ✅ Add loading states everywhere
   - Search page: skeleton ✅
   - Chat page: has LoadingSpinner ✅
   - Compliance: spinner on submit ✅
   - Dashboard: has existing loading states ✅

3. ⚠️ Update Dashboard
   - Existing implementation looks functional
   - Stats display working
   - Quick actions present

4. ✅ Basic responsive setup
   - Grid layouts implemented
   - Desktop-first (1024px+)

**Acceptance:**
- [x] No uncaught errors (Error Boundary added)
- [x] All loading states work
- [x] Dashboard functional
- [x] Pages work on 1024px+ screens

**Files Created/Edited:**
- ✅ `frontend/src/components/ErrorBoundary.tsx` (created)
- ✅ `frontend/src/main.tsx` (edited - wrapped App in ErrorBoundary)

---

## Week 2: Testing & Deployment (3 Days)

### Day 6: Integration Testing (Monday)
**Goal:** Test all features work together

**Tasks:**
1. Manual testing checklist
   - [ ] Dashboard loads
   - [ ] Search works with filters
   - [ ] Chat receives responses
   - [ ] Compliance validates correctly
   - [ ] Navigation works
   - [ ] No console errors

2. Fix any bugs found
   - Priority: blocking bugs only
   - Nice-to-haves can wait

3. Test with real backend
   - Ensure API calls work
   - Handle errors gracefully
   - Test with sample data

**Acceptance:**
- [ ] All 4 pages functional
- [ ] No critical bugs
- [ ] Works with backend API

---

### Day 7: Accessibility & Polish (Tuesday)
**Goal:** Basic accessibility compliance

**Tasks:**
1. Add ARIA labels
   - Form fields
   - Buttons
   - Interactive elements

2. Keyboard navigation
   - Tab through forms
   - Enter to submit
   - Escape to close

3. Color contrast check
   - Ensure text readable
   - Fix any contrast issues

4. Final polish
   - Fix spacing issues
   - Consistent styling
   - Remove any TODOs

**Acceptance:**
- [ ] Basic keyboard navigation works
- [ ] ARIA labels present
- [ ] No major accessibility violations
- [ ] UI looks polished

---

### Day 8: Documentation & Handoff (Wednesday)
**Goal:** Document what was built

**Tasks:**
1. Update README.md
   - How to run locally
   - Environment variables needed
   - Basic usage instructions

2. Create quick user guide
   - How to search
   - How to ask questions
   - How to check compliance

3. Document known limitations
   - What's not implemented
   - Known bugs (if any)
   - Future improvements

4. Final testing
   - Smoke test all features
   - Prepare for demo

**Acceptance:**
- [ ] README updated
- [ ] User guide created
- [ ] Ready for demo

---

## Implementation Checklist

### Week 1 (Must-Haves)
- [ ] **Day 1:** Navigation layout (Header + MainLayout)
- [ ] **Day 2:** Search FilterPanel component
- [ ] **Day 3:** Enhanced search results display
- [ ] **Day 4:** Compliance real-time validation
- [ ] **Day 5:** Error boundaries + loading states

### Week 2 (Finalization)
- [ ] **Day 6:** Integration testing + bug fixes
- [ ] **Day 7:** Basic accessibility + polish
- [ ] **Day 8:** Documentation + demo prep

---

## Technical Decisions (MVP)

### What to Install
**Required:**
```bash
# React Hook Form + Zod (for validation)
npm install react-hook-form @hookform/resolvers zod

# Date utilities (if needed)
npm install date-fns
```

**NOT Installing (out of MVP scope):**
- ❌ shadcn/ui (too much setup time)
- ❌ TanStack Query (current axios setup works)
- ❌ Recharts (no advanced dashboard)
- ❌ React Flow (no graph visualization)

### What to Skip
- No Settings page
- No Workflows page
- No RegulationDetail page
- No mobile optimization
- No advanced dashboard charts
- No knowledge graph visualization
- No notification center
- No user profile menu
- No dark mode

### Keep It Simple
- Use Tailwind directly (no component library)
- Stick with current state management (Zustand)
- Keep current API layer (axios)
- Desktop-only (1024px+ screens)
- Basic styling (clean, not fancy)

---

## File Structure (MVP)

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── Header.tsx          [NEW - Day 1]
│   │   └── MainLayout.tsx      [NEW - Day 1]
│   ├── search/
│   │   └── FilterPanel.tsx     [NEW - Day 2]
│   └── shared/
│       ├── CitationTag.tsx     [EXISTS ✓]
│       ├── ConfidenceBadge.tsx [EXISTS ✓]
│       ├── LoadingSpinner.tsx  [EXISTS ✓]
│       └── ErrorBoundary.tsx   [NEW - Day 5]
├── pages/
│   ├── Dashboard.tsx           [EDIT - Day 5]
│   ├── Search.tsx              [EDIT - Days 2-3]
│   ├── Chat.tsx                [EXISTS ✓]
│   └── Compliance.tsx          [EDIT - Day 4]
├── store/                      [EXISTS ✓]
├── services/                   [EXISTS ✓]
├── types/                      [EXISTS ✓]
└── App.tsx                     [EDIT - Day 1]
```

---

## Success Criteria

### Functional Requirements
- [ ] All 4 pages render without errors
- [ ] Search returns results with filters
- [ ] Chat provides answers with citations
- [ ] Compliance validates and reports
- [ ] Navigation works between pages

### Quality Requirements
- [ ] No console errors
- [ ] Basic keyboard navigation works
- [ ] Loading states for all async operations
- [ ] Error messages user-friendly
- [ ] Responsive on desktop (1024px+)

### Performance Requirements
- [ ] Pages load in <2 seconds
- [ ] Search results in <3 seconds
- [ ] Chat response in <5 seconds
- [ ] No janky animations/transitions

### Demo Requirements
- [ ] Can demonstrate full search workflow
- [ ] Can demonstrate Q&A workflow
- [ ] Can demonstrate compliance check
- [ ] UI looks professional
- [ ] No embarrassing bugs

---

## Risk Mitigation

### Biggest Risks
1. **Time Pressure:** Only 8 days
   - **Mitigation:** Cut features ruthlessly, focus on core
   - **Fallback:** Skip Day 7 polish if needed

2. **Backend API Issues:** If backend doesn't work
   - **Mitigation:** Mock data for demo
   - **Fallback:** Use hardcoded responses

3. **Validation Complexity:** React Hook Form integration
   - **Mitigation:** Keep validation simple
   - **Fallback:** Remove real-time validation, just validate on submit

4. **Styling Time Sink:** Making it look good
   - **Mitigation:** Use Tailwind defaults, don't customize
   - **Fallback:** Basic clean styling is enough

### Emergency Scope Reduction
If running out of time, cut in this order:
1. Day 7 polish (defer to post-MVP)
2. Real-time validation (just validate on submit)
3. Filter panel enhancements (just checkboxes)
4. Dashboard enhancements (keep it basic)

---

## Daily Standup Template

**What I did yesterday:**
- Completed [X tasks]
- Made progress on [Y]

**What I'm doing today:**
- [Day N task from plan]

**Blockers:**
- [Any issues preventing progress]

**On Track?**
- ✅ Yes / ⚠️ At Risk / ❌ Behind

---

## Definition of Done

A task is "done" when:
- [ ] Code written and tested locally
- [ ] No console errors
- [ ] Works with backend API (or has mock data)
- [ ] Basic styling applied
- [ ] Committed to git
- [ ] Deployed and verified

---

## Post-MVP Improvements (Future)

**After MVP demo, prioritize:**
1. Mobile responsive design
2. Better error handling
3. More robust validation
4. Pagination for search results
5. Better loading states
6. Accessibility audit
7. Performance optimization
8. Advanced features (workflows, etc.)

**But for now: Ship the MVP! 🚀**

---

## Quick Reference

### Key Commands
```bash
# Install deps
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Run tests (if you have time)
npm run test
```

### Important URLs
- Dev: http://localhost:5173
- Backend API: http://localhost:8000
- Docs: /docs/design.md

### Getting Unstuck
1. Check design.md for requirements
2. Look at existing components for patterns
3. Keep it simple - MVP doesn't need to be perfect
4. Focus on functionality over beauty

---

**Remember:** This is an MVP for a demo, not a production app. Good enough is good enough. Ship it! 🎯

---

**Document Control:**
- Version: 1.0 MVP
- Date: November 24, 2025
- Status: Ready to Execute
- Timeline: 8 Days (1-2 weeks)
