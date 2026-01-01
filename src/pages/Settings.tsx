import { useState, useEffect } from 'react';
import { SearchConfig } from '../types/property';
import { supabase } from '../lib/supabase';
import { MapPin, Euro, Ruler, Play, Pause, Edit, Trash2, Trees, Car } from 'lucide-react';

export default function Settings() {
  const [configs, setConfigs] = useState<SearchConfig[]>([]);
  const [, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState<Partial<SearchConfig>>({
    city: '',
    neighborhoods: [],
    price_min: 500000,
    price_max: 750000,
    area_min: 130,
    max_results: 50,
    require_garden: false,
    require_parking: false,
    max_distance_mode: null,
    max_distance_minutes: null,
    active: true
  });
  const [neighborhoodInput, setNeighborhoodInput] = useState('');

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from('search_configs')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;
      setConfigs(data || []);
    } catch (error) {
      console.error('Error loading configs:', error);
      alert('Error loading search configurations');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      if (!formData.city) {
        alert('City is required');
        return;
      }

      if (editingId) {
        const { error } = await supabase
          .from('search_configs')
          .update(formData)
          .eq('id', editingId);

        if (error) throw error;
      } else {
        const { error } = await supabase
          .from('search_configs')
          .insert([formData]);

        if (error) throw error;
      }

      setFormData({
        city: '',
        neighborhoods: [],
        price_min: 500000,
        price_max: 750000,
        area_min: 130,
        max_results: 50,
        require_garden: false,
        require_parking: false,
        max_distance_mode: null,
        max_distance_minutes: null,
        active: true
      });
      setEditingId(null);
      setNeighborhoodInput('');
      
      await loadConfigs();
    } catch (error) {
      console.error('Error saving config:', error);
      alert('Error saving configuration');
    }
  };

  const handleEdit = (config: SearchConfig) => {
    setEditingId(config.id);
    setFormData({
      city: config.city,
      neighborhoods: config.neighborhoods,
      price_min: config.price_min,
      price_max: config.price_max,
      area_min: config.area_min,
      max_results: config.max_results,
      require_garden: config.require_garden,
      require_parking: config.require_parking,
      active: config.active
    });
    setNeighborhoodInput(config.neighborhoods.join(', '));
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this search configuration?')) {
      return;
    }

    try {
      const { error } = await supabase
        .from('search_configs')
        .delete()
        .eq('id', id);

      if (error) throw error;
      await loadConfigs();
    } catch (error) {
      console.error('Error deleting config:', error);
      alert('Error deleting configuration');
    }
  };

  const handleToggleActive = async (id: number, currentActive: boolean) => {
    try {
      const { error } = await supabase
        .from('search_configs')
        .update({ active: !currentActive })
        .eq('id', id);

      if (error) throw error;
      await loadConfigs();
    } catch (error) {
      console.error('Error toggling active:', error);
      alert('Error updating configuration');
    }
  };

  const handleCancel = () => {
    setEditingId(null);
    setFormData({
      city: '',
      neighborhoods: [],
      price_min: 500000,
      price_max: 750000,
      area_min: 130,
      max_results: 50,
      require_garden: false,
      require_parking: false,
      active: true
    });
    setNeighborhoodInput('');
  };

  const parseNeighborhoods = (input: string): string[] => {
    return input
      .split(',')
      .map(n => n.trim().toLowerCase())
      .filter(n => n.length > 0);
  };

  return (
    <div className="main-content">
      <div className="section-header">
        <h2 className="section-title">Search Settings</h2>
        <p className="section-subtitle">Manage your Funda search configurations</p>
      </div>

      {/* Form */}
      <div className="settings-form-compact">
        <h4 className="settings-form-title">
          {editingId ? 'Edit Configuration' : 'New Configuration'}
        </h4>

        <div className="form-group-compact">
          <label className="form-label">
            City or Cities (comma-separated) *
          </label>
          <input
            type="text"
            value={formData.city}
            onChange={(e) => setFormData({ ...formData, city: e.target.value.toLowerCase() })}
            className="form-input"
            placeholder="e.g. breda  or  etten-leur, rijen, delft"
          />
          <small style={{ fontSize: '0.85em', color: '#666', marginTop: '0.25rem', display: 'block' }}>
            💡 You can search multiple cities at once: "breda, tilburg" or single city: "delft"
          </small>
        </div>

        <div className="form-group-compact">
          <label className="form-label">Neighborhoods (comma-separated, optional)</label>
          <input
            type="text"
            value={neighborhoodInput}
            onChange={(e) => {
              setNeighborhoodInput(e.target.value);
              setFormData({ ...formData, neighborhoods: parseNeighborhoods(e.target.value) });
            }}
            className="form-input"
            placeholder="e.g. station, centrum"
          />
          <small style={{ fontSize: '0.85em', color: '#666', marginTop: '0.25rem', display: 'block' }}>
            Leave empty to search entire city/cities
          </small>
        </div>

        <div className="form-row">
          <div className="form-group-compact">
            <label className="form-label">Min Price (€)</label>
            <input
              type="number"
              value={formData.price_min}
              onChange={(e) => setFormData({ ...formData, price_min: Number(e.target.value) })}
              className="form-input"
              step="10000"
            />
          </div>

          <div className="form-group-compact">
            <label className="form-label">Max Price (€)</label>
            <input
              type="number"
              value={formData.price_max}
              onChange={(e) => setFormData({ ...formData, price_max: Number(e.target.value) })}
              className="form-input"
              step="10000"
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group-compact">
            <label className="form-label">Min Area (m²)</label>
            <input
              type="number"
              value={formData.area_min}
              onChange={(e) => setFormData({ ...formData, area_min: Number(e.target.value) })}
              className="form-input"
            />
          </div>

          <div className="form-group-compact">
            <label className="form-label">Max Results</label>
            <input
              type="number"
              value={formData.max_results}
              onChange={(e) => setFormData({ ...formData, max_results: Number(e.target.value) })}
              className="form-input"
              min="1"
              max="100"
            />
          </div>
        </div>

        <div className="form-group-compact">
          <label className="form-label" style={{ marginBottom: '0.75rem', display: 'block' }}>
            Distance to Station Filter (Optional)
          </label>
          
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <label className="form-label" style={{ fontSize: '0.85rem' }}>Transport Mode</label>
              <select
                value={formData.max_distance_mode || ''}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  max_distance_mode: (e.target.value as "walk" | "bike" | "transit") || null
                })}
                className="form-input"
              >
                <option value="">No distance filter</option>
                <option value="walk">Walking</option>
                <option value="bike">Biking</option>
                <option value="transit">Public Transit</option>
              </select>
            </div>

            <div style={{ flex: 1 }}>
              <label className="form-label" style={{ fontSize: '0.85rem' }}>Max Minutes</label>
              <input
                type="number"
                value={formData.max_distance_minutes || ''}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  max_distance_minutes: e.target.value ? Number(e.target.value) : null 
                })}
                className="form-input"
                placeholder="e.g. 15"
                disabled={!formData.max_distance_mode}
                min="1"
                max="60"
              />
            </div>
          </div>
          
          <small style={{ fontSize: '0.85em', color: '#666', marginTop: '0.25rem', display: 'block' }}>
            💡 Example: "Walking" + "15" = only properties within 15min walk
          </small>
        </div>

        <div className="form-group-compact">
          <label className="form-label" style={{ marginBottom: '0.75rem', display: 'block' }}>
            Required Features
          </label>
          
          <label className="checkbox-label" style={{ marginBottom: '0.5rem' }}>
            <input
              type="checkbox"
              checked={formData.require_garden || false}
              onChange={(e) => setFormData({ ...formData, require_garden: e.target.checked })}
              className="checkbox-input"
            />
            <Trees size={16} style={{ marginLeft: '0.5rem', marginRight: '0.25rem' }} />
            <span>Must have garden</span>
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={formData.require_parking || false}
              onChange={(e) => setFormData({ ...formData, require_parking: e.target.checked })}
              className="checkbox-input"
            />
            <Car size={16} style={{ marginLeft: '0.5rem', marginRight: '0.25rem' }} />
            <span>Must have parking</span>
          </label>
        </div>

        <div className="form-group-compact">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={formData.active}
              onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
              className="checkbox-input"
            />
            <span>Active (include in daily searches)</span>
          </label>
        </div>

        <div className="form-actions">
          <button onClick={handleSave} className="btn btn-success">
            {editingId ? 'Update' : 'Create'}
          </button>
          {editingId && (
            <button onClick={handleCancel} className="btn btn-secondary">
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* List of existing configs */}
      <div className="configs-section">
        <h4 className="configs-title">
          Saved Configurations ({configs.length})
        </h4>

        {configs.length === 0 ? (
          <p className="configs-empty">
            No configurations yet. Create one above!
          </p>
        ) : (
          <div className="config-list">
            {configs.map(config => {
              const cities = config.city.split(',').map(c => c.trim());
              const cityDisplay = cities.length > 1 
                ? `${cities.length} cities: ${cities.map(c => c.charAt(0).toUpperCase() + c.slice(1)).join(', ')}`
                : cities[0].charAt(0).toUpperCase() + cities[0].slice(1);

              return (
                <div key={config.id} className={`config-item ${!config.active ? 'inactive' : ''}`}>
                  <div className="config-info">
                    <div className="config-header">
                      <h5 className="config-name">
                        {cityDisplay}
                      </h5>
                      <span className={`status-badge ${config.active ? 'active' : 'inactive'}`}>
                        {config.active ? '● Active' : '○ Inactive'}
                      </span>
                    </div>
                    <div className="config-details">
                      {config.neighborhoods.length > 0 && (
                        <div className="config-detail">
                          <MapPin size={14} />
                          <span>{config.neighborhoods.join(', ')}</span>
                        </div>
                      )}
                      <div className="config-detail">
                        <Euro size={14} />
                        <span>€{config.price_min.toLocaleString()} - €{config.price_max.toLocaleString()}</span>
                      </div>
                      <div className="config-detail">
                        <Ruler size={14} />
                        <span>{config.area_min}m² min · {config.max_results} results max</span>
                      </div>
                      {(config.require_garden || config.require_parking) && (
                        <div className="config-detail">
                          {config.require_garden && (
                            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              <Trees size={14} />
                              Garden
                            </span>
                          )}
                          {config.require_parking && (
                            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginLeft: config.require_garden ? '0.5rem' : 0 }}>
                              <Car size={14} />
                              Parking
                            </span>
                          )}
                        </div>
                      )}
                      {config.max_distance_mode && (
                        <div className="config-detail">
                          <span>
                            Max {config.max_distance_mode}: {config.max_distance_minutes}min to station
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="config-actions">
                    <button
                      onClick={() => handleToggleActive(config.id, config.active)}
                      className="btn-icon"
                      title={config.active ? 'Deactivate' : 'Activate'}
                    >
                      {config.active ? <Pause size={18} /> : <Play size={18} />}
                    </button>
                    <button
                      onClick={() => handleEdit(config)}
                      className="btn-icon"
                      title="Edit"
                    >
                      <Edit size={18} />
                    </button>
                    <button
                      onClick={() => handleDelete(config.id)}
                      className="btn-icon danger"
                      title="Delete"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Info box */}
      <div style={{ 
        marginTop: '2rem', 
        padding: '1rem', 
        backgroundColor: '#f0f9ff', 
        borderRadius: '0.5rem',
        border: '1px solid #bae6fd'
      }}>
        <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', fontWeight: 600 }}>
          💡 Distance Filtering
        </h5>
        <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.5, color: '#0c4a6e' }}>
          Set a custom distance filter per config, or leave it empty to get all properties. The Python script will calculate distances for all available transport modes, then filter based on your chosen mode and time limit.
        </p>
      </div>
    </div>
  );
}