# UI Implementation Plan
**Regulatory Intelligence Assistant - Frontend Completion Roadmap**

**Version:** 1.0  
**Date:** November 24, 2025  
**Current Status:** 40% Complete  
**Estimated Total Effort:** 8-10 weeks (2 developers)

---

## Executive Summary

This document provides a detailed, step-by-step plan to complete the frontend UI implementation based on the gap analysis comparing the actual implementation against the UI Design Document (docs/ui-design.md).

**Current State:**
- ✅ 4 of 9 pages implemented
- ✅ 3 of 10 custom components built
- ✅ Core state management complete
- ✅ API integration ~70% complete

**Goal State:**
- ✅ All 9 pages fully functional
- ✅ All 10 custom components built
- ✅ Complete navigation system
- ✅ Full responsive design
- ✅ WCAG 2.1 AA compliance

---

## Implementation Phases Overview

| Phase | Focus | Duration | Priority |
|-------|-------|----------|----------|
| **Phase 0** | Setup & Infrastructure | 1 week | Critical |
| **Phase 1** | Core Search Enhancement | 2 weeks | High |
| **Phase 2** | Navigation & Layout | 1 week | High |
| **Phase 3** | Compliance Enhancement | 1 week | High |
| **Phase 4** | Chat Enhancement | 1 week | Medium |
| **Phase 5** | New Pages - Part 1 | 2 weeks | Medium |
| **Phase 6** | New Pages - Part 2 | 1.5 weeks | Medium |
| **Phase 7** | Polish & Accessibility | 1.5 weeks | High |
| **Total** | | **10 weeks** | |

---

## Phase 0: Setup & Infrastructure (Week 1)

### Goals
- Install missing dependencies
- Configure development environment
- Set up component library
- Establish coding standards

### Tasks

#### 0.1 Install Missing Dependencies (Day 1)

```bash
cd frontend

# Install shadcn/ui components
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input badge dialog tabs
npx shadcn-ui@latest add accordion tooltip separator skeleton
npx shadcn-ui@latest add alert scroll-area select checkbox
npx shadcn-ui@latest add radio-group label form table

# Install form handling
npm install react-hook-form @hookform/resolvers zod

# Install TanStack Query
npm install @tanstack/react-query @tanstack/react-query-devtools

# Install icons
npm install lucide-react

# Install date handling
npm install date-fns

# Install graph visualization
npm install @xyflow/react d3

# Install chart library
npm install recharts
```

**Acceptance Criteria:**
- [ ] All dependencies installed without errors
- [ ] shadcn/ui components available in components/ui/
- [ ] Package.json updated with all new dependencies

---

#### 0.2 Update Tailwind Configuration (Day 1)

