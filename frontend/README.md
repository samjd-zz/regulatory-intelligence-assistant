# Regulatory Intelligence Assistant - Frontend

A modern React-based web interface for navigating complex laws, policies, and regulations with AI-powered assistance.

## 🚀 Tech Stack

- **Framework**: React 19.2 with TypeScript 5.9
- **Build Tool**: Vite 7.2
- **Styling**: Tailwind CSS v4 (with @tailwindcss/forms and @tailwindcss/typography)
- **State Management**: Zustand 5.0
- **Routing**: React Router v7
- **Data Fetching**: TanStack Query (React Query) v5
- **HTTP Client**: Axios 1.13
- **Form Handling**: React Hook Form 7.66 with Zod 4.1 validation
- **Icons**: Lucide React 0.554

## 📋 Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

## 🛠️ Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   └── shared/          # Shared components (badges, spinners, etc.)
│   ├── pages/               # Page components
│   │   ├── Dashboard.tsx    # Homepage with quick actions
│   │   ├── Search.tsx       # Regulation search interface
│   │   ├── Chat.tsx         # Q&A chat interface
│   │   └── Compliance.tsx   # Compliance checking form
│   ├── services/            # API service layer
│   │   └── api.ts          # Axios client and API functions
│   ├── store/               # Zustand state management
│   │   ├── searchStore.ts   # Search state
│   │   ├── chatStore.ts     # Chat state
│   │   ├── complianceStore.ts # Compliance state
│   │   └── userStore.ts     # User preferences (persisted)
│   ├── types/               # TypeScript interfaces
│   │   └── index.ts        # Shared type definitions
│   ├── lib/                 # Utility functions
│   │   └── utils.ts        # Helper functions (cn, formatDate, etc.)
│   ├── App.tsx             # Root component with routing
│   ├── main.tsx            # Application entry point
│   └── index.css           # Global styles with Tailwind
├── public/                  # Static assets
├── vite.config.ts          # Vite configuration
├── tailwind.config.js      # Tailwind theme configuration
├── tsconfig.json           # TypeScript configuration
└── package.json            # Dependencies and scripts
```

## 🎨 Key Features

### 1. Dashboard (`/`)
- Quick action cards for Search, Q&A, and Compliance
- Statistics display (regulations indexed, response time, accuracy)
- Clean, accessible interface

### 2. Search Regulations (`/search`)
- Natural language search with semantic understanding
- Faceted filtering (jurisdiction, program, date range)
- Search results with confidence scores
- Citation display and copying
- Related regulations suggestions

### 3. Ask Questions (`/chat`)
- Conversational AI interface
- Context-aware responses
- Citation tracking for all answers
- Confidence indicators
- Chat history with message persistence

### 4. Check Compliance (`/compliance`)
- Form/document validation against regulations
- Multi-field compliance checking
- Visual compliance indicators (pass/fail/warning)
- Detailed explanation of requirements
- Downloadable compliance reports

## 🎯 State Management

The application uses Zustand for lightweight, flexible state management:

- **searchStore**: Manages search queries, results, filters, and history
- **chatStore**: Handles chat messages, AI responses, and conversation state
- **complianceStore**: Controls compliance checks and validation results
- **userStore**: Persists user preferences (theme, language) to localStorage

## 🔌 API Integration

The frontend communicates with the backend API through Axios with:

- Base URL configuration: `http://localhost:8000/api`
- Request/response interceptors for error handling
- Loading state management
- Automatic retry logic via React Query

### API Endpoints Used

- `POST /search` - Semantic search for regulations
- `POST /chat` - Q&A with AI assistance
- `POST /compliance/check` - Validate compliance
- `GET /documents/:id` - Fetch regulation details
- `GET /suggestions` - Get query suggestions

## 🎨 Styling

### Tailwind CSS v4

The application uses Tailwind CSS v4 with the new import syntax:

```css
@import "tailwindcss";
```

### Custom Theme

Custom colors defined in `tailwind.config.js`:

- **Primary Colors**: Blue palette for main UI elements
- **Confidence Colors**: 
  - High: Green (#10b981)
  - Medium: Yellow (#f59e0b)
  - Low: Red (#ef4444)

### Typography

- **Font**: Inter (system fallback: system-ui, sans-serif)
- **Typography Plugin**: @tailwindcss/typography for rich content
- **Forms Plugin**: @tailwindcss/forms for consistent form styling

## 🧪 Development

### Available Scripts

```bash
# Start development server (with HMR)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Code Quality

- TypeScript for type safety
- ESLint for code quality
- Consistent file naming (PascalCase for components)
- Component-based architecture

## 🚀 Build & Deployment

1. Build the production bundle:
```bash
npm run build
```

2. The optimized files will be in the `dist/` directory

3. Preview the build:
```bash
npm run preview
```

4. Deploy the `dist/` directory to your hosting service

### Environment Variables

The application uses Vite's proxy configuration for API calls. In production, update the API base URL in `src/services/api.ts`:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
```

## ♿ Accessibility

The application follows WCAG 2.1 Level AA standards:

- Semantic HTML elements
- ARIA labels and roles
- Keyboard navigation support
- Focus indicators
- Color contrast compliance
- Screen reader optimization

## 🔒 Security Considerations

- Input sanitization via Zod validation
- XSS protection through React's built-in escaping
- CORS configuration handled by backend
- No sensitive data in localStorage (except user preferences)

## 📱 Responsive Design

The interface is fully responsive with breakpoints:

- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

## 🐛 Debugging

### Common Issues

1. **API Connection Errors**
   - Ensure backend is running on port 8000
   - Check CORS configuration
   - Verify API endpoints match backend routes

2. **Styling Issues**
   - Clear browser cache
   - Rebuild Tailwind: `npm run build`
   - Check PostCSS configuration

3. **TypeScript Errors**
   - Verify all interfaces match API responses
   - Check import paths use `@/` alias
   - Run `npm run build` to check for type errors

## 📚 Further Documentation

- [Main Project README](../README.md)
- [UI Design Spec](../docs/ui-design.md)
- [Backend API Docs](../backend/README.md)
- [Development Plan](../docs/parallel-plan.md)

## 🤝 Contributing

1. Follow the existing code structure
2. Use TypeScript for all new files
3. Add proper types for API responses
4. Test responsive behavior on multiple devices
5. Ensure accessibility standards are met

## 📄 License

Part of the Regulatory Intelligence Assistant project for the G7 GovAI Challenge.
