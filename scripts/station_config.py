"""
Station configuration for distance calculations
Defines which station to use for each city and acceptable transport modes
"""

STATION_CONFIG = {
    'breda': {
        'station': 'Breda Station, Netherlands',
        'modes': ['walk', 'bike'],  # walk and bike times matter
        'max_walk': 25,  # minutes - used for filtering
        'max_bike': 15,  # minutes
        'max_transit': None,  # not used for filtering
    },
    'etten-leur': {
        'station': 'Etten-Leur Station, Netherlands',
        'modes': ['walk'],
        'max_walk': 15,
        'max_bike': None,
        'max_transit': None,
    },
    'delft': {
        'station': 'Delft Station, Netherlands',
        'modes': ['walk'],
        'max_walk': 15,
        'max_bike': None,
        'max_transit': None,
    },
    'tilburg': {
        'station': 'Tilburg Station, Netherlands',
        'modes': ['walk', 'bike'],
        'max_walk': 25,
        'max_bike': 15,
        'max_transit': None,
    },
    'rijen': {
        'station': 'Station Gilze-Rijen, Netherlands',
        'modes': ['walk', 'bike'],
        'max_walk': 20,
        'max_bike': 10,
        'max_transit': None,
    },
    'teteringen': {
        'station': 'Breda Station, Netherlands',  # Use Breda as destination
        'modes': ['transit'],  # Only care about bus connection
        'max_walk': None,
        'max_bike': None,
        'max_transit': 20,  # Max 20min by bus to Breda
        'note': 'No local station - uses bus to Breda'
    },
}


def get_station_for_city(city: str) -> dict | None:
    """
    Get station configuration for a city
    
    Args:
        city: City name (case-insensitive)
        
    Returns:
        Station config dict or None if city not configured
    """
    if not city:
        return None
    
    city_normalized = city.lower().strip()
    return STATION_CONFIG.get(city_normalized)


def should_calculate_mode(city: str, mode: str) -> bool:
    """
    Check if we should calculate a specific transport mode for a city
    
    Args:
        city: City name
        mode: 'walk', 'bike', or 'transit'
        
    Returns:
        True if this mode should be calculated for this city
    """
    config = get_station_for_city(city)
    if not config:
        return False
    
    return mode in config.get('modes', [])


def get_max_time_for_mode(city: str, mode: str) -> int | None:
    """
    Get maximum acceptable time for a transport mode in a city
    
    Args:
        city: City name
        mode: 'walk', 'bike', or 'transit'
        
    Returns:
        Max time in minutes, or None if no limit
    """
    config = get_station_for_city(city)
    if not config:
        return None
    
    mode_key = f'max_{mode}'
    return config.get(mode_key)


def passes_distance_filter(property_data: dict) -> bool:
    """
    Check if a property passes the distance filters for its city
    
    Args:
        property_data: Property dict with city and distance fields
        
    Returns:
        True if property passes filters (or no filters defined)
    """
    city = property_data.get('city')
    config = get_station_for_city(city)
    
    if not config:
        # No config for this city - accept by default
        return True
    
    # Check each configured mode
    for mode in config.get('modes', []):
        max_time = get_max_time_for_mode(city, mode)
        if max_time is None:
            continue
        
        # Get the distance for this mode
        distance_key = f'distance_station_{mode}'
        distance = property_data.get(distance_key)
        
        # If distance not calculated yet, accept it (will be filtered later)
        if distance is None or distance == 'N/A':
            continue
        
        # Check if it exceeds the max
        if isinstance(distance, (int, float)) and distance > max_time:
            return False
    
    return True