**File:** `frontend/tailwind.config.js`

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#2563eb',
          600: '#1d4ed8',
          700: '#1e40af',
          800: '#1e3a8a',
          900: '#1e293b',
        },
        confidence: {
          high: '#16a34a',
          medium: '#eab308',
          low: '#dc2626',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Courier New', 'monospace'],
      },
      fontSize: {
        'citation': ['0.875rem', { lineHeight: '1.25rem', letterSpacing: '-0.01em' }],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

**Acceptance Criteria:**
- [ ] Tailwind config matches design document
- [ ] Custom colors available (primary, confidence)
- [ ] Custom fonts configured

---

#### 0.3 Set Up TanStack Query (Day 1)

**File:** `frontend/src/main.tsx`

Update to include QueryClientProvider:

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// Wrap App with QueryClientProvider
<QueryClientProvider client={queryClient}>
  <App />
  <ReactQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

**Acceptance Criteria:**
- [ ] QueryClient configured and wrapping App
- [ ] DevTools available in development
- [ ] Default options set per design spec

---

#### 0.4 Create Custom Hooks Directory Structure (Day 2)

```bash
# Create hooks directory
mkdir -p frontend/src/hooks

# Create hook files
touch frontend/src/hooks/useRegulation.ts
touch frontend/src/hooks/useSearch.ts
touch frontend/src/hooks/useCompliance.ts
touch frontend/src/hooks/useWorkflow.ts
touch frontend/src/hooks/useDebounce.ts
touch frontend/src/hooks/useLocalStorage.ts
```

**Acceptance Criteria:**
- [ ] Hooks directory created
- [ ] Hook files created and empty (ready for implementation)

---

#### 0.5 Update Project Structure (Day 2)

Create missing component directories:

```bash
cd frontend/src/components

# Create missing directories
mkdir -p graph
mkdir -p workflows
mkdir -p layout
mkdir -p regulation

# Create placeholder files
touch layout/Header.tsx
touch layout/Sidebar.tsx
touch layout/Footer.tsx
touch layout/MainLayout.tsx
touch search/FilterPanel.tsx
touch search/ResultCard.tsx
touch chat/CitationSidebar.tsx
touch compliance/ComplianceReport.tsx
touch regulation/RegulationViewer.tsx
touch workflows/WorkflowStepper.tsx
touch graph/KnowledgeGraph.tsx
```

**Acceptance Criteria:**
- [ ] All component directories exist
- [ ] Placeholder files created
- [ ] Structure matches design document

---

## Phase 1: Core Search Enhancement (Weeks 2-3)

### Goals
- Complete search functionality
- Add filter panel
- Enhance result display
- Add autocomplete

### Tasks

#### 1.1 Create FilterPanel Component (Week 2, Days 1-2)

**File:** `frontend/src/components/search/FilterPanel.tsx`

**Requirements:**
- Collapsible filter sections
- Jurisdiction filter (checkboxes: Federal, Provincial, Municipal)
- Date range picker (effective date)
- Document type filter (Act, Regulation, Policy)
- Program filter (EI, Immigration, Healthcare, etc.)
- "Clear All" button
- Result count display

**Implementation Steps:**
1. Create FilterPanel component structure
2. Add filter sections with shadcn Accordion
3. Implement checkbox groups with shadcn Checkbox
4. Add date range picker
5. Connect to searchStore
6. Add clear functionality
7. Style with Tailwind

**Acceptance Criteria:**
- [ ] FilterPanel renders in Search page
- [ ] All filter types functional
- [ ] Filters update search results
- [ ] Clear all works correctly
- [ ] Accessible with keyboard navigation

---

#### 1.2 Enhance SearchBar with Autocomplete (Week 2, Day 3)

**File:** `frontend/src/components/search/SearchBar.tsx`

**Requirements:**
- Autocomplete dropdown as user types
- Recent searches display
- Highlight matching terms
- Keyboard navigation (Arrow keys, Enter, Escape)
- Loading spinner during suggestions fetch

**Implementation Steps:**
1. Add useDebounce hook for autocomplete
2. Fetch suggestions from API
3. Render dropdown with suggestions
4. Add keyboard navigation
5. Store recent searches in userStore
6. Style dropdown with shadcn Popover

**API Integration:**
```typescript
// Use existing getSuggestions from api.ts
const suggestions = await getSuggestions(query);
```

**Acceptance Criteria:**
- [ ] Autocomplete appears after 2 characters
- [ ] Suggestions load within 200ms
- [ ] Recent searches displayed
- [ ] Keyboard navigation works
- [ ] Accessible with ARIA combobox

---

#### 1.3 Enhance ResultCard Component (Week 2, Day 4)

**File:** `frontend/src/components/search/ResultCard.tsx`

**Requirements:**
- Hover effects with shadow
- Highlight search terms in snippet
- Better metadata display
- "View Full Text" button
- Save to favorites button

**Implementation Steps:**
1. Update ResultCard styling with hover effects
2. Add text highlighting function for search terms
3. Expand metadata display (jurisdiction, date, type)
4. Add action buttons (View, Save)
5. Connect to regulation detail route
6. Add save functionality via userStore

**Acceptance Criteria:**
- [ ] Hover effect displays
- [ ] Search terms highlighted in snippet
- [ ] All metadata displayed
- [ ] Buttons functional
- [ ] Links to regulation detail page

---

#### 1.4 Update Search Page Layout (Week 2, Day 5)

**File:** `frontend/src/pages/Search.tsx`

**Requirements:**
- Add FilterPanel sidebar (3 columns)
- Results area (9 columns)
- Sort dropdown
- Result count and processing time
- Pagination

**Implementation Steps:**
1. Add grid layout (3/9 split)
2. Integrate FilterPanel component
3. Add sort dropdown (Relevance, Date, Title)
4. Display result count and time
5. Add pagination component
6. Update searchStore for pagination

**Acceptance Criteria:**
- [ ] Layout matches design (3/9 columns)
- [ ] FilterPanel visible on desktop
- [ ] Sort functionality works
- [ ] Result count displays
- [ ] Pagination works correctly

---

#### 1.5 Add Search Hooks (Week 3, Day 1)

**File:** `frontend/src/hooks/useSearch.ts`

**Requirements:**
- useSearch hook with TanStack Query
- useSearchSuggestions hook
- Caching and error handling

**Implementation:**
```typescript
import { useQuery } from '@tanstack/react-query'
import { searchRegulations } from '@/services/api'

export function useSearch(query: string, filters: FilterState) {
  return useQuery({
    queryKey: ['search', query, filters],
    queryFn: () => searchRegulations({ query, filters, limit: 20 }),
    enabled: query.length > 0,
    staleTime: 5 * 60 * 1000,
  })
}

export function useSearchSuggestions(query: string) {
  return useQuery({
    queryKey: ['suggestions', query],
    queryFn: () => getSuggestions(query),
    enabled: query.length > 2,
    staleTime: 2 * 60 * 1000,
  })
}
```

**Acceptance Criteria:**
- [ ] useSearch hook created
- [ ] useSearchSuggestions hook created
- [ ] Caching works correctly
- [ ] Error handling implemented

---

#### 1.6 Mobile Responsive Search (Week 3, Day 2)

**Requirements:**
- Filter panel in bottom sheet on mobile
- Full-width results on mobile
- Touch-friendly tap targets

**Implementation Steps:**
1. Add responsive breakpoints
2. Create bottom sheet for filters (mobile)
3. Update layout for mobile (single column)
4. Ensure touch targets ≥44px
5. Test on mobile viewport

**Acceptance Criteria:**
- [ ] Filters accessible on mobile
- [ ] Layout adapts to mobile
- [ ] Touch targets adequate
- [ ] Performance acceptable on mobile

---

## Phase 2: Navigation & Layout (Week 4)

### Goals
- Create main layout structure
- Add header with navigation
- Add sidebar navigation
- Implement routing

### Tasks

#### 2.1 Create MainLayout Component (Week 4, Days 1-2)

**File:** `frontend/src/components/layout/MainLayout.tsx`

**Requirements:**
- Header at top
- Sidebar on left (collapsible)
- Main content area
- Footer at bottom
- Responsive design

**Implementation:**
```typescript
interface MainLayoutProps {
  children: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  
  return (
    <div className="min-h-screen flex flex-col">
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      <div className="flex flex-1">
        <Sidebar open={sidebarOpen} />
        <main className="flex-1 p-6 bg-gray-50">
          {children}
        </main>
      </div>
      <Footer />
    </div>
  )
}
```

**Acceptance Criteria:**
- [ ] Layout component created
- [ ] Responsive grid works
- [ ] Sidebar collapsible
- [ ] All pages wrapped in layout

---

#### 2.2 Create Header Component (Week 4, Day 2)

**File:** `frontend/src/components/layout/Header.tsx`

**Requirements:**
- Logo/branding
- Global search bar
- User profile menu
- Notification center icon
- Mobile menu button

**Implementation Steps:**
1. Create header with logo
2. Add global search bar (reuse SearchBar)
3. Add user menu dropdown
4. Add notification bell icon
5. Add mobile hamburger menu
6. Style with Tailwind

**Acceptance Criteria:**
- [ ] Header displays across all pages
- [ ] Global search functional
- [ ] User menu dropdown works
- [ ] Mobile menu button visible on mobile

---

#### 2.3 Create Sidebar Navigation (Week 4, Day 3)

**File:** `frontend/src/components/layout/Sidebar.tsx`

**Requirements:**
- Navigation links to all pages
- Active route highlighting
- Icons for each section
- Collapsible on mobile

**Navigation Structure:**
```typescript
const navItems = [
  { path: '/', label: 'Dashboard', icon: Home },
  { path: '/search', label: 'Search', icon: Search },
  { path: '/chat', label: 'Q&A Chat', icon: MessageSquare },
  { path: '/compliance', label: 'Compliance', icon: CheckCircle },
  { path: '/workflows', label: 'Workflows', icon: GitBranch },
  { path: '/updates', label: 'Updates', icon: Bell },
  { path: '/expert', label: 'Expert Review', icon: Users },
  { path: '/settings', label: 'Settings', icon: Settings },
]
```

**Acceptance Criteria:**
- [ ] All navigation links present
- [ ] Active route highlighted
- [ ] Icons displayed
- [ ] Collapsible on mobile

---

#### 2.4 Create Footer Component (Week 4, Day 3)

**File:** `frontend/src/components/layout/Footer.tsx`

**Requirements:**
- Copyright notice
- Links (Privacy, Terms, Help)
- Version number
- Contact info

**Acceptance Criteria:**
- [ ] Footer displays on all pages
- [ ] Links functional
- [ ] Responsive design

---

#### 2.5 Update App.tsx with Layout and Routes (Week 4, Day 4)

**File:** `frontend/src/App.tsx`

**Requirements:**
- Wrap routes in MainLayout
- Add all 9 routes
- Add 404 page

**Implementation:**
```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { MainLayout } from './components/layout/MainLayout'

function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/search" element={<Search />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/compliance" element={<Compliance />} />
          <Route path="/workflows" element={<Workflows />} />
          <Route path="/regulation/:id" element={<RegulationDetail />} />
          <Route path="/updates" element={<Updates />} />
          <Route path="/expert" element={<ExpertValidation />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  )
}
```

**Acceptance Criteria:**
- [ ] All routes defined
- [ ] Layout wraps all pages
- [ ] Navigation between pages works
- [ ] 404 page created

---

#### 2.6 Mobile Navigation (Week 4, Day 5)

**Requirements:**
- Bottom navigation bar on mobile
- Drawer navigation for mobile
- Touch-friendly navigation

**Implementation Steps:**
1. Create mobile bottom nav component
2. Show/hide based on screen size
3. Add drawer for full menu
4. Test touch interactions

**Acceptance Criteria:**
- [ ] Bottom nav visible on mobile
- [ ] Drawer accessible
- [ ] Navigation smooth
- [ ] Works on all mobile sizes

---

## Phase 3: Compliance Enhancement (Week 5)

### Goals
- Add real-time field validation
- Enhance compliance report
- Add export functionality
- Improve form UX

### Tasks

#### 3.1 Implement Real-time Validation (Week 5, Days 1-2)

**File:** `frontend/src/pages/Compliance.tsx`

**Requirements:**
- Validate fields on blur
- Show validation feedback immediately
- Display validation badges per field
- Tooltip with requirement explanation

**Implementation Steps:**
1. Install React Hook Form and Zod
2. Create validation schema with Zod
3. Implement useForm hook
4. Add field validation on blur
5. Display inline validation messages
6. Add tooltips with requirements

**Validation Schema Example:**
```typescript
import { z } from 'zod'

const complianceSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  sin: z.string().regex(/^\d{3}-\d{3}-\d{3}$/, 'Invalid SIN format'),
  residency_status: z.enum(['citizen', 'permanent_resident', 'temporary_resident']),
  hours_worked: z.number().min(420, 'Must have at least 420 hours'),
})
```

**Acceptance Criteria:**
- [ ] React Hook Form integrated
- [ ] Zod validation schema created
- [ ] Real-time validation works
- [ ] Validation messages display correctly
- [ ] Tooltips show requirements

---

#### 3.2 Enhance ComplianceReport Component (Week 5, Day 3)

**File:** `frontend/src/components/compliance/ComplianceReport.tsx`

**Requirements:**
- Expandable/collapsible issue details
- Better visual hierarchy
- Export functionality (PDF, print)
- Email report option

**Implementation Steps:**
1. Create separate ComplianceReport component
2. Add Accordion for issue details
3. Implement export to PDF (use jsPDF or browser print)
4. Add print stylesheet
5. Add email functionality
6. Style with color-coded sections

**Acceptance Criteria:**
- [ ] Issues expandable/collapsible
- [ ] Export to PDF works
- [ ] Print functionality works
- [ ] Email option available
- [ ] Visual hierarchy clear

---

#### 3.3 Add Progress Indicator (Week 5, Day 4)

**Requirements:**
- Show form completion percentage
- Highlight required vs optional fields
- Update as user fills form

**Implementation:**
```typescript
const progress = useMemo(() => {
  const fields = ['name', 'sin', 'residency_status', 'hours_worked']
  const completed = fields.filter(f => formData[f]).length
  return (completed / fields.length) * 100
}, [formData])
```

**Acceptance Criteria:**
- [ ] Progress bar displays
- [ ] Updates in real-time
- [ ] Shows percentage
- [ ] Visually appealing

---

#### 3.4 Add Document Upload (Week 5, Day 5)

**Requirements:**
- File upload component
- Support for PDF, images
- Preview uploaded files
- Validation of file types

**Implementation Steps:**
1. Create file upload component
2. Add drag-and-drop support
3. Validate file types and sizes
4. Display file previews
5. Store files in form state

**Acceptance Criteria:**
- [ ] File upload works
- [ ] Drag-and-drop functional
- [ ] File validation works
- [ ] Previews display correctly

---

## Phase 4: Chat Enhancement (Week 6)

### Goals
- Add citation sidebar
- Improve message display
- Add related questions
- Enhance accessibility

### Tasks

#### 4.1 Create CitationSidebar Component (Week 6, Days 1-2)

**File:** `frontend/src/components/chat/CitationSidebar.tsx`

**Requirements:**
- List all citations from conversation
- Click to view full regulation
- Highlight active citation
- Copy citation button
- Sticky positioning

**Implementation:**
```typescript
interface CitationSidebarProps {
  citations: Citation[]
  activeCitationId?: string
  onCitationClick: (id: string) => void
}

export function CitationSidebar({ citations, activeCitationId, onCitationClick }: CitationSidebarProps) {
  return (
    <aside className="w-80 sticky top-4 h-fit">
      <Card>
        <CardHeader>
          <h3>Referenced Regulations</h3>
        </CardHeader>
        <CardContent>
          {citations.map(citation => (
            <CitationCard
              key={citation.id}
              citation={citation}
              active={citation.id === activeCitationId}
              onClick={() => onCitationClick(citation.id)}
            />
          ))}
        </CardContent>
      </Card>
    </aside>
  )
}
```

**Acceptance Criteria:**
- [ ] Sidebar displays all citations
- [ ] Click navigation works
- [ ] Active citation highlighted
- [ ] Copy functionality works
- [ ] Sticky positioning works

---

#### 4.2 Update Chat Page Layout (Week 6, Day 2)

**File:** `frontend/src/pages/Chat.tsx`

**Requirements:**
- Add CitationSidebar (4 columns)
- Adjust chat area (8 columns)
- Responsive design (hide sidebar on mobile)

**Acceptance Criteria:**
- [ ] Layout updated (8/4 split)
- [ ] Sidebar visible on desktop
- [ ] Hidden on mobile (accessible via button)
- [ ] Responsive design works

---

#### 4.3 Add Related Questions (Week 6, Day 3)

**Requirements:**
- Display related questions after AI response
- Clickable to ask question
- Generated by backend

**Implementation:**
```typescript
// In AssistantMessage component
{message.relatedQuestions && (
  <div className="mt-4 border-t pt-4">
    <p className="text-sm font-medium mb-2">💡 Related Questions:</p>
    <div className="space-y-2">
      {message.relatedQuestions.map(q => (
        <button
          key={q}
          onClick={() => sendMessage(q)}
          className="text-left text-sm text-blue-600 hover:underline block"
        >
          {q}
        </button>
      ))}
    </div>
  </div>
)}
```

**Acceptance Criteria:**
- [ ] Related questions display
- [ ] Clickable to ask
- [ ] Styled appropriately

---

#### 4.4 Add Message Actions (Week 6, Day 4)

**Requirements:**
- Copy message button
- Share message button
- Thumbs up/down feedback
- Regenerate response

**Implementation Steps:**
1. Add action buttons to message footer
2. Implement copy to clipboard
3. Add share functionality
4. Add feedback buttons
5. Add regenerate option

**Acceptance Criteria:**
- [ ] Copy works
- [ ] Share works
- [ ] Feedback buttons functional
- [ ] Regenerate works

---

#### 4.5 Improve Message Accessibility (Week 6, Day 5)

**Requirements:**
- ARIA labels for messages
- Keyboard navigation
- Screen reader support
- Focus management

**Implementation Steps:**
1. Add ARIA role="article" to messages
2. Add ARIA labels for citations
3. Implement keyboard shortcuts
4. Test with screen reader
5. Add skip links

**Acceptance Criteria:**
- [ ] ARIA labels correct
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] No accessibility violations

