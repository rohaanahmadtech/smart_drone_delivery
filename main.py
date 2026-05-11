import sys
import os
from drone_system import SmartDroneSystem, Point, WeatherCondition, NoFlyZone
from visualizer import DroneVisualizer
import networkx as nx
import matplotlib
matplotlib.use('TkAgg')  # Force TkAgg backend for better display
import matplotlib.pyplot as plt

def create_sample_scenario():
    """Create a realistic sample scenario for demonstration"""
    drone_system = SmartDroneSystem()
    
    # Create delivery points (warehouse and customers)
    warehouse = Point(40.7128, -74.0060, "Warehouse")
    customer1 = Point(40.7150, -74.0080, "Customer_A")
    customer2 = Point(40.7180, -74.0120, "Customer_B")
    customer3 = Point(40.7100, -74.0000, "Customer_C")
    customer4 = Point(40.7200, -74.0040, "Customer_D")
    hospital = Point(40.7140, -74.0100, "Hospital_Supply")
    
    # Add all locations
    drone_system.add_location(warehouse, is_charging_station=True)
    drone_system.add_location(customer1)
    drone_system.add_location(customer2)
    drone_system.add_location(customer3)
    drone_system.add_location(customer4)
    drone_system.add_location(hospital)
    
    # Add additional charging station
    charging_station = Point(40.7160, -74.0050, "Charging_Station_1")
    drone_system.add_location(charging_station, is_charging_station=True)
    
    # Create routes (graph edges)
    points = [warehouse, customer1, customer2, customer3, customer4, hospital, charging_station]
    
    # Add all possible connections (simplified real-world connections)
    connections = [
        (warehouse, customer1), (warehouse, customer3), (warehouse, charging_station),
        (customer1, customer2), (customer1, hospital), (customer2, customer4),
        (customer3, customer4), (customer3, hospital), (customer4, charging_station),
        (hospital, charging_station), (customer2, charging_station)
    ]
    
    for from_point, to_point in connections:
        drone_system.add_route(from_point, to_point)
    
    # Add weather conditions
    drone_system.set_weather(customer2, WeatherCondition.LIGHT_RAIN)
    drone_system.set_weather(customer4, WeatherCondition.WINDY)
    
    # Add no-fly zones
    park = NoFlyZone(Point(40.7130, -74.0070, "Central_Park"), 0.2, "Central Park - No Fly Zone")
    stadium = NoFlyZone(Point(40.7170, -74.0030, "Stadium"), 0.15, "Stadium Event Zone")
    drone_system.add_no_fly_zone(park)
    drone_system.add_no_fly_zone(stadium)
    
    return drone_system

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_section(title):
    """Print section header"""
    print(f"\n▶ {title}")
    print("-"*40)

def show_plot(fig, title):
    """Helper function to show plots with proper handling"""
    fig.canvas.manager.set_window_title(title)
    fig.tight_layout()
    plt.figure(fig.number)  # Make it current
    plt.show(block=False)
    plt.pause(0.5)  # Allow GUI to update

