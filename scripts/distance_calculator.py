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
            result = round(duration_seconds / 60)
            print(f"      🔍 API: {mode} took {duration_seconds}s = {duration_seconds/60:.1f}min → rounded to {result}min")
            return result
        
        return 'N/A'
        
    except requests.exceptions.RequestException as e:
        print(f"      ⚠️  Request error for {mode}: {e}")
        return 'N/A'
    except Exception as e:
        print(f"      ⚠️  Error calculating {mode} distance: {e}")
        return 'N/A'


def calculate_all_distances(property_data: dict) -> dict:
    """
    DEBUGGED VERSION - Calculate walking, biking, and transit distances to nearest station
    """
    print(f"      🔍 DEBUG START calculate_all_distances")
    print(f"      🔍 Input: city={property_data.get('city')}")
    
    # Skip if no Google Maps API key
    if not GOOGLE_MAPS_API_KEY:
        print(f"      🔍 DEBUG: No API key, returning")
        return property_data
    
    # Check if already calculated
    walk_dist = property_data.get('distance_station_walk')
    bike_dist = property_data.get('distance_station_bike')
    transit_dist = property_data.get('distance_station_transit')
    
    print(f"      🔍 DEBUG: Existing distances - walk={walk_dist}, bike={bike_dist}, transit={transit_dist}")
    
    if (walk_dist is not None or bike_dist is not None or transit_dist is not None):
        print(f"      🔍 DEBUG: Already calculated, returning")
        return property_data
    
    city = property_data.get('city')
    station_config = get_station_for_city(city)
    
    if not station_config:
        print(f"      🔍 DEBUG: No station config for {city}, returning")
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
    
    print(f"      🔍 DEBUG: Property address built: '{property_address}'")
    
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
    
    print(f"      🔍 DEBUG: Modes to calculate: {modes_to_calculate}")
    
    for mode in modes_to_calculate:
        print(f"      🔍 DEBUG: Starting mode '{mode}'")
        
        # Map our mode names to Google Maps API mode names
        mode_mapping = {
            'walk': 'walking',
            'bike': 'bicycling',
            'transit': 'transit'
        }
        api_mode = mode_mapping.get(mode, mode)
        
        print(f"      🔍 DEBUG: Calling calculate_distance_to_station('{property_address}', '{station_address}', '{api_mode}')")
        
        time_value = calculate_distance_to_station(property_address, station_address, api_mode)
        
        print(f"      🔍 DEBUG: Got time_value = {time_value} (type: {type(time_value)})")
        
        field_name = f'distance_station_{mode}'
        property_data[field_name] = time_value
        
        print(f"      🔍 DEBUG: Set property_data['{field_name}'] = {time_value}")
        print(f"      🔍 DEBUG: Verify property_data['{field_name}'] = {property_data[field_name]}")
        
        time.sleep(0.2)
    
    # Log results
    results = []
    if 'walk' in modes_to_calculate:
        val = property_data['distance_station_walk']
        print(f"      🔍 DEBUG: Reading walk distance: {val}")
        results.append(f"Walk: {val}min")
    if 'bike' in modes_to_calculate:
        val = property_data['distance_station_bike']
        print(f"      🔍 DEBUG: Reading bike distance: {val}")
        results.append(f"Bike: {val}min")
    if 'transit' in modes_to_calculate:
        val = property_data['distance_station_transit']
        print(f"      🔍 DEBUG: Reading transit distance: {val}")
        results.append(f"Transit: {val}min")
    
    print(f"      ✅ {' | '.join(results)}")
    
    print(f"      🔍 DEBUG END - returning property_data")
    
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