---

## Phase 5: New Pages - Part 1 (Weeks 7-8)

### Goals
- Create RegulationDetail page
- Create Workflows page
- Create Updates page

### Tasks

#### 5.1 Create RegulationDetail Page (Week 7, Days 1-3)

**File:** `frontend/src/pages/RegulationDetail.tsx`

**Requirements:**
- Regulation header with metadata
- Tabbed content (Summary, Full Text, Amendments, Related)
- Sidebar with related content
- Knowledge graph preview
- Action buttons (Save, Share, Export)

**Implementation Steps:**

**Day 1:**
1. Create page component structure
2. Add regulation header component
3. Fetch regulation data with useRegulation hook
4. Display basic metadata

**Day 2:**
3. Implement tabs with shadcn Tabs
4. Create Summary tab content
5. Create Full Text tab content
6. Create Amendments tab content
7. Create Related tab content

**Day 3:**
8. Add sidebar with related regulations
9. Add knowledge graph preview (static initially)
10. Add action buttons
11. Style page

**API Integration:**
```typescript
export function useRegulation(id: string) {
  return useQuery({
    queryKey: ['regulation', id],
    queryFn: () => api.getRegulation(id),
  })
}

export function useRelatedRegulations(id: string) {
  return useQuery({
    queryKey: ['related', id],
    queryFn: () => api.getRelatedRegulations(id),
  })
}
```

