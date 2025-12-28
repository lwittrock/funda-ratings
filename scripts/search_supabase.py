#!/usr/bin/env python3
"""
Funda Search Script with Supabase Integration
Searches for properties and saves to Supabase
"""

import json
import os
from datetime import datetime
from pathlib import Path
from funda import Funda
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
    print("   Set them in your terminal:")
    print("   export SUPABASE_URL='https://xxxxx.supabase.co'")
    print("   export SUPABASE_KEY='your-anon-key'")
    exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def load_config():
    """Load search configuration"""
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path, 'r') as f:
        return json.load(f)


def load_existing_properties():
    """Load existing properties from Supabase"""
    try:
        response = supabase.table('properties').select('*').execute()
        # Convert list to dict keyed by id
        return {prop['id']: prop for prop in response.data}
    except Exception as e:
        print(f"⚠️  Warning: Could not load existing properties: {e}")
        return {}


def upsert_property(property_data):
    """Insert or update a property in Supabase"""
    try:
        supabase.table('properties').upsert(property_data).execute()
    except Exception as e:
        print(f"   ❌ Failed to upsert property {property_data['id']}: {e}")
        raise


def normalize_name(name):
    """Normalize names for comparison"""
    return name.lower().replace(' ', '').replace('-', '')


def extract_property_data(listing):
    """Extract relevant data from Funda listing"""
    # Get photo URLs - handle different possible structures
    photo_urls = listing.get('photo_urls', [])
    if not photo_urls:
        photos = listing.get('photos', [])
        if photos and isinstance(photos, list):
            photo_urls = photos
    
    thumbnail_url = photo_urls[0] if photo_urls else None
    
    # Get URL - try different keys, prioritize the direct url field
    funda_url = listing.get('url') or listing.get('share_url') or listing.get('funda_url')
    
    # If no URL found, try to construct it
    if not funda_url:
        object_type = listing.get('object_type', 'huis').lower()
        if object_type == 'house':
            object_type = 'huis'
        elif object_type == 'apartment':
            object_type = 'appartement'
        
        city = listing.get('city', '').lower()
        title_slug = listing.get('title', '').lower().replace(' ', '-')
        property_id = listing.get('global_id') or listing.get('tiny_id')
        
        funda_url = f"https://www.funda.nl/detail/koop/{city}/{object_type}-{title_slug}/{property_id}/"
    
    # Helper function to extract integer from string like "148 m²"
    def extract_int(value):
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            # Extract first number from string
            import re
            match = re.search(r'\d+', value)
            return int(match.group()) if match else None
        return None
    
    return {
        'id': str(listing.get('global_id') or listing.get('tiny_id')),
        'title': listing.get('title'),
        'city': listing.get('city'),
        'neighbourhood': listing.get('neighbourhood'),
        'postcode': listing.get('postcode'),
        'province': listing.get('province'),
        'price': extract_int(listing.get('price')),
        'living_area': extract_int(listing.get('living_area')),
        'plot_area': extract_int(listing.get('plot_area')),
        'bedrooms': extract_int(listing.get('bedrooms')),
        'rooms': extract_int(listing.get('rooms')),
        'construction_year': extract_int(listing.get('construction_year')),
        'energy_label': listing.get('energy_label'),
        'object_type': listing.get('object_type'),
        'house_type': listing.get('house_type'),
        'features': {
            'has_garden': listing.get('has_garden', False),
            'has_balcony': listing.get('has_balcony', False),
            'has_roof_terrace': listing.get('has_roof_terrace', False),
            'has_solar_panels': listing.get('has_solar_panels', False),
            'has_heat_pump': listing.get('has_heat_pump', False),
            'has_parking': listing.get('has_parking_on_site', False),
        },
        'thumbnail_url': thumbnail_url,
        'funda_url': funda_url,
    }

