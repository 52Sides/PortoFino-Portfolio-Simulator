# PortoFino Frontend

React + TypeScript + Vite application for portfolio simulation, history tracking, and report generation.

## Requirements

- Node.js 20+
- npm or yarn
- Access to backend API (set via `VITE_API_URL`)

## Project Structure
```
src/
api/ Axios client and WebSocket helpers
components/ Reusable UI components (Navbar, MetricCard, forms)
pages/ Application pages (App, HistoryPage)
store/ Zustand auth store
main.tsx Entry point
index.css Tailwind CSS base
App.css Custom app styles
```
## Environment Variables

Set the backend API URL when building or running:
```
VITE_API_URL=http://localhost:8000
```
### Installation
```
npm install
```
### Development

Start the dev server with hot reload:
```
npm run dev
```
Open http://localhost:5173 in your browser.

### Build

Build production-ready assets:
```
npm run build
```
Output will be in the dist/ folder.

### Docker

Build and run frontend container:

```
docker build --build-arg VITE_API_URL=http://backend:8000 -t portofino-frontend .
docker run -p 80:80 -p 443:443 portofino-frontend
```

#### Notes

- Nginx serves static files and proxies /api/ requests to backend.
- Tailwind dark mode is controlled via dark class on html element.
- React Router SPA routing works through try_files in nginx.

### Testing 

#### Unit

```
npm run test
```

#### E2E (Playwright)

```
npx playwright test
```

### This frontend handles:

- Login, registration, and token management
- Portfolio simulation with live WebSocket updates
- Viewing historical simulations
- Generating and downloading XLSX reports