**Acceptance Criteria:**
- [ ] Page displays regulation details
- [ ] All tabs functional
- [ ] Sidebar shows related regulations
- [ ] Action buttons work
- [ ] Responsive design
- [ ] Accessible

---

#### 5.2 Create Workflows Page (Week 7, Days 4-5)

**File:** `frontend/src/pages/Workflows.tsx`

**Requirements:**
- List of available workflows
- Active workflow display
- Step-by-step progress
- Context-aware help

**Implementation Steps:**

**Day 4:**
1. Create Workflows page component
2. Add workflow list component
3. Fetch available workflows
4. Display workflow cards

**Day 5:**
5. Create WorkflowStepper component
6. Implement step progression
7. Add context help for each step
8. Add form fields per step
9. Connect to backend workflow API

**Workflow Structure:**
```typescript
interface Workflow {
  id: string
  title: string
  description: string
  steps: WorkflowStep[]
  estimatedTime: string
}

interface WorkflowStep {
  id: string
  title: string
  description: string
  fields: FormField[]
  helpText: string
  validations: ValidationRule[]
}
```

**Acceptance Criteria:**
- [ ] Workflow list displays
- [ ] Can start workflow
- [ ] Step progression works
- [ ] Help text displays
- [ ] Form validation works
- [ ] Can complete workflow