def search_properties():
    """Main search function"""
    print("="*80)
    print("🏠 FUNDA PROPERTY SEARCH (Supabase)")
    print("="*80)
    
    # Load configuration
    config = load_config()
    search_config = config['search']
    
    city = search_config['city']
    neighborhoods = search_config.get('neighborhoods')
    price_min = search_config.get('price_min')
    price_max = search_config.get('price_max')
    area_min = search_config.get('area_min')
    max_results = search_config.get('max_results', 50)
    
    print(f"\n🔍 Searching in {city.title()}...")
    if neighborhoods:
        print(f"   Neighborhoods: {', '.join([n.title() for n in neighborhoods])}")
    if price_min or price_max:
        print(f"   Price: €{price_min:,} - €{price_max:,}".replace(',', '.'))
    if area_min:
        print(f"   Min area: {area_min} m²")
    
    # Load existing properties from Supabase
    print("\n📊 Loading existing properties from Supabase...")
    existing_properties = load_existing_properties()
    existing_ids = set(existing_properties.keys())
    
    print(f"   Currently tracking {len(existing_properties)} properties")
    
    # Initialize Funda API
    f = Funda()
    
    # Search
    print("\n🔧 Running search...")
    try:
        results = f.search_listing(
            location=city,
            price_min=price_min,
            price_max=price_max,
            area_min=area_min,
        )
    except Exception as e:
        print(f"   ❌ Search error: {e}")
        print("\n   Trying alternative approach...")
        try:
            results = f.search_listing(
                location=city,
                price_min=price_min,
                price_max=price_max,
            )
            print(f"   Success without area filter: {len(results)} results")
            if area_min:
                results = [r for r in results if r.get('living_area', 0) >= area_min]
                print(f"   After manual area filter: {len(results)} results")
        except Exception as e2:
            print(f"   ❌ Alternative search also failed: {e2}")
            return
    
    print(f"   Found {len(results)} properties from API")
    
    # Filter by neighborhoods if specified
    if neighborhoods:
        normalized_neighborhoods = [normalize_name(n) for n in neighborhoods]
        filtered = []
        
        for listing in results:
            neighborhood = listing.get('neighbourhood', '')
            if neighborhood and normalize_name(neighborhood) in normalized_neighborhoods:
                filtered.append(listing)
        
        results = filtered
        print(f"   After neighborhood filter: {len(results)} properties")
    
    # Limit results
    results = results[:max_results]
    
    # Process results
    now = datetime.now().astimezone().isoformat()
    found_ids = set()
    new_count = 0
    updated_count = 0
    
    print(f"\n💾 Processing {len(results)} properties...")
    
    for idx, listing in enumerate(results, 1):
        try:
            global_id = listing.get('global_id') or listing.get('tiny_id')
            print(f"   [{idx}/{len(results)}] Processing {global_id}...")
            
            # Get detailed listing
            try:
                detailed_listing = f.get_listing(global_id)
                property_data = extract_property_data(detailed_listing)
            except Exception as e:
                print(f"      ⚠️  Using search result data: {e}")
                property_data = extract_property_data(listing)
            
            property_id = property_data['id']
            found_ids.add(property_id)
            
            # Debug first property
            if idx == 1:
                print(f"\n   ✅ Sample property:")
                print(f"      Title: {property_data['title']}")
                print(f"      URL: {property_data['funda_url']}")
            
            if property_id in existing_properties:
                # Update existing property
                old_data = existing_properties[property_id]
                property_data['added_date'] = old_data.get('added_date', now)
                property_data['last_seen'] = now
                property_data['status'] = 'active'
                
                # Track price changes
                price_history = old_data.get('price_history', [])
                if isinstance(price_history, str):
                    price_history = json.loads(price_history)
                
                if old_data.get('price') != property_data['price']:
                    price_history.append({
                        'price': old_data['price'],
                        'date': old_data.get('last_seen', old_data.get('added_date'))
                    })
                
                property_data['price_history'] = price_history
                updated_count += 1
            else:
                # New property
                property_data['added_date'] = now
                property_data['last_seen'] = now
                property_data['status'] = 'active'
                property_data['price_history'] = []
                new_count += 1
            
            # Upsert to Supabase
            upsert_property(property_data)
            
        except Exception as e:
            print(f"      ❌ Error processing property: {e}")
            continue
    
    # Mark removed properties
    print("\n🔍 Checking for removed properties...")
    removed_count = 0
    for property_id in existing_ids:
        if property_id not in found_ids:
            if existing_properties[property_id].get('status') == 'active':
                try:
                    supabase.table('properties').update({
                        'status': 'removed',
                        'removed_date': now
                    }).eq('id', property_id).execute()
                    removed_count += 1
                except Exception as e:
                    print(f"   ❌ Failed to mark {property_id} as removed: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("✅ SEARCH COMPLETE")
    print("="*80)
    print(f"   🆕 New properties: {new_count}")
    print(f"   🔄 Updated properties: {updated_count}")
    print(f"   ❌ Removed properties: {removed_count}")
    print(f"   📊 Total in database: {len(existing_properties) + new_count}")
    print(f"\n💾 Data saved to Supabase!")
    print(f"🌐 Your app will now load from the database\n")


if __name__ == "__main__":
    try:
        search_properties()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()