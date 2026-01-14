#!/usr/bin/env python3
"""
Funda Search Script with Supabase Integration
Optimized two-stage filtering:
1. Filter on basic search results (neighborhoods)
2. Fetch detailed listings only for those that pass
3. Filter on detailed data (garden, distance)
"""

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from funda import Funda
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our modules
from station_config import get_station_for_city
from distance_calculator import calculate_all_distances, estimate_api_calls, GOOGLE_MAPS_API_KEY

# Load environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
    exit(1)

if not GOOGLE_MAPS_API_KEY:
    print("⚠️  Warning: GOOGLE_MAPS_API_KEY not set - distance calculations will be skipped")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def load_search_configs():
    """Load active search configurations from Supabase"""
    try:
        response = supabase.table('search_configs').select('*').eq('active', True).execute()
        return response.data
    except Exception as e:
        print(f"❌ Error loading search configs: {e}")
        return []


def load_existing_properties():
    """Load existing properties from Supabase"""
    try:
        response = supabase.table('properties').select('*').execute()
        return {prop['funda_id']: prop for prop in response.data}
    except Exception as e:
        print(f"⚠️  Warning: Could not load existing properties: {e}")
        return {}


def upsert_property(property_data):
    """Insert or update a property in Supabase"""
    try:
        supabase.table('properties').upsert(property_data, on_conflict='funda_id').execute()
    except Exception as e:
        print(f"   ❌ Failed to upsert property {property_data.get('funda_id')}: {e}")
        raise


def normalize_name(name):
    """Normalize names for comparison"""
    return name.lower().replace(' ', '').replace('-', '')


def extract_int(value):
    """Extract integer from string like '148 m²' or return int/None"""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        # Handle common "not available" strings
        if value.lower() in ['na', 'n.v.t.', 'n.v.t', 'nvt', '']:
            return None
        match = re.search(r'\d+', value)
        return int(match.group()) if match else None
    return None


def get_listing_attr(listing, attr_name, default=None):
    """
    Safely get attribute from Listing object
    Listing objects store data in a 'data' dict attribute
    """
    # First try to get from the data dict
    if hasattr(listing, 'data') and isinstance(listing.data, dict):
        if attr_name in listing.data:
            return listing.data[attr_name]
    
    # Then try as direct attribute
    return getattr(listing, attr_name, default)


def extract_coordinates(listing):
    """Extract latitude and longitude from listing"""
    coords = get_listing_attr(listing, 'coordinates')
    if coords and isinstance(coords, (list, tuple)) and len(coords) == 2:
        return float(coords[0]), float(coords[1])
    
    lat = get_listing_attr(listing, 'latitude')
    lng = get_listing_attr(listing, 'longitude')
    
    if lat is not None and lng is not None:
        try:
            return float(lat), float(lng)
        except (ValueError, TypeError):
            pass
    
    return None, None