---

#### 5.3 Create Updates/Monitoring Page (Week 8, Days 1-3)

**File:** `frontend/src/pages/Updates.tsx`

**Requirements:**
- Timeline of regulatory changes
- Filter by jurisdiction, date, impact
- Subscription management
- Update statistics

**Implementation Steps:**

**Day 1:**
1. Create Updates page component
2. Add filter bar
3. Fetch regulatory updates
4. Display timeline view

**Day 2:**
5. Create update card component
6. Add impact level badges
7. Implement filtering
8. Add subscription sidebar

**Day 3:**
9. Create subscription management
10. Add statistics panel
11. Implement "Mark as read"
12. Style timeline

**API Integration:**
```typescript
export function useRegulatoryUpdates(filters: UpdateFilters) {
  return useQuery({
    queryKey: ['updates', filters],
    queryFn: () => api.getRegulatoryUpdates(filters),
  })
}
```

**Acceptance Criteria:**
- [ ] Timeline displays updates
- [ ] Filters work correctly
- [ ] Subscriptions manageable
- [ ] Statistics display
- [ ] Responsive design

---

## Phase 6: New Pages - Part 2 (Weeks 8-9)

### Goals
- Create Expert Validation page
- Create Settings page
- Create NotFound page

### Tasks

#### 6.1 Create Expert Validation Page (Week 8, Days 4-5 & Week 9, Day 1)

**File:** `frontend/src/pages/ExpertValidation.tsx`

**Requirements:**
- Review queue with priority
- Active review panel
- Approve/reject workflow
- Statistics dashboard

**Implementation Steps:**

**Day 4:**
1. Create page component
2. Add review queue sidebar
3. Fetch pending reviews
4. Display priority badges

**Day 5:**
5. Create review panel component
6. Display case details
7. Show AI recommendation
8. Add expert review form

**Day 1 (Week 9):**
9. Implement approval workflow
10. Add notes/comments field
11. Add statistics panel
12. Style page

**Acceptance Criteria:**
- [ ] Queue displays pending reviews
- [ ] Can view case details
- [ ] Can approve/reject recommendations
- [ ] Statistics display
- [ ] Notes can be added

---

#### 6.2 Create Settings Page (Week 9, Day 2)

**File:** `frontend/src/pages/Settings.tsx`

**Requirements:**
- Tabbed settings interface
- Notification preferences
- Display settings
- Default filters
- Account management

**Implementation:**
```typescript
export function Settings() {
  const { preferences, updatePreferences } = useUserStore()
  
  return (
    <div>
      <h1>Settings & Preferences</h1>
      <Tabs defaultValue="notifications">
        <TabsList>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="display">Display</TabsTrigger>
          <TabsTrigger value="filters">Default Filters</TabsTrigger>
          <TabsTrigger value="account">Account</TabsTrigger>
        </TabsList>
        
        <TabsContent value="notifications">
          <NotificationSettings />
        </TabsContent>
        
        <TabsContent value="display">
          <DisplaySettings />
        </TabsContent>
        
        {/* etc */}
      </Tabs>
    </div>
  )
}
```

**Acceptance Criteria:**
- [ ] All tabs functional
- [ ] Settings save correctly
- [ ] Changes persist
- [ ] Validation works
- [ ] Reset to defaults works

---

#### 6.3 Create NotFound Page (Week 9, Day 3)

**File:** `frontend/src/pages/NotFound.tsx`

