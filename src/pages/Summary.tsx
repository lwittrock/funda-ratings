import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { Property } from '../types/property';
import { supabase } from '../lib/supabase';
import 'leaflet/dist/leaflet.css';

const STATUS_COLORS = {
  interested: '#16a34a', // green
  reviewed: '#2563eb',   // blue
  new: '#dc2626',        // red
  rejected: '#d1d5db'    // light gray
};

interface TimelineData {
  date: string;
  count: number;
}

export default function Summary() {
  const [activeTab, setActiveTab] = useState('stats');
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProperties();
  }, []);

  const loadProperties = async () => {
    try {
      const { data, error } = await supabase
        .from('properties')
        .select('*')
        .order('created_at', { ascending: true });

      if (error) throw error;
      setProperties(data || []);
    } catch (error) {
      console.error('Error loading properties:', error);
    } finally {
      setLoading(false);
    }
  };

  // Calculate statistics
  const stats = {
    total: properties.length,
    new: properties.filter(p => p.review_status === 'new').length,
    reviewed: properties.filter(p => p.review_status === 'reviewed').length,
    interested: properties.filter(p => p.review_status === 'interested').length,
    rejected: properties.filter(p => p.review_status === 'rejected').length,
  };

  // Calculate average ratings for reviewed properties (reviewed + interested)
  const reviewedProps = properties.filter(p => 
    p.review_status === 'reviewed' || p.review_status === 'interested'
  );

  const calculateAvgRating = (field: keyof Pick<Property, 'rating_location' | 'rating_quality' | 'rating_outside' | 'rating_value'>) => {
    const rated = reviewedProps.filter(p => p[field] != null);
    if (rated.length === 0) return 0;
    const sum = rated.reduce((acc, p) => acc + (p[field] || 0), 0);
    return (sum / rated.length).toFixed(1);
  };

  const avgRatings = {
    location: calculateAvgRating('rating_location'),
    quality: calculateAvgRating('rating_quality'),
    outside: calculateAvgRating('rating_outside'),
    value: calculateAvgRating('rating_value'),
  };

  // Prepare timeline data (properties added per day)
  const timelineData = (): TimelineData[] => {
    const dateCounts: Record<string, number> = {};
    
    properties.forEach(prop => {
      if (prop.created_at) {
        const date = new Date(prop.created_at).toISOString().split('T')[0];
        dateCounts[date] = (dateCounts[date] || 0) + 1;
      }
    });

    return Object.entries(dateCounts)
      .map(([date, count]) => ({ date, count }))
      .sort((a, b) => a.date.localeCompare(b.date));
  };

  // Get properties with coordinates for map
  const mapProperties = properties.filter(p => p.latitude && p.longitude);

  if (loading) {
    return (
      <div style={{ 
        minHeight: '80vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        fontSize: '1.25rem',
        color: 'var(--text-secondary)'
      }}>
        Loading summary...
      </div>
    );
  }

  return (
    <div className="main-content">
      {/* Section Header */}
      <div className="section-header">
        <h2 className="section-title">Summary</h2>
        <p className="section-subtitle">Statistics and insights for your property search</p>
      </div>

      {/* Tab Navigation */}
      <div className="filter-buttons" style={{ marginBottom: '2rem' }}>
        <button
          onClick={() => setActiveTab('stats')}
          className={`filter-button ${activeTab === 'stats' ? 'active' : ''}`}
        >
          <span className="filter-label">Statistics</span>
        </button>
        <button
          onClick={() => setActiveTab('timeline')}
          className={`filter-button ${activeTab === 'timeline' ? 'active' : ''}`}
        >
          <span className="filter-label">Timeline</span>
        </button>
        <button
          onClick={() => setActiveTab('map')}
          className={`filter-button ${activeTab === 'map' ? 'active' : ''}`}
        >
          <span className="filter-label">Map</span>
        </button>
      </div>

      {/* Statistics Tab */}
      {activeTab === 'stats' && (
        <div>
          {/* Property Count Cards */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '0.75rem',
            marginBottom: '2rem'
          }}>
            <div style={{ 
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '0.5rem',
              padding: '1rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                {stats.total}
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                Total
              </div>
            </div>

            <div style={{ 
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '0.5rem',
              padding: '1rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '2rem', fontWeight: '700', color: STATUS_COLORS.new }}>
                {stats.new}
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                New
              </div>
            </div>

            <div style={{ 
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '0.5rem',
              padding: '1rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '2rem', fontWeight: '700', color: STATUS_COLORS.reviewed }}>
                {stats.reviewed}
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                Reviewed
              </div>
            </div>

            <div style={{ 
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '0.5rem',
              padding: '1rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '2rem', fontWeight: '700', color: STATUS_COLORS.interested }}>
                {stats.interested}
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                Interested
              </div>
            </div>

            <div style={{ 
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '0.5rem',
              padding: '1rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '2rem', fontWeight: '700', color: STATUS_COLORS.rejected }}>
                {stats.rejected}
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                Rejected
              </div>
            </div>
          </div>

          {/* Average Ratings */}
          {reviewedProps.length > 0 && (
            <div style={{ 
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '0.5rem',
              padding: '1.25rem'
            }}>
              <h3 style={{ 
                fontSize: '1rem', 
                fontWeight: '600', 
                marginBottom: '0.5rem',
                color: 'var(--text-primary)'
              }}>
                Average Ratings
              </h3>
              <p style={{ 
                fontSize: '0.8125rem', 
                color: 'var(--text-secondary)', 
                marginBottom: '1.25rem' 
              }}>
                Based on {reviewedProps.length} reviewed properties
              </p>
              
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                gap: '1.25rem'
              }}>
                <div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '0.375rem' }}>
                    Location
                  </div>
                  <div style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--color-primary)' }}>
                    {avgRatings.location} <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: '500' }}>/5</span>
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '0.375rem' }}>
                    Quality
                  </div>
                  <div style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--color-primary)' }}>
                    {avgRatings.quality} <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: '500' }}>/5</span>
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '0.375rem' }}>
                    Outside
                  </div>
                  <div style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--color-primary)' }}>
                    {avgRatings.outside} <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: '500' }}>/5</span>
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '0.375rem' }}>
                    Value
                  </div>
                  <div style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--color-primary)' }}>
                    {avgRatings.value} <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: '500' }}>/5</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Timeline Tab */}
      {activeTab === 'timeline' && (
        <div className="property-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ 
            fontSize: '1.125rem', 
            fontWeight: '600', 
            marginBottom: '1.5rem',
            color: 'var(--text-primary)'
          }}>
            Properties Added Over Time
          </h3>
          
          {timelineData().length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={timelineData()}>
                <XAxis 
                  dataKey="date" 
                  stroke="var(--text-muted)"
                  style={{ fontSize: '0.75rem' }}
                  tickFormatter={(date: string) => {
                    const d = new Date(date);
                    return `${d.getMonth() + 1}/${d.getDate()}`;
                  }}
                />
                <YAxis 
                  stroke="var(--text-muted)"
                  style={{ fontSize: '0.75rem' }}
                  allowDecimals={false}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '0.5rem'
                  }}
                  labelFormatter={(date: string) => new Date(date).toLocaleDateString()}
                  formatter={(value: number | undefined) => [`${value || 0} properties`, 'Added']}
                />
                <Bar 
                  dataKey="count" 
                  fill="var(--color-primary)"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
              No timeline data available
            </div>
          )}
        </div>
      )}

      {/* Map Tab */}
      {activeTab === 'map' && (
        <div className="property-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ 
            fontSize: '1.125rem', 
            fontWeight: '600', 
            marginBottom: '1rem',
            color: 'var(--text-primary)'
          }}>
            Property Locations
          </h3>
          <p style={{ 
            fontSize: '0.875rem', 
            color: 'var(--text-secondary)', 
            marginBottom: '1rem' 
          }}>
            {mapProperties.length} of {properties.length} properties have location data
          </p>

          {mapProperties.length > 0 ? (
            <div style={{ height: '600px', borderRadius: '0.5rem', overflow: 'hidden' }}>
              <MapContainer
                center={[mapProperties[0].latitude!, mapProperties[0].longitude!]}
                zoom={11}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
                  url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                />
                
                {mapProperties.map((property) => (
                  <CircleMarker
                    key={property.id}
                    center={[property.latitude!, property.longitude!]}
                    radius={8}
                    fillColor={STATUS_COLORS[property.review_status]}
                    color="#fff"
                    weight={2}
                    opacity={property.review_status === 'rejected' ? 0.3 : 1}
                    fillOpacity={property.review_status === 'rejected' ? 0.3 : 0.8}
                  >
                    <Popup>
                      <div style={{ minWidth: '200px' }}>
                        <strong style={{ fontSize: '0.9rem' }}>{property.title}</strong>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                          {property.city}
                        </div>
                        <div style={{ fontSize: '0.9rem', fontWeight: '600', marginTop: '0.5rem' }}>
                          {property.price_formatted}
                        </div>
                        <div style={{ 
                          fontSize: '0.75rem', 
                          marginTop: '0.5rem',
                          padding: '0.25rem 0.5rem',
                          backgroundColor: STATUS_COLORS[property.review_status],
                          color: 'white',
                          borderRadius: '0.25rem',
                          display: 'inline-block'
                        }}>
                          {property.review_status}
                        </div>
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
              </MapContainer>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🗺️</div>
              <p>No properties with location data yet.</p>
              <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
                Run the search script to fetch coordinates.
              </p>
            </div>
          )}

          {/* Legend */}
          {mapProperties.length > 0 && (
            <div style={{ 
              display: 'flex', 
              gap: '1.5rem', 
              marginTop: '1rem',
              fontSize: '0.875rem',
              flexWrap: 'wrap'
            }}>
              {Object.entries(STATUS_COLORS).map(([status, color]) => (
                <div key={status} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{ 
                    width: '16px', 
                    height: '16px', 
                    borderRadius: '50%',
                    backgroundColor: color,
                    border: '2px solid #fff',
                    opacity: status === 'rejected' ? 0.3 : 1
                  }} />
                  <span style={{ textTransform: 'capitalize' }}>{status}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}