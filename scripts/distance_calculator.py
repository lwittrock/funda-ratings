"""
Distance calculation module
Handles Google Maps API calls for calculating distances to train stations
"""

import os
import requests
import time
from typing import Optional, Union
from station_config import get_station_for_city, should_calculate_mode

GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')


def calculate_distance_to_station(
    property_address: str,
    station_address: str,
    mode: str = 'walking'
) -> Union[int, str]:
    """
    Calculate travel time to station using Google Maps Distance Matrix API
    
    Args:
        property_address: Full address of the property
        station_address: Address of the train station
        mode: 'walking', 'bicycling', or 'transit'
    
    Returns:
        int: Travel time in minutes, or 'N/A' if route not available
    """
    if not GOOGLE_MAPS_API_KEY:
        return None
    
    try:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            'origins': property_address,
            'destinations': station_address,
            'mode': mode,
            'key': GOOGLE_MAPS_API_KEY,
            'language': 'nl',
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check if we got valid results
        if data.get('status') != 'OK':
            return 'N/A'
        
        rows = data.get('rows', [])
        if not rows or not rows[0].get('elements'):
            return 'N/A'
        
        element = rows[0]['elements'][0]
        
        # Check element status
        if element.get('status') != 'OK':
            # Route not available (e.g., no transit connection)
            return 'N/A'
        
        # Get duration in seconds and convert to minutes
        duration_seconds = element.get('duration', {}).get('value')
        if duration_seconds:
            return round(duration_seconds / 60)
        
        return 'N/A'
        
    except requests.exceptions.RequestException as e:
        print(f"      ⚠️  Request error for {mode}: {e}")
        return 'N/A'
    except Exception as e:
        print(f"      ⚠️  Error calculating {mode} distance: {e}")
        return 'N/A'


def calculate_all_distances(property_data: dict) -> dict:
    """
    Calculate walking, biking, and transit distances to nearest station
    Only calculates modes that are relevant for the city
    Only calculates if distances are not already set
    
    Args:
        property_data: Dict with property information including city and address
    
    Returns:
        Dict with distance fields added/updated
    """
    # Skip if no Google Maps API key
    if not GOOGLE_MAPS_API_KEY:
        return property_data
    
    # Check if already calculated
    if (property_data.get('distance_station_walk') is not None or
        property_data.get('distance_station_bike') is not None or
        property_data.get('distance_station_transit') is not None):
        return property_data
    
    city = property_data.get('city')
    station_config = get_station_for_city(city)
    
    if not station_config:
        # City not in our station map - skip
        return property_data
    
    station_address = station_config['station']
    
    # Build full property address
    parts = []
    if property_data.get('title'):
        parts.append(property_data['title'])
    if property_data.get('postcode'):
        parts.append(property_data['postcode'])
    if city:
        parts.append(city)
    
    property_address = ', '.join(parts)
    
    if not property_address:
        return property_data
    
    print(f"      🗺️  Calculating distances to {station_address}...")
    
    # Initialize all distance fields
    property_data['nearest_station_name'] = station_address.split(',')[0]
    property_data['distance_station_walk'] = None
    property_data['distance_station_bike'] = None
    property_data['distance_station_transit'] = None
    
    # Calculate only the modes we care about for this city
    modes_to_calculate = station_config.get('modes', [])
    
    for mode in modes_to_calculate:
        # Map our mode names to Google Maps API mode names
        api_mode = 'bicycling' if mode == 'bike' else mode
        
        time_value = calculate_distance_to_station(property_address, station_address, api_mode)
        property_data[f'distance_station_{mode}'] = time_value
        
        time.sleep(0.2)  # Small delay to avoid rate limiting
    
    # Log results
    results = []
    if 'walk' in modes_to_calculate:
        results.append(f"Walk: {property_data['distance_station_walk']}min")
    if 'bike' in modes_to_calculate:
        results.append(f"Bike: {property_data['distance_station_bike']}min")
    if 'transit' in modes_to_calculate:
        results.append(f"Transit: {property_data['distance_station_transit']}min")
    
    print(f"      ✅ {' | '.join(results)}")
    
    return property_data


def estimate_api_calls(num_new_properties: int) -> dict:
    """
    Estimate Google Maps API calls for a set of properties
    
    Args:
        num_new_properties: Number of new properties without distance data
        
    Returns:
        Dict with call estimates and cost info
    """
    # Average modes per property (most cities use 1-2 modes)
    avg_modes_per_property = 1.5
    
    estimated_calls = int(num_new_properties * avg_modes_per_property)
    
    # Google Maps pricing (as of 2024)
    free_tier = 40000  # per month
    cost_per_call = 0.005  # $0.005 per call after free tier
    
    monthly_calls = estimated_calls * 30  # if run daily
    
    return {
        'calls_per_run': estimated_calls,
        'calls_per_month': monthly_calls,
        'within_free_tier': monthly_calls < free_tier,
        'estimated_monthly_cost': max(0, (monthly_calls - free_tier) * cost_per_call)
    }