**Requirements:**
- 404 error message
- Helpful suggestions
- Link back to home
- Search bar

**Implementation:**
```typescript
export function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h1 className="text-6xl font-bold text-gray-300">404</h1>
      <h2 className="text-2xl font-semibold mt-4">Page Not Found</h2>
      <p className="text-gray-600 mt-2 max-w-md">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <div className="mt-8 space-x-4">
        <Button asChild>
          <Link to="/">Go to Dashboard</Link>
        </Button>
        <Button variant="outline" asChild>
          <Link to="/search">Search Regulations</Link>
        </Button>
      </div>
    </div>
  )
}
```

**Acceptance Criteria:**
- [ ] 404 message displays
- [ ] Links work correctly
- [ ] Styled appropriately
- [ ] Accessible

---

#### 6.4 Enhance Dashboard Page (Week 9, Days 4-5)

**File:** `frontend/src/pages/Dashboard.tsx`

**Requirements:**
- Add search activity chart
- Recent queries list with links
- Regulatory updates widget
- Help & resources section
- Complex grid layout (8/4 split)

**Implementation Steps:**

**Day 4:**
1. Add Recharts library for activity chart
2. Create line chart for last 7 days
3. Fetch search activity data
4. Display recent queries with links

**Day 5:**
5. Add regulatory updates widget
6. Add help & resources section
7. Implement 8/4 grid layout
8. Style dashboard

**Acceptance Criteria:**
- [ ] Activity chart displays
- [ ] Recent queries listed
- [ ] Updates widget shows recent changes
- [ ] Help resources available
- [ ] Layout matches design

---

## Phase 7: Polish & Accessibility (Weeks 10-11)

### Goals
- Complete accessibility audit
- Implement responsive design fully
- Add loading states and error boundaries
- Optimize performance
- Conduct user testing

### Tasks

#### 7.1 Accessibility Audit (Week 10, Days 1-2)

**Requirements:**
- WCAG 2.1 AA compliance
- Keyboard navigation throughout
- Screen reader compatibility
- Color contrast validation

**Implementation Steps:**
1. Install and run axe DevTools
2. Test with NVDA/JAWS screen reader
3. Verify keyboard navigation on all pages
4. Check color contrast ratios
5. Fix identified issues
6. Add skip links
7. Ensure focus management

**Tools:**
- axe DevTools browser extension
- Lighthouse accessibility audit
- WAVE accessibility evaluation tool
- Screen reader testing (NVDA/JAWS/VoiceOver)

**Acceptance Criteria:**
- [ ] Zero critical accessibility violations
- [ ] All interactive elements keyboard accessible
- [ ] Screen reader announces content correctly
- [ ] Color contrast meets WCAG AA standards
- [ ] Focus indicators visible and clear

---

#### 7.2 Complete Responsive Design (Week 10, Days 3-4)

**Requirements:**
- Test all pages at all breakpoints
- Mobile-specific optimizations
- Tablet layout refinements
- Touch-friendly interactions

**Testing Matrix:**
- Mobile: 320px, 375px, 414px
- Tablet: 768px, 1024px
- Desktop: 1280px, 1440px, 1920px

**Implementation Steps:**
1. Test each page at all breakpoints
2. Fix layout issues
3. Optimize touch targets
4. Test on real devices
5. Add mobile-specific features
6. Optimize images for mobile

**Acceptance Criteria:**
- [ ] All pages work at all breakpoints
- [ ] Touch targets ≥44px on mobile
- [ ] No horizontal scrolling
- [ ] Images optimized
- [ ] Performance acceptable on mobile

---

#### 7.3 Add Loading States and Error Boundaries (Week 10, Day 5)

**Requirements:**
- Loading skeletons for all pages
- Error boundaries to catch crashes
- Fallback UI for errors
- Retry mechanisms

**Implementation:**

**Error Boundary:**
```typescript
// components/ErrorBoundary.tsx
import React from 'react'

interface Props {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-8 text-center">
          <h2>Something went wrong</h2>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
```

**Acceptance Criteria:**
- [ ] Error boundaries wrap major sections
- [ ] Loading skeletons on all pages
- [ ] Error states display helpful messages
- [ ] Retry functionality works
- [ ] No uncaught errors

---

#### 7.4 Performance Optimization (Week 11, Days 1-2)

**Requirements:**
- Optimize bundle size
- Lazy load routes and components
- Optimize images
- Implement code splitting
- Add service worker for caching

**Implementation Steps:**
1. Analyze bundle size with Vite build analyzer
2. Implement lazy loading for routes
3. Add React.lazy for heavy components
4. Optimize images (WebP, responsive images)
5. Enable code splitting
6. Add service worker
7. Implement caching strategies

**Performance Targets:**
- Initial load: <2 seconds (3G)
- Time to Interactive: <3 seconds
- First Contentful Paint: <1.5 seconds
- Lighthouse score: >90

**Acceptance Criteria:**
- [ ] Bundle size optimized
- [ ] Routes lazy loaded
- [ ] Images optimized
- [ ] Lighthouse score >90
- [ ] Performance targets met

---

#### 7.5 Cross-browser Testing (Week 11, Day 3)

**Requirements:**
- Test on Chrome, Firefox, Safari, Edge
- Fix browser-specific issues
- Add polyfills if needed

**Testing Checklist:**
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Chrome Mobile
- [ ] Safari iOS

**Acceptance Criteria:**
- [ ] All features work on all browsers
- [ ] Layout consistent across browsers
- [ ] No browser-specific errors
- [ ] Polyfills added where needed

---

