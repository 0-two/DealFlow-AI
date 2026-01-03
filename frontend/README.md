# DealFlow AI Frontend

Next.js 14 frontend for DealFlow AI - RAG-based Investor and Deal Analysis Platform.

## Features

- 🤖 **AI Query Engine** - Multi-language RAG pipeline with LLM-powered insights
- 📊 **Analytics Dashboard** - Sector trends, timeline analysis, and funding statistics
- 💼 **Investor Search** - Smart filtering and personalized recommendations
- 📥 **Data Ingestion** - Upload PDFs, CSVs, and web content seamlessly

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: TanStack React Query
- **HTTP Client**: Axios
- **Charts**: Recharts
- **Icons**: Lucide React
- **Date Handling**: date-fns

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local

# Update .env.local with your API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

```bash
# Start development server
npm run dev

# Server runs at http://localhost:3000
```

### Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx              # Home page
│   ├── investors/
│   │   └── page.tsx          # Investor search page
│   ├── trends/
│   │   └── page.tsx          # Trends analysis page
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles
├── components/
│   ├── Chat/                 # Chat components
│   ├── Investors/            # Investor-related components
│   ├── Trends/               # Trends-related components
│   ├── Layout/               # Layout components
│   └── Common/               # Shared components
├── lib/
│   ├── api.ts                # API client and endpoints
│   ├── types.ts              # TypeScript types
│   └── utils.ts              # Utility functions
├── public/                   # Static assets
├── .env.local                # Environment variables
└── package.json              # Dependencies
```

## API Integration

The frontend connects to the backend API (default: `http://localhost:8000`).

### Available API Endpoints

- **Query**: `/api/query` - RAG-powered question answering
- **Investors**: `/api/investors` - Investor search and recommendations
- **Trends**: `/api/trends` - Funding trends and analytics
- **Ingestion**: `/api/ingest` - Document and URL ingestion

See [lib/api.ts](./lib/api.ts) for detailed API client implementation.

## Environment Variables

Create `.env.local` file:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development Tips

1. **Type Safety**: Use TypeScript types from `lib/types.ts`
2. **API Calls**: Use exported functions from `lib/api.ts`
3. **Utilities**: Common helpers are in `lib/utils.ts`
4. **Styling**: Use Tailwind CSS classes (see `globals.css` for custom styles)
5. **Error Handling**: Use `handleApiError` from `lib/api.ts`

## Performance Optimizations

- Image optimization with Next.js Image component
- Code splitting with dynamic imports
- React Query for server state management
- Tailwind CSS for minimal CSS output

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

This project is part of DealFlow AI.
