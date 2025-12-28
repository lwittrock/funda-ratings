# 🏠 Funda Property Tracker

Track and rate properties from Funda.nl. Python scraper + React frontend + Supabase backend.

## 🚀 Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -r scripts/requirements.txt
npm install

# Create .env file in root
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 2. Setup Supabase

Run the SQL schema from `scripts/supabase-schema.sql` in your Supabase SQL Editor.

### 3. Configure Search

Edit `scripts/config.json`:

```json
{
  "search": {
    "city": "breda",
    "neighborhoods": ["belcrum", "station"],
    "price_min": 500000,
    "price_max": 750000,
    "area_min": 130,
    "max_results": 50
  }
}
```

### 4. Run

```bash
# Search for properties
python scripts/search_supabase.py

# Start frontend
npm run dev
```

## 📊 Features

- **Search**: Automated Funda scraping with custom filters
- **Track**: Properties stored in Supabase with price history
- **Rate**: Score properties on location, quality, garden, value (1-5)
- **Organize**: Filter by status (unreviewed, reviewed, viewing interest, rejected)
- **Mobile-first**: Responsive design with hamburger menu

## 🛠️ Tech Stack

- **Frontend**: React + TypeScript + Tailwind CSS v4 + Vite
- **Backend**: Python + pyfunda
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Vercel / Netlify / GitHub Pages

## 🌐 Deployment

### Vercel (Recommended)

1. Import GitHub repo on vercel.com
2. Add environment variables:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
3. Deploy!

### GitHub Pages

```bash
# Update vite.config.ts
base: '/funda-ratings/'

# Deploy
npm install --save-dev gh-pages
npm run deploy
```

## 📝 Workflow

1. Run `python scripts/search_supabase.py` to scrape properties → saves to Supabase
2. Open web app to review and rate properties → auto-saves to Supabase
3. Access from any device - ratings sync automatically

## 🔮 Future Ideas

- GitHub Actions for automated daily searches
- Email alerts for new properties
- Property comparison view
- Map view with filters

## 📄 License

MIT