#### 7.6 User Acceptance Testing (Week 11, Days 4-5)

**Requirements:**
- Conduct UAT with stakeholders
- Gather feedback
- Document issues
- Prioritize fixes

**UAT Process:**
1. Create test scenarios
2. Conduct UAT sessions
3. Collect feedback
4. Document issues in tracking system
5. Prioritize and fix critical issues
6. Re-test fixed issues

**Test Scenarios:**
- Search for regulations
- Ask questions in chat
- Check compliance
- Navigate workflows
- Review updates
- Expert validation workflow

**Acceptance Criteria:**
- [ ] UAT sessions completed
- [ ] Feedback collected and documented
- [ ] Critical issues fixed
- [ ] User satisfaction >80%

---

## Phase 8: Documentation & Handoff (Week 12)

### Goals
- Complete technical documentation
- Create user guides
- Document API integrations
- Prepare deployment guide

### Tasks

#### 8.1 Technical Documentation (Week 12, Days 1-2)

**Documents to Create:**

1. **Component Documentation**
   - Document all components with examples
   - Add JSDoc comments
   - Create Storybook stories (optional)

2. **State Management Guide**
   - Document Zustand stores
   - Explain data flow
   - Provide usage examples

3. **API Integration Guide**
   - Document all API endpoints
   - Show request/response examples
   - Explain error handling

4. **Development Setup Guide**
   - Installation instructions
   - Environment variables
   - Running locally

**Acceptance Criteria:**
- [ ] All components documented
- [ ] State management explained
- [ ] API integration documented
- [ ] Setup guide complete

---

#### 8.2 User Guides (Week 12, Day 3)

**Documents to Create:**

1. **User Manual**
   - How to search regulations
   - How to use Q&A chat
   - How to check compliance
   - How to use workflows

2. **Quick Start Guide**
   - Getting started
   - Common tasks
   - Tips and tricks

3. **FAQ Document**
   - Common questions
   - Troubleshooting
   - Contact information

**Acceptance Criteria:**
- [ ] User manual complete
- [ ] Quick start guide written
- [ ] FAQ documented
- [ ] Screenshots included

---

#### 8.3 Deployment Documentation (Week 12, Day 4)

**Documents to Create:**

1. **Deployment Guide**
   - Build process
   - Environment configuration
   - Deployment steps
   - Rollback procedures

2. **Production Checklist**
   - Pre-deployment checks
   - Post-deployment verification
   - Monitoring setup

**Acceptance Criteria:**
- [ ] Deployment guide complete
- [ ] Production checklist ready
- [ ] Rollback procedures documented

---

#### 8.4 Handoff & Training (Week 12, Day 5)

**Activities:**
1. Conduct handoff meeting
2. Walk through codebase
3. Demonstrate features
4. Answer questions
5. Transfer knowledge

**Acceptance Criteria:**
- [ ] Handoff meeting completed
- [ ] Team trained on codebase
- [ ] All questions answered
- [ ] Documentation transferred

---

## Implementation Priority Matrix

### Must Have (Phase 0-3)
**Timeline: 5 weeks**

| Feature | Priority | Effort | Impact |
|---------|----------|--------|--------|
| FilterPanel | P0 | Medium | Critical |
| Navigation & Layout | P0 | High | Critical |
| Real-time Validation | P0 | Medium | High |
| Autocomplete Search | P1 | Medium | High |
| Enhanced Results | P1 | Low | Medium |

### Should Have (Phase 4-6)
**Timeline: 5 weeks**

| Feature | Priority | Effort | Impact |
|---------|----------|--------|--------|
| Citation Sidebar | P1 | Medium | High |
| RegulationDetail Page | P0 | High | Critical |
| Workflows Page | P1 | High | High |
| Updates Page | P1 | Medium | High |
| Settings Page | P2 | Low | Medium |

### Nice to Have (Phase 7-8)
**Timeline: 2 weeks**

| Feature | Priority | Effort | Impact |
|---------|----------|--------|--------|
| Expert Validation | P2 | High | Medium |
| Knowledge Graph | P2 | High | Low |
| Advanced Dashboard | P2 | Medium | Low |

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API performance issues | Medium | High | Implement caching, optimize queries |
| Browser compatibility | Low | Medium | Test early, add polyfills |
| Accessibility violations | Medium | High | Continuous testing, expert review |
| Mobile performance | Medium | Medium | Optimize assets, lazy loading |
| Third-party dependencies | Low | Medium | Lock versions, test updates |

### Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scope creep | High | High | Strict change control, prioritization |
| Resource availability | Medium | High | Cross-training, documentation |
| Dependencies delays | Medium | Medium | Parallel work streams, early integration |
| Testing delays | Low | Medium | Continuous testing, automated tests |

---

## Success Metrics

### Development Metrics
- [ ] All 9 pages implemented
- [ ] All 10 custom components built
- [ ] 100% TypeScript coverage
- [ ] Zero critical accessibility violations
- [ ] Lighthouse score >90

### Performance Metrics
- [ ] Initial load <2 seconds
- [ ] Search results <3 seconds
- [ ] Q&A response <5 seconds
- [ ] Compliance check <3 seconds

### Quality Metrics
- [ ] WCAG 2.1 AA compliant
- [ ] Works on all major browsers
- [ ] Works on mobile devices
- [ ] Zero critical bugs
- [ ] User satisfaction >80%

---

## Next Steps

### Immediate Actions (This Week)
1. Review and approve this implementation plan
2. Set up project tracking (Jira/GitHub Projects)
3. Assign team members to phases
4. Begin Phase 0 (Setup & Infrastructure)