def main():
    print_header("🚁 SMART DRONE DELIVERY SYSTEM")
    print("Initializing system...")
    
    # Create and setup the drone system
    drone_system = create_sample_scenario()
    visualizer = DroneVisualizer(drone_system)
    
    # Display system information
    print_section("System Information")
    print(f"📍 Total nodes: {drone_system.graph.number_of_nodes()}")
    print(f"🔗 Total connections: {drone_system.graph.number_of_edges()}")
    print(f"⚡ Charging stations: {len(drone_system.charging_stations)}")
    print(f"🚫 No-fly zones: {len(drone_system.no_fly_zones)}")
    print(f"🌤️ Weather-affected routes: {len([w for w in drone_system.weather_conditions])}")
    
    # Create a list to store all figures
    figures = []
    
    # 1. Dijkstra - Shortest Path
    print_section("1. DIJKSTRA - Shortest Path")
    start = "Warehouse"
    end = "Customer_D"
    print(f"Finding shortest path from {start} to {end}...")
    
    path, cost = drone_system.find_shortest_path(start, end)
    if path:
        print(f"✅ Optimal route found!")
        print(f"   Path: {' → '.join(path)}")
        print(f"   Total cost: {cost:.3f}")
        
        details = drone_system.get_route_details(path)
        print(f"   Total distance: {details['total_distance']:.3f} units")
        print(f"   Stops: {details['num_stops']}")
        
        # Visualize the path
        print("   📊 Generating shortest path visualization...")
        fig1 = visualizer.plot_network_graph(highlight_path=path, 
                                             title=f"Shortest Path: {start} → {end}")
        figures.append(fig1)
        show_plot(fig1, "Shortest Path Visualization")
    else:
        print("❌ No path found!")
    
    # 2. MST - Network Optimization
    print_section("2. MINIMUM SPANNING TREE - Network Optimization")
    mst_edges = drone_system.optimize_delivery_network()
    print(f"✅ Optimal network uses {len(mst_edges)} connections:")
    for edge in list(mst_edges)[:5]:  # Show first 5
        print(f"   • {edge[0]} ↔ {edge[1]}")
    if len(mst_edges) > 5:
        print(f"   ... and {len(mst_edges)-5} more")
    
    print("   📊 Generating MST visualization...")
    fig2 = visualizer.plot_network_graph(title="Optimal Delivery Network (MST)")
    figures.append(fig2)
    show_plot(fig2, "MST Network Optimization")
    
    # 3. DFS/BFS - Area Exploration
    print_section("3. DFS/BFS - Area Exploration")
    start_point = "Warehouse"
    
    print(f"DFS Exploration from {start_point}:")
    dfs_path = drone_system.explore_area(start_point, method='dfs')
    print(f"   → {' → '.join(dfs_path[:5])}..." if len(dfs_path) > 5 else f"   → {' → '.join(dfs_path)}")
    
    print(f"BFS Exploration from {start_point}:")
    bfs_path = drone_system.explore_area(start_point, method='bfs')
    print(f"   → {' → '.join(bfs_path[:5])}..." if len(bfs_path) > 5 else f"   → {' → '.join(bfs_path)}")
    
    # 4. Charging Station Finder
    print_section("4. BATTERY MANAGEMENT - Nearest Charging Station")
    current_pos = "Customer_B"
    path_to_charge, cost_to_charge = drone_system.find_charging_station_path(current_pos)
    
    if path_to_charge:
        print(f"⚠️ Low battery at {current_pos}!")
        print(f"🔋 Nearest charging station: {path_to_charge[-1]}")
        print(f"   Path: {' → '.join(path_to_charge)}")
        print(f"   Distance: {cost_to_charge:.3f} units")
    else:
        print(f"❌ No charging station reachable from {current_pos}")
    
    # 5. Multiple Routes Comparison
    print_section("5. ROUTE COMPARISON ANALYSIS")
    destinations = ["Customer_A", "Customer_B", "Customer_C", "Customer_D", "Hospital_Supply"]
    routes_data = []
    
    for dest in destinations:
        path, cost = drone_system.find_shortest_path("Warehouse", dest)
        if path:
            routes_data.append((dest, cost))
            print(f"   Warehouse → {dest}: {cost:.3f} (via {' → '.join(path)})")
    
    if routes_data:
        print("   📊 Generating route comparison chart...")
        fig3 = visualizer.plot_cost_comparison(routes_data)
        figures.append(fig3)
        show_plot(fig3, "Route Cost Comparison")
    
    # 6. Interactive Map
    print_section("6. INTERACTIVE VISUALIZATION")
    print("Generating interactive map with folium...")
    
    # Calculate map center
    all_positions = [drone_system.graph.nodes[node]['pos'] for node in drone_system.graph.nodes]
    center_lat = sum(p[0] for p in all_positions) / len(all_positions)
    center_lng = sum(p[1] for p in all_positions) / len(all_positions)
    
    visualizer.create_map(center_lat, center_lng, zoom_start=14)
    visualizer.add_locations_to_map()
    visualizer.add_no_fly_zones_to_map()
    
    # Add some example routes to map
    for dest in destinations[:3]:
        path, _ = drone_system.find_shortest_path("Warehouse", dest)
        if path:
            visualizer.add_route_to_map(path)
    
    map_file = "drone_delivery_map.html"
    visualizer.save_map(map_file)
    print(f"✅ Interactive map saved as '{map_file}'")
    
    # Try to open the map in browser
    import webbrowser
    if os.path.exists(map_file):
        webbrowser.open(f'file://{os.path.abspath(map_file)}')
        print("   🌐 Map opened in your default browser")
    
    # 7. Route Statistics
    print_section("📊 SYSTEM STATISTICS")
    
    # Calculate all shortest paths from warehouse
    path_costs = []
    for node in drone_system.graph.nodes:
        if node != "Warehouse":
            _, cost = drone_system.find_shortest_path("Warehouse", node)
            if cost != float('inf'):
                path_costs.append(cost)
    
    if path_costs:
        print(f"📈 Average delivery cost: {sum(path_costs)/len(path_costs):.3f}")
        print(f"🔝 Maximum delivery cost: {max(path_costs):.3f}")
        print(f"📉 Minimum delivery cost: {min(path_costs):.3f}")
    
    # Weather impact analysis
    weather_affected = 0
    for u, v, data in drone_system.graph.edges(data=True):
        if data['weather_factor'] > 1.0:
            weather_affected += 1
    
    total_edges = drone_system.graph.number_of_edges()
    print(f"🌧️ Weather-affected routes: {weather_affected}/{total_edges} ({weather_affected/total_edges*100:.1f}%)")
    
    # Connectivity check
    print(f"🔗 Network is {'✓' if nx.is_connected(drone_system.graph) else '✗'} fully connected")
    
    print_section("🎯 DEMONSTRATION COMPLETE")
    print("✅ All algorithms implemented and visualized")
    print(f"✅ {len(figures)} visualization windows should be open")
    print("✅ Interactive map saved - check your browser")
    print("\n💡 TIP: Close the plot windows to exit the program")
    
    # Keep the program running until user closes all figures
    try:
        plt.show(block=True)
    except:
        pass
    
    return drone_system, visualizer

if __name__ == "__main__":
    try:
        # Run the main program
        drone_system, visualizer = main()
        
    except KeyboardInterrupt:
        print("\n\n👋 System shutdown by user")
        plt.close('all')
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n📌 Troubleshooting:")
        print("1. Make sure all packages are installed: pip install -r requirements.txt")
        print("2. Try running: python -m pip install --upgrade matplotlib")
        print("3. Check if you have a GUI backend available")
        sys.exit(1)