def extract_property_data(listing):
    """Extract ALL data from Funda listing and map to database schema"""
    
    # Get photo URLs
    photo_urls = get_listing_attr(listing, 'photo_urls', [])
    if not photo_urls:
        photos = get_listing_attr(listing, 'photos', [])
        if photos and isinstance(photos, list):
            # Photos might be IDs - just store them
            photo_urls = photos
    
    thumbnail_url = photo_urls[0] if photo_urls else None
    
    # Get URL
    funda_url = get_listing_attr(listing, 'url') or get_listing_attr(listing, 'share_url')
    
    # Construct URL if not found
    if not funda_url:
        object_type_slug = get_listing_attr(listing, 'object_type', 'huis').lower()
        if object_type_slug == 'house':
            object_type_slug = 'huis'
        elif object_type_slug == 'apartment':
            object_type_slug = 'appartement'
        
        city = get_listing_attr(listing, 'city', '').lower()
        title_slug = get_listing_attr(listing, 'title', '').lower().replace(' ', '-')
        property_id = get_listing_attr(listing, 'global_id') or get_listing_attr(listing, 'tiny_id')
        
        funda_url = f"https://www.funda.nl/detail/koop/{city}/{object_type_slug}-{title_slug}/{property_id}/"
    
    # Extract coordinates
    latitude, longitude = extract_coordinates(listing)
    
    # Extract all fields
    return {
        # Identifiers
        'funda_id': str(get_listing_attr(listing, 'global_id') or get_listing_attr(listing, 'tiny_id')),
        'tiny_id': str(get_listing_attr(listing, 'tiny_id')) if get_listing_attr(listing, 'tiny_id') else None,
        
        # Address
        'title': get_listing_attr(listing, 'title'),
        'city': get_listing_attr(listing, 'city'),
        'postcode': get_listing_attr(listing, 'postcode'),
        'province': get_listing_attr(listing, 'province'),
        'neighbourhood': get_listing_attr(listing, 'neighbourhood'),
        'municipality': get_listing_attr(listing, 'municipality'),
        'house_number': get_listing_attr(listing, 'house_number'),
        'house_number_ext': get_listing_attr(listing, 'house_number_ext'),
        
        # Coordinates
        'latitude': latitude,
        'longitude': longitude,
        
        # Price
        'price': extract_int(get_listing_attr(listing, 'price')),
        'price_formatted': get_listing_attr(listing, 'price_formatted'),
        
        # Property details
        'offering_type': get_listing_attr(listing, 'offering_type'),
        'object_type': get_listing_attr(listing, 'object_type'),
        'construction_type': get_listing_attr(listing, 'construction_type'),
        'house_type': get_listing_attr(listing, 'house_type'),
        'funda_status': get_listing_attr(listing, 'status'),
        
        # Measurements
        'living_area': extract_int(get_listing_attr(listing, 'living_area')),
        'plot_area': extract_int(get_listing_attr(listing, 'plot_area')),
        'bedrooms': extract_int(get_listing_attr(listing, 'bedrooms')),
        'rooms': extract_int(get_listing_attr(listing, 'rooms')),
        'construction_year': extract_int(get_listing_attr(listing, 'construction_year')),
        
        # Energy & Features
        'energy_label': get_listing_attr(listing, 'energy_label'),
        'has_garden': get_listing_attr(listing, 'has_garden', False),
        'has_balcony': get_listing_attr(listing, 'has_balcony', False),
        'has_solar_panels': get_listing_attr(listing, 'has_solar_panels', False),
        'has_heat_pump': get_listing_attr(listing, 'has_heat_pump', False),
        'has_roof_terrace': get_listing_attr(listing, 'has_roof_terrace', False),
        'has_parking_on_site': get_listing_attr(listing, 'has_parking_on_site', False),
        'has_parking_enclosed': get_listing_attr(listing, 'has_parking_enclosed', False),
        'is_energy_efficient': get_listing_attr(listing, 'is_energy_efficient', False),
        'is_monument': get_listing_attr(listing, 'is_monument', False),
        'is_fixer_upper': get_listing_attr(listing, 'is_fixer_upper', False),
        
        # Listing details
        'description': get_listing_attr(listing, 'description'),
        'highlight': get_listing_attr(listing, 'highlight'),
        'publication_date': get_listing_attr(listing, 'publication_date'),
        'open_house': get_listing_attr(listing, 'open_house', False),
        'is_auction': get_listing_attr(listing, 'is_auction', False),
        
        # URLs
        'url': funda_url,
        'share_url': get_listing_attr(listing, 'share_url'),
        'google_maps_url': get_listing_attr(listing, 'google_maps_url'),
        'brochure_url': get_listing_attr(listing, 'brochure_url'),
        'thumbnail_url': thumbnail_url,
        
        # Media (as JSON)
        'photos': photo_urls,
        'features_data': {},
        
        # Review fields (default for new properties)
        'review_status': 'new',
        'rating_location': None,
        'rating_quality': None,
        'rating_outside': None,
        'rating_value': None,
        'notes': None,
        
        # Distance fields (will be calculated separately)
        'nearest_station_name': None,
        'distance_station_walk': None,
        'distance_station_bike': None,
        'distance_station_transit': None,
    }


def parse_cities(city_input):
    """Parse city input - can be single city or comma-separated list"""
    if not city_input:
        return []
    
    if isinstance(city_input, list):
        return city_input
    
    cities = [c.strip().lower() for c in city_input.split(',')]
    return [c for c in cities if c]


def filter_by_neighborhood(listing, neighborhoods):
    """Check if listing passes neighborhood filter"""
    if not neighborhoods:
        return True
    
    neighborhood = get_listing_attr(listing, 'neighbourhood', '')
    normalized_neighborhoods = [normalize_name(n) for n in neighborhoods]
    
    if not neighborhood or normalize_name(neighborhood) not in normalized_neighborhoods:
        return False
    
    return True