### Week 1 Goals
1. Install all dependencies
2. Configure development environment
3. Set up component structure
4. Begin FilterPanel implementation

### Month 1 Goals
1. Complete Phases 0-2 (Setup, Search, Navigation)
2. Have working search with filters
3. Navigation system in place
4. Begin Phase 3 (Compliance)

### Month 2 Goals
1. Complete Phases 3-5 (Compliance, Chat, New Pages Part 1)
2. All core pages functional
3. Begin Phase 6 (New Pages Part 2)

### Month 3 Goals
1. Complete Phases 6-8 (Remaining pages, Polish, Documentation)
2. Full accessibility compliance
3. Performance optimization
4. Ready for production deployment

---

## Appendix

### A. Component Dependency Graph

```
MainLayout
├── Header
│   ├── SearchBar
│   ├── UserMenu
│   └── NotificationCenter
├── Sidebar
│   └── Navigation
├── Main Content
│   └── [Page Components]
└── Footer

Search Page
├── SearchBar (with Autocomplete)
├── FilterPanel
│   ├── Accordion (shadcn)
│   ├── Checkbox (shadcn)
│   └── DatePicker
└── ResultsList
    └── ResultCard
        ├── ConfidenceBadge
        └── CitationTag

Chat Page
├── MessageList
│   ├── UserMessage
│   └── AssistantMessage
│       ├── ConfidenceBadge
│       └── CitationTag
├── ChatInput
└── CitationSidebar

Compliance Page
├── ComplianceForm
│   ├── Form Fields (shadcn)
│   └── ValidationBadges
└── ComplianceReport
    ├── IssueList
    └── Accordion (shadcn)
```

### B. State Management Architecture

```
searchStore
- query, results, filters, loading, error
- setQuery(), search(), updateFilters()

chatStore
- messages, currentQuestion, loading, error
- sendMessage(), addMessage(), clearChat()

complianceStore
- formData, validationResults, report, checking
- updateField(), validateField(), checkCompliance()

userStore (persisted)
- user, preferences, recentSearches, savedRegulations
- setUser(), updatePreferences(), addRecentSearch()
```

### C. File Size Guidelines

**Component Files:**
- Maximum: 300 lines
- Ideal: 150-200 lines
- Strategy: Extract subcomponents, hooks, and utilities

**Page Files:**
- Maximum: 400 lines
- Ideal: 200-300 lines
- Strategy: Extract sections into components

**Hook Files:**
- Maximum: 100 lines
- Ideal: 50-75 lines
- Strategy: One hook per file, focused responsibility

### D. Naming Conventions

**Components:**
- PascalCase: `SearchBar.tsx`, `FilterPanel.tsx`
- One component per file
- Named exports preferred

**Hooks:**
- camelCase with `use` prefix: `useSearch.ts`, `useDebounce.ts`
- Named exports only

**Utilities:**
- camelCase: `formatDate.ts`, `highlightText.ts`
- Named exports

**Types:**
- PascalCase for interfaces: `SearchResult`, `ComplianceReport`
- Defined in `types/index.ts` or component file

### E. Git Workflow

**Branch Strategy:**
- `main` - production-ready code
- `develop` - integration branch
- `feature/phase-X-task-name` - feature branches
- `bugfix/issue-name` - bug fixes

**Commit Messages:**
```
type(scope): subject

body (optional)

footer (optional)
```

Types: feat, fix, docs, style, refactor, test, chore

**Pull Request Process:**
1. Create feature branch from `develop`
2. Implement feature with tests
3. Update documentation
4. Create PR with description
5. Address review comments
6. Merge to `develop`

### F. Testing Strategy

**Unit Tests:**
- All utility functions
- Custom hooks
- Complex component logic

**Component Tests:**
- User interactions
- Accessibility
- Rendering logic

**Integration Tests:**
- API integration
- Store integration
- Page workflows

**E2E Tests:**
- Critical user flows
- Search workflow
- Chat workflow
- Compliance workflow

### G. Performance Budgets

**Bundle Sizes:**
- Initial bundle: <500KB (gzipped)
- Lazy loaded routes: <200KB each
- Third-party libraries: <300KB total

**Network:**
- API responses: <1MB
- Image assets: WebP format, <200KB each
- Font loading: FOUT strategy

**Runtime:**
- Time to Interactive: <3s
- First Input Delay: <100ms
- Cumulative Layout Shift: <0.1

---

## Conclusion

This implementation plan provides a comprehensive, step-by-step roadmap to complete the Regulatory Intelligence Assistant UI. By following this plan systematically and adhering to the specified guidelines, the team can deliver a high-quality, accessible, and performant application that meets all design requirements.

**Key Takeaways:**
1. **Phased Approach**: 8 phases over 10-12 weeks
2. **Priority-Driven**: Critical features first (search, navigation, compliance)
3. **Quality-Focused**: Accessibility, performance, and testing built-in
4. **Documentation**: Comprehensive guides for users and developers
5. **Risk Management**: Identified risks with mitigation strategies

**Success Factors:**
- Clear acceptance criteria for each task
- Regular testing and validation
- Continuous accessibility audits
- Stakeholder involvement
- Flexible prioritization

The plan is designed to be iterative and adaptable, allowing for adjustments based on feedback and changing priorities while maintaining focus on delivering core functionality first.

---

**Document Control:**
- Version: 1.0
- Date: November 24, 2025
- Status: Final
- Next Review: After Phase 2 completion
