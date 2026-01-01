import { Property } from '../types/property';
import { useState } from 'react';

interface PropertyCardProps {
  property: Property;
  onReview: () => void;
  onQuickReject: () => void;
}

export default function PropertyCard({ property, onReview, onQuickReject }: PropertyCardProps) {
  const [imageError, setImageError] = useState(false);

  const getAverageScore = (): number | null => {
    const scores = [
      property.rating_location,
      property.rating_quality,
      property.rating_outside,
      property.rating_value
    ].filter(s => s !== null) as number[];
    
    if (scores.length === 0) return null;
    return scores.reduce((a, b) => a + b, 0) / scores.length;
  };

  const formatDistance = (value: number | string | null): string => {
    if (value === null || value === undefined) return '—';
    if (value === 'N/A') return 'N/A';
    return `${value}`;
  };

  // Build location line
  const buildLocationLine = (): string => {
    const parts = [];
    if (property.distance_station_walk || property.distance_station_bike || property.distance_station_transit) {
      parts.push(`🚶 ${formatDistance(property.distance_station_walk)}min`);
      parts.push(`🚴 ${formatDistance(property.distance_station_bike)}min`);
      parts.push(`🚌 ${formatDistance(property.distance_station_transit)}min`);
    }
    return parts.join(' · ');
  };

  // Build house line
  const buildHouseLine = (): string => {
    const parts = [];
    parts.push(`${property.living_area} m²`);
    if (property.bedrooms) parts.push(`${property.bedrooms} bedrooms`);
    if (property.energy_label) parts.push(`energy: ${property.energy_label}`);
    if (property.construction_year) parts.push(`year ${property.construction_year}`);
    return parts.join(' · ');
  };

  // Build outside line
  const buildOutsideLine = (): string => {
    const parts = [];
    if (property.plot_area) parts.push(`${property.plot_area} m² plot`);
    if (property.has_garden) parts.push('garden');
    if (property.has_parking_on_site) parts.push('garage');
    return parts.join(' · ');
  };

  // Get score color
  const getScoreColor = (score: number): string => {
  if (score >= 4) return 'var(--color-success)'; // Green - #16a34a
  if (score >= 3) return '#f59e0b'; // Amber/yellow
  if (score >= 2) return 'var(--color-warning)'; // Orange - #ea580c
  return 'var(--color-danger)'; // Red - #dc2626
  };

  const locationLine = buildLocationLine();
  const houseLine = buildHouseLine();
  const outsideLine = buildOutsideLine();
  const avgScore = getAverageScore();

  return (
    <a 
      href={property.url} 
      target="_blank" 
      rel="noopener noreferrer"
      className="property-card"
      style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}
    >
      {property.thumbnail_url && !imageError ? (
        <img 
          src={property.thumbnail_url} 
          alt={property.title}
          className="property-image"
          onError={() => setImageError(true)}
        />
      ) : (
        <div className="property-image-placeholder">🏠</div>
      )}
      
      <div className="property-content">
        <div className="property-header">
          <h3 className="property-title">{property.title}, {property.city}</h3>
        </div>
        
        <div className="property-price">
          € {property.price?.toLocaleString('nl-NL')}
        </div>
        
        <div className="property-stats">
          {/* Location */}
          {locationLine && (
            <div className="property-stat">
              <span className="stat-bullet">•</span>
              <span><strong>Location:</strong> {locationLine}</span>
            </div>
          )}
          
          {/* House */}
          <div className="property-stat">
            <span className="stat-bullet">•</span>
            <span><strong>House:</strong> {houseLine}</span>
          </div>
          
          {/* Outside */}
          {outsideLine && (
            <div className="property-stat">
              <span className="stat-bullet">•</span>
              <span><strong>Outside:</strong> {outsideLine}</span>
            </div>
          )}
        </div>
        
        <div className="property-actions" style={{ alignItems: 'center' }}>
          {avgScore !== null && (
            <div 
              className="btn"
              style={{ 
                margin: 0, 
                background: getScoreColor(avgScore),
                color: 'white',
                cursor: 'default'
              }}
            >
              <span className="rating-label">Score: </span>
              <span className="rating-score">{avgScore.toFixed(1)}/5</span>
            </div>
          )}
          
          {property.review_status === 'new' ? (
            <>
              <button 
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onReview();
                }} 
                className="btn btn-success"
              >
                Review
              </button>
              <button 
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onQuickReject();
                }} 
                className="btn btn-danger"
              >
                ✕
              </button>
            </>
          ) : (
            <button 
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onReview();
              }} 
              className="btn btn-secondary"
            >
              Edit
            </button>
          )}
        </div>
      </div>
    </a>
  );
}