def passes_distance_filter_from_config(property_data, config):
    """Check if property passes distance filter"""
    mode = config.get('max_distance_mode')
    max_minutes = config.get('max_distance_minutes')
    
    if not mode or max_minutes is None:
        return True
    
    distance_key = f'distance_station_{mode}'
    distance = property_data.get(distance_key)
    
    if distance is None or distance == 'N/A':
        return True
    
    if isinstance(distance, (int, float)) and distance > max_minutes:
        return False
    
    return True


def search_properties():
    """Main search function with two-stage filtering"""
    print("="*80)
    print("🏠 FUNDA PROPERTY SEARCH (Optimized)")
    print("="*80)
    
    print("\n📋 Loading search configurations from Supabase...")
    search_configs = load_search_configs()
    
    if not search_configs:
        print("❌ No active search configurations found!")
        return
    
    print(f"   Found {len(search_configs)} active configuration(s)")
    
    print("\n📊 Loading existing properties from Supabase...")
    existing_properties = load_existing_properties()
    print(f"   Currently tracking {len(existing_properties)} properties")
    
    f = Funda()
    
    total_new = 0
    total_updated = 0
    total_filtered_neighborhood = 0
    total_filtered_garden = 0
    total_filtered_distance = 0
    
    for idx, config in enumerate(search_configs, 1):
        city_input = config.get('city')
        cities = parse_cities(city_input)
        
        neighborhoods = config.get('neighborhoods', [])
        price_min = config.get('price_min')
        price_max = config.get('price_max')
        area_min = config.get('area_min')
        max_results = config.get('max_results', 50)
        require_garden = config.get('require_garden', False)
        distance_mode = config.get('max_distance_mode')
        distance_max = config.get('max_distance_minutes')
        
        print(f"\n{'='*80}")
        print(f"🔍 Search Config #{idx}: {', '.join([c.title() for c in cities])}")
        print(f"{'='*80}")
        
        if neighborhoods:
            print(f"   Neighborhoods: {', '.join([n.title() for n in neighborhoods])}")
        if price_min or price_max:
            print(f"   Price: €{price_min:,} - €{price_max:,}".replace(',', '.'))
        if area_min:
            print(f"   Min area: {area_min} m²")
        if require_garden:
            print(f"   Required: Garden")
        if distance_mode and distance_max:
            print(f"   Max distance: {distance_max}min by {distance_mode}")
        
        # STAGE 1: Basic search from Funda API
        print(f"\n📥 STAGE 1: Fetching basic listings from Funda...")
        all_results = []
        
        for city in cities:
            print(f"   Searching {city.title()}...", end='')
            
            for page_num in range(0, 5): 
                try:
                    page_results = f.search_listing(
                        location=city,
                        price_min=price_min,
                        price_max=price_max,
                        area_min=area_min,
                        offering_type='buy',
                        page=page_num
                    )
                    
                    if not page_results:
                        break
                        
                    all_results.extend(page_results)
                    
                    if len(page_results) < 15:
                        break
                        
                except Exception as e:
                    print(f" ⚠️  Error: {e}")
                    break
            
            city_count = len([r for r in all_results if get_listing_attr(r, 'city', '').lower() == city])
            print(f" {city_count} found")
        
        print(f"   Total from API: {len(all_results)} properties")
        
        # STAGE 2: Apply cheap filters (neighborhood)
        print(f"\n🔍 STAGE 2: Applying neighborhood filter...")
        passed_basic_filter = []
        filtered_neighborhood = 0
        
        for listing in all_results:
            if filter_by_neighborhood(listing, neighborhoods):
                passed_basic_filter.append(listing)
            else:
                filtered_neighborhood += 1
        
        total_filtered_neighborhood += filtered_neighborhood
        
        if filtered_neighborhood > 0:
            print(f"   ✅ Passed: {len(passed_basic_filter)}")
            print(f"   ❌ Filtered out: {filtered_neighborhood}")
        else:
            print(f"   ✅ All passed: {len(passed_basic_filter)}")
        
        # Limit before detailed fetching
        passed_basic_filter = passed_basic_filter[:max_results]
        
        if len(passed_basic_filter) == 0:
            print(f"   ⏭️  No properties to process, moving to next config...")
            continue
        
        # STAGE 3: Fetch detailed listings
        print(f"\n📥 STAGE 3: Fetching detailed listings ({len(passed_basic_filter)} properties)...")
        print(f"   ⏱️  This may take ~{len(passed_basic_filter) * 0.3:.0f} seconds...")
        
        new_count = 0
        updated_count = 0
        filtered_garden = 0
        filtered_distance = 0
        
        for prop_idx, listing in enumerate(passed_basic_filter, 1):
            try:
                global_id = get_listing_attr(listing, 'global_id') or get_listing_attr(listing, 'tiny_id')
                
                if prop_idx % 5 == 0 or prop_idx == 1:
                    print(f"   [{prop_idx}/{len(passed_basic_filter)}] Processing...")
                
                # Fetch detailed listing
                try:
                    detailed_listing = f.get_listing(global_id)
                    property_data = extract_property_data(detailed_listing)
                    time.sleep(0.3)  # Rate limiting
                except Exception as e:
                    print(f"      ⚠️  Could not get detailed listing: {e}")
                    property_data = extract_property_data(listing)
                
                # Show first property
                if prop_idx == 1:
                    print(f"\n   ✅ First property (detailed):")
                    print(f"      Title: {property_data['title']}")
                    print(f"      City: {property_data['city']}")
                    print(f"      Neighborhood: {property_data['neighbourhood']}")
                    print(f"      Garden: {property_data['has_garden']}")
                
                # STAGE 4: Apply garden filter
                if require_garden and not property_data.get('has_garden', False):
                    filtered_garden += 1
                    if filtered_garden <= 3:
                        print(f"      ⏭️  No garden: {property_data['title']}")
                    continue
                
                funda_id = property_data['funda_id']
                is_new = funda_id not in existing_properties
                
                if is_new:
                    new_count += 1
                else:
                    # Update existing - preserve user review data
                    old_data = existing_properties[funda_id]
                    property_data['review_status'] = old_data.get('review_status', 'new')
                    property_data['rating_location'] = old_data.get('rating_location')
                    property_data['rating_quality'] = old_data.get('rating_quality')
                    property_data['rating_outside'] = old_data.get('rating_outside')
                    property_data['rating_value'] = old_data.get('rating_value')
                    property_data['notes'] = old_data.get('notes')
                    property_data['id'] = old_data.get('id')
                    
                    # Preserve distance data if already calculated
                    if old_data.get('distance_station_walk') is not None:
                        property_data['nearest_station_name'] = old_data.get('nearest_station_name')
                        property_data['distance_station_walk'] = old_data.get('distance_station_walk')
                        property_data['distance_station_bike'] = old_data.get('distance_station_bike')
                        property_data['distance_station_transit'] = old_data.get('distance_station_transit')
                    
                    updated_count += 1
                
                # STAGE 5: Calculate distances
                if GOOGLE_MAPS_API_KEY:
                    property_data = calculate_all_distances(property_data)
                
                # STAGE 6: Apply distance filter (only for new properties)
                if is_new and not passes_distance_filter_from_config(property_data, config):
                    mode = config.get('max_distance_mode')
                    max_min = config.get('max_distance_minutes')
                    actual = property_data.get(f'distance_station_{mode}')
                    filtered_distance += 1
                    if filtered_distance <= 3:
                        print(f"      ⏭️  Too far: {actual}min by {mode} (max {max_min}min)")
                    continue
                
                # Save to database
                upsert_property(property_data)
                
            except Exception as e:
                print(f"      ❌ Error: {e}")
                continue
        
        total_new += new_count
        total_updated += updated_count
        total_filtered_garden += filtered_garden
        total_filtered_distance += filtered_distance
        
        print(f"\n   ✅ Config #{idx} complete:")
        print(f"      🆕 New: {new_count}")
        print(f"      🔄 Updated: {updated_count}")
        if filtered_garden > 0:
            print(f"      🚫 Filtered (no garden): {filtered_garden}")
        if filtered_distance > 0:
            print(f"      🚫 Filtered (too far): {filtered_distance}")
    
    # Summary
    print("\n" + "="*80)
    print("✅ ALL SEARCHES COMPLETE")
    print("="*80)
    print(f"\n📊 Filter Results:")
    print(f"   Neighborhood: {total_filtered_neighborhood} filtered")
    print(f"   Garden: {total_filtered_garden} filtered")
    print(f"   Distance: {total_filtered_distance} filtered")
    print(f"\n💾 Database Updates:")
    print(f"   🆕 New properties: {total_new}")
    print(f"   🔄 Updated properties: {total_updated}")
    print(f"   📊 Total in database: {len(existing_properties) + total_new}")
    
    print(f"\n💾 Data saved to Supabase!")
    print(f"🌐 Your app will now load from the database\n")


if __name__ == "__main__":
    try:
        search_properties()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()