import json
import yaml
from pathlib import Path

def extract_endpoints_from_openapi():
    """Extract all endpoints from the OpenAPI specification and categorize them"""
    
    # Read the OpenAPI JSON file
    json_file_path = "/Users/georgemajor/Library/CloudStorage/GoogleDrive-george@upowerenergy.uk/Shared drives/Jibber Jabber Drive Google /VITUAL LEAD PARTY/elexon_api2.json"
    
    with open(json_file_path, 'r') as f:
        api_spec = json.load(f)
    
    base_url = api_spec['servers'][0]['url']
    paths = api_spec['paths']
    
    # Dictionary to store categorized endpoints
    categorized_endpoints = {}
    
    print(f"Found {len(paths)} endpoints in the API specification")
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() == 'get':  # Only GET endpoints for our smoke test
                tags = details.get('tags', ['uncategorized'])
                summary = details.get('summary', 'No description')
                
                # Clean up category name
                category = tags[0].lower().replace(' ', '_').replace('-', '_')
                
                if category not in categorized_endpoints:
                    categorized_endpoints[category] = {}
                
                # Create a clean endpoint name
                endpoint_name = path.split('/')[-1].upper()
                if endpoint_name == '':
                    endpoint_name = path.split('/')[-2].upper()
                
                # Make endpoint name unique within category
                original_name = endpoint_name
                counter = 1
                while endpoint_name in categorized_endpoints[category]:
                    endpoint_name = f"{original_name}_{counter}"
                    counter += 1
                
                categorized_endpoints[category][endpoint_name] = {
                    'url': f"{base_url}{path}",
                    'summary': summary,
                    'path': path
                }
    
    return categorized_endpoints

def create_comprehensive_config():
    """Create a comprehensive configuration file with all endpoints"""
    endpoints = extract_endpoints_from_openapi()
    
    # Create a comprehensive config file
    config_data = {}
    
    for category, category_endpoints in endpoints.items():
        config_data[category] = {}
        for name, details in category_endpoints.items():
            config_data[category][name] = details['url']
    
    # Save to YAML file
    with open('config:comprehensive_endpoints.yml', 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=True)
    
    print(f"Created comprehensive config with {len(config_data)} categories")
    for category, endpoints in config_data.items():
        print(f"  {category}: {len(endpoints)} endpoints")
    
    return config_data

def create_sample_config():
    """Create a smaller sample config for testing with key endpoints from each category"""
    endpoints = extract_endpoints_from_openapi()
    
    # Select 2-3 key endpoints from each major category
    sample_config = {}
    
    priority_categories = [
        'generation_forecast',
        'demand',
        'system',
        'generation_actual',
        'balancing_services',
        'datasets'
    ]
    
    for category in priority_categories:
        if category in endpoints:
            sample_config[category] = {}
            # Take first 3 endpoints from each category
            for i, (name, details) in enumerate(list(endpoints[category].items())[:3]):
                sample_config[category][name] = details['url']
    
    # Save sample config
    with open('config:sample_endpoints.yml', 'w') as f:
        yaml.dump(sample_config, f, default_flow_style=False, sort_keys=True)
    
    print(f"\nCreated sample config with {len(sample_config)} categories for testing")
    for category, category_endpoints in sample_config.items():
        print(f"  {category}: {len(category_endpoints)} endpoints")
    
    return sample_config

if __name__ == "__main__":
    print("Extracting endpoints from OpenAPI specification...")
    
    # Create both comprehensive and sample configs
    comprehensive = create_comprehensive_config()
    sample = create_sample_config()
    
    print("\nFiles created:")
    print("- config:comprehensive_endpoints.yml (all endpoints)")
    print("- config:sample_endpoints.yml (sample for testing)")
