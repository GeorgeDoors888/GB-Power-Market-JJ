#!/usr/bin/env python3
"""
Add CVA Plants Layer to Map

This script updates the dno_energy_map_advanced.html file to include CVA plants
as a separate layer with distinct styling from SVA generators.

CVA (Central Volume Allocation) plants:
- Large transmission-connected power stations
- Nuclear, major CCGT, offshore wind
- Triangle markers (vs circles for SVA)
- Black border for distinction
- Larger sizes reflecting bigger capacities

Created: 2025
"""

def update_map_html():
    """Add CVA layer functionality to map HTML"""
    
    map_file = 'dno_energy_map_advanced.html'
    
    with open(map_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 1. Add CVA button after Generation button
    button_section = '''                <div class="button-group">
                    <button onclick="showGenerationSites()" id="btn-generation">Generation</button>
                    <button onclick="showDemandHeatmap()" id="btn-demand">Demand</button>'''
    
    button_replacement = '''                <div class="button-group">
                    <button onclick="showGenerationSites()" id="btn-generation">SVA Generation</button>
                    <button onclick="showCVAPlants()" id="btn-cva">CVA Plants</button>
                    <button onclick="showDemandHeatmap()" id="btn-demand">Demand</button>'''
    
    if button_section in html_content:
        html_content = html_content.replace(button_section, button_replacement)
        print("✅ Updated button section")
    else:
        print("⚠️  Could not find button section - manual update needed")
    
    # 2. Add CVA function after showGenerationSites function
    # Find the end of showGenerationSites function
    generation_function_end = "        }  // End of showGenerationSites"
    
    cva_function = '''
        
        // ==================== CVA PLANTS ====================
        // Load and display CVA (Central Volume Allocation) plants
        // These are transmission-connected power stations (nuclear, major CCGT, offshore wind)
        function showCVAPlants() {
            updateInfo('Loading CVA plants from electricityproduction.uk data...');
            toggleButton('btn-cva');
            
            // Check if file exists
            fetch('cva_plants_map.json')
                .then(response => {
                    console.log('📥 Fetch CVA plants response:', response.status);
                    if (!response.ok) {
                        throw new Error('CVA plants JSON file not found. Please run generate_cva_map_json.py after scraping completes.');
                    }
                    return response.json();
                })
                .then(cvaPlants => {
                    console.log(`✅ Loaded ${cvaPlants.length} CVA plants`);
                    
                    // Count by type
                    const typeCounts = {};
                    const typeCapacity = {};
                    
                    // Clear any existing CVA markers
                    if (window.cvaMarkers) {
                        window.cvaMarkers.forEach(m => m.setMap(null));
                    }
                    window.cvaMarkers = [];
                    
                    // Create markers for each CVA plant
                    cvaPlants.forEach(plant => {
                        // Track statistics
                        const type = plant.type_category || 'Other';
                        typeCounts[type] = (typeCounts[type] || 0) + 1;
                        typeCapacity[type] = (typeCapacity[type] || 0) + (plant.capacity || 0);
                        
                        // Get color based on fuel type
                        const color = getCVAColor(plant.type_category);
                        
                        // Calculate marker size based on capacity
                        // CVA plants are typically larger, so use larger base size
                        const capacity = plant.capacity || 0;
                        let scale;
                        if (capacity >= 1000) scale = 12;  // Gigawatt scale
                        else if (capacity >= 500) scale = 10;
                        else if (capacity >= 200) scale = 8;
                        else if (capacity >= 100) scale = 6;
                        else if (capacity >= 50) scale = 5;
                        else scale = 4;
                        
                        // Create triangle marker for CVA (vs circle for SVA)
                        const marker = new google.maps.Marker({
                            position: { lat: plant.lat, lng: plant.lng },
                            map: map,
                            icon: {
                                path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,  // Triangle
                                scale: scale,
                                fillColor: color,
                                fillOpacity: 0.85,
                                strokeColor: '#000000',  // Black border to distinguish from SVA
                                strokeWeight: 2,
                                rotation: 0  // Point up
                            },
                            title: `${plant.name} (CVA - ${plant.capacity ? plant.capacity.toFixed(1) : 'N/A'} MW)`,
                            zIndex: 1000  // Above SVA generators
                        });
                        
                        // Info window with CVA-specific data
                        marker.addListener('click', () => {
                            const content = `
                                <div style="font-family: Arial, sans-serif; min-width: 200px;">
                                    <h3 style="margin: 0 0 10px 0; color: #1a73e8;">${plant.name}</h3>
                                    <table style="width: 100%; border-collapse: collapse;">
                                        <tr><td style="padding: 4px 8px 4px 0;"><strong>Type:</strong></td><td style="padding: 4px 0;">CVA (Transmission)</td></tr>
                                        <tr><td style="padding: 4px 8px 4px 0;"><strong>Capacity:</strong></td><td style="padding: 4px 0;">${plant.capacity ? plant.capacity.toFixed(1) + ' MW' : 'Unknown'}</td></tr>
                                        <tr><td style="padding: 4px 8px 4px 0;"><strong>Fuel:</strong></td><td style="padding: 4px 0;">${plant.fuel_type || 'Unknown'}</td></tr>
                                        <tr><td style="padding: 4px 8px 4px 0;"><strong>Category:</strong></td><td style="padding: 4px 0;">${plant.type_category || 'Other'}</td></tr>
                                        ${plant.status ? `<tr><td style="padding: 4px 8px 4px 0;"><strong>Status:</strong></td><td style="padding: 4px 0;">${plant.status}</td></tr>` : ''}
                                        ${plant.operator ? `<tr><td style="padding: 4px 8px 4px 0;"><strong>Operator:</strong></td><td style="padding: 4px 0;">${plant.operator}</td></tr>` : ''}
                                        <tr><td style="padding: 4px 8px 4px 0;"><strong>Location:</strong></td><td style="padding: 4px 0;">${plant.lat.toFixed(4)}, ${plant.lng.toFixed(4)}</td></tr>
                                    </table>
                                    ${plant.url ? `<p style="margin: 10px 0 0 0;"><a href="${plant.url}" target="_blank" style="color: #1a73e8;">View Details →</a></p>` : ''}
                                </div>
                            `;
                            infoWindow.setContent(content);
                            infoWindow.open(map, marker);
                        });
                        
                        window.cvaMarkers.push(marker);
                    });
                    
                    // Calculate total capacity
                    const totalCapacity = cvaPlants.reduce((sum, p) => sum + (p.capacity || 0), 0);
                    
                    // Build breakdown text
                    let breakdown = '<strong>Breakdown by Type:</strong><br>';
                    const sortedTypes = Object.keys(typeCounts).sort((a, b) => typeCapacity[b] - typeCapacity[a]);
                    sortedTypes.forEach(type => {
                        const pct = ((typeCapacity[type] / totalCapacity) * 100).toFixed(1);
                        breakdown += `${type}: ${typeCounts[type]} plants, ${typeCapacity[type].toFixed(0)} MW (${pct}%)<br>`;
                    });
                    
                    updateInfo(`✅ Loaded ${cvaPlants.length} CVA plants (${totalCapacity.toFixed(0)} MW total)<br>${breakdown}`);
                    
                    console.log('📊 CVA Plants by type:', typeCounts);
                    console.log('📊 CVA Capacity by type (MW):', typeCapacity);
                })
                .catch(error => {
                    console.error('❌ Error loading CVA plants:', error);
                    updateInfo('❌ CVA plants not available yet. Please complete web scraping first.<br>' +
                              'Run: python scrape_plants_optimized.py<br>' +
                              'Then: python generate_cva_map_json.py');
                });
        }  // End of showCVAPlants
        
        // Get color for CVA plant based on type
        function getCVAColor(typeCategory) {
            const colors = {
                'Wind': '#4CAF50',          // Green
                'Solar': '#FFC107',         // Amber
                'Gas': '#FF5722',           // Deep orange
                'Nuclear': '#9C27B0',       // Purple
                'Hydro': '#2196F3',         // Blue
                'Biomass': '#795548',       // Brown
                'Coal': '#424242',          // Dark grey
                'Storage': '#00BCD4',       // Cyan
                'Oil': '#E91E63',           // Pink
                'Other': '#9E9E9E'          // Grey
            };
            return colors[typeCategory] || colors['Other'];
        }
'''
    
    if generation_function_end in html_content:
        html_content = html_content.replace(generation_function_end, generation_function_end + cva_function)
        print("✅ Added CVA function")
    else:
        print("⚠️  Could not find generation function end - manual update needed")
        print("   Looking for:", generation_function_end)
    
    # 3. Write updated content
    with open(map_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ Map updated successfully: {map_file}")
    print("\n📋 Next steps:")
    print("   1. Wait for scraping to complete (scrape_plants_optimized.py)")
    print("   2. Run: python generate_cva_map_json.py")
    print("   3. Open map in browser to test CVA layer")

if __name__ == '__main__':
    update_map_html()
