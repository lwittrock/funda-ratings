import { useState } from 'react';
import { HashRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import Properties from './pages/Properties';
import Settings from './pages/Settings';
import Summary from './pages/Summary';

// Navigation items
const navItems = [
  { path: '/', label: 'Properties' },
  { path: '/settings', label: 'Settings' },
  { path: '/summary', label: 'Summary' },
];

// Animated hamburger icon
const AnimatedMenuIcon: React.FC<{ isOpen: boolean }> = ({ isOpen }) => (
  <div className="flex flex-col justify-center items-center w-6 h-5 gap-1">
    <span className={`block w-full h-0.5 bg-white transition-all duration-300 ${isOpen ? 'rotate-45 translate-y-[0.4rem]' : ''}`} />
    <span className={`block w-full h-0.5 bg-white transition-all duration-300 ${isOpen ? 'opacity-0' : ''}`} />
    <span className={`block w-full h-0.5 bg-white transition-all duration-300 ${isOpen ? '-rotate-45 -translate-y-[0.4rem]' : ''}`} />
  </div>
);

// Navigation component
function Navigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { pathname } = useLocation();

  const toggleMobileMenu = () => setMobileMenuOpen(!mobileMenuOpen);

  const isActive = (path: string) => pathname === path;

  return (
    <nav className="nav-bar">
      <div className="nav-container">
        {/* Mobile Header */}
        <div className="nav-mobile">
          <span className="nav-logo">Funda Tracker</span>
          <button
            onClick={toggleMobileMenu}
            className="nav-hamburger"
            aria-label="Toggle menu"
          >
            <AnimatedMenuIcon isOpen={mobileMenuOpen} />
          </button>
        </div>

        {/* Desktop Layout */}
        <div className="nav-desktop">
          <span className="nav-logo">Funda Tracker</span>
          <ul className="nav-links">
            {navItems.map((item) => (
              <li key={item.path}>
                <Link 
                  to={item.path} 
                  className={`nav-link ${isActive(item.path) ? 'active' : ''}`}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
          <div style={{ width: '180px' }} />
        </div>

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <ul className="nav-mobile-menu">
            {navItems.map((item) => (
              <li key={item.path}>
                <Link 
                  to={item.path} 
                  onClick={() => setMobileMenuOpen(false)} 
                  className={`nav-mobile-link ${isActive(item.path) ? 'active' : ''}`}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </nav>
  );
}

// App component
function App() {
  return (
    <HashRouter>
      <div className="app">
        <Navigation />
        <main className="max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<Properties />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/summary" element={<Summary />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  );
}

export default App;