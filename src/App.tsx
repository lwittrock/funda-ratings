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

  const linkClass = (path: string) => {
    const isActive = pathname === path;
    if (mobileMenuOpen) {
      return `block py-3 px-4 rounded transition-colors ${
        isActive ? 'text-blue-400 font-semibold bg-gray-700/50' : 'text-white hover:bg-gray-700/30'
      }`;
    }
    return `transition duration-300 ${
      isActive ? 'text-blue-400 font-semibold' : 'text-white hover:text-blue-400'
    }`;
  };

  return (
    <nav className="bg-gray-800 p-4 shadow-md">
      <div className="max-w-7xl mx-auto">
        {/* Mobile Header */}
        <div className="flex justify-between items-center lg:hidden">
          <span className="text-white font-bold text-lg">🏠 Funda Tracker</span>
          <button
            onClick={toggleMobileMenu}
            className="text-white p-2 hover:bg-gray-700 rounded"
            aria-label="Toggle menu"
            style={{ WebkitTapHighlightColor: 'transparent' }}
          >
            <AnimatedMenuIcon isOpen={mobileMenuOpen} />
          </button>
        </div>

        {/* Desktop Links */}
        <ul className="hidden lg:flex justify-center space-x-24">
          {navItems.map((item) => (
            <li key={item.path}>
              <Link to={item.path} className={linkClass(item.path)}>
                {item.label}
              </Link>
            </li>
          ))}
        </ul>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <ul className="lg:hidden mt-4 space-y-1 pt-4 border-t border-gray-700">
            {navItems.map((item) => (
              <li key={item.path}>
                <Link to={item.path} onClick={() => setMobileMenuOpen(false)} className={linkClass(item.path)}>
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