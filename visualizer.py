import folium
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Circle
from typing import List, Tuple
import numpy as np

class DroneVisualizer:
    def __init__(self, drone_system):
        self.system = drone_system
        self.map = None
        
    def create_map(self, center_lat: float, center_lng: float, zoom_start: int = 12):
        """Create interactive map using folium"""
        self.map = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_start)
        
    def add_locations_to_map(self):
        """Add all locations to the map"""
        for node in self.system.graph.nodes:
            pos = self.system.graph.nodes[node]['pos']
            point = self.system.graph.nodes[node]['point']
            
            # Choose icon based on node type
            if node in self.system.charging_stations:
                icon = folium.Icon(color='green', icon='bolt', prefix='fa')
                popup = f"<b>{node}</b><br>⚡ Charging Station"
            else:
                icon = folium.Icon(color='blue', icon='circle', prefix='fa')
                popup = f"<b>{node}</b><br>📍 Delivery Point"
                
            folium.Marker(
                [pos[0], pos[1]],
                popup=popup,
                icon=icon,
                tooltip=node
            ).add_to(self.map)
            
    def add_no_fly_zones_to_map(self):
        """Add no-fly zones to the map"""
        for zone in self.system.no_fly_zones:
            folium.Circle(
                radius=zone.radius * 1000,  # Convert to meters
                location=[zone.center.lat, zone.center.lng],
                popup=f"🚫 {zone.name}",
                color='red',
                fill=True,
                fill_opacity=0.3
            ).add_to(self.map)
            
    def add_route_to_map(self, path: List[str], color: str = 'blue'):
        """Add a route to the map"""
        route_coords = []
        for node in path:
            pos = self.system.graph.nodes[node]['pos']
            route_coords.append([pos[0], pos[1]])
            
        folium.PolyLine(
            route_coords,
            color=color,
            weight=3,
            opacity=0.8,
            popup=f"Route: {len(path)} stops"
        ).add_to(self.map)
        
        # Add markers for start and end
        start_pos = self.system.graph.nodes[path[0]]['pos']
        end_pos = self.system.graph.nodes[path[-1]]['pos']
        
        folium.Marker(
            [start_pos[0], start_pos[1]],
            popup="🚁 Start",
            icon=folium.Icon(color='green', icon='play', prefix='fa')
        ).add_to(self.map)
        
        folium.Marker(
            [end_pos[0], end_pos[1]],
            popup="🎯 Destination",
            icon=folium.Icon(color='red', icon='flag-checkered', prefix='fa')
        ).add_to(self.map)
        
    def save_map(self, filename: str = 'drone_delivery_map.html'):
        """Save the map to HTML file"""
        if self.map:
            self.map.save(filename)
            print(f"Map saved as {filename}")
            
    def plot_network_graph(self, highlight_path: List[str] = None, title: str = "Drone Delivery Network"):
        """Create a matplotlib visualization of the network"""
        plt.figure(figsize=(12, 8))
        
        # Create position dictionary
        pos = {node: self.system.graph.nodes[node]['pos'] 
               for node in self.system.graph.nodes}
        
        # Draw the main graph
        nx.draw_networkx_nodes(self.system.graph, pos, 
                              node_color='lightblue', 
                              node_size=500,
                              alpha=0.7)
        
        # Draw charging stations differently
        charging_nodes = [n for n in self.system.graph.nodes if n in self.system.charging_stations]
        nx.draw_networkx_nodes(self.system.graph, pos,
                              nodelist=charging_nodes,
                              node_color='lightgreen',
                              node_size=600,
                              alpha=0.9)
        
        # Draw edges
        nx.draw_networkx_edges(self.system.graph, pos,
                              edge_color='gray',
                              width=1,
                              alpha=0.5)
        
        # Highlight specific path if provided
        if highlight_path:
            path_edges = list(zip(highlight_path, highlight_path[1:]))
            nx.draw_networkx_edges(self.system.graph, pos,
                                  edgelist=path_edges,
                                  edge_color='red',
                                  width=3,
                                  alpha=1)
        
        # Add labels
        nx.draw_networkx_labels(self.system.graph, pos, font_size=10, font_weight='bold')
        
        # Add no-fly zones
        ax = plt.gca()
        for zone in self.system.no_fly_zones:
            circle = Circle((zone.center.lat, zone.center.lng), 
                          zone.radius * 5,  # Scaled for visualization
                          fill=True, 
                          alpha=0.2, 
                          color='red')
            ax.add_patch(circle)
            plt.text(zone.center.lat, zone.center.lng, f"🚫 {zone.name}", 
                    fontsize=8, ha='center')
        
        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel("Latitude", fontsize=12)
        plt.ylabel("Longitude", fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return plt.gcf()
        
    def plot_cost_comparison(self, routes_data: List[Tuple[str, float]]):
        """Plot cost comparison between different routes"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        route_names = [f"Route {i+1}" for i in range(len(routes_data))]
        costs = [data[1] for data in routes_data]
        
        bars = ax.bar(route_names, costs, color=['blue', 'green', 'orange', 'red', 'purple'])
        ax.set_ylabel('Total Cost (distance × weather)', fontsize=12)
        ax.set_title('Route Cost Comparison', fontsize=14, fontweight='bold')
        
        # Add value labels on bars
        for bar, cost in zip(bars, costs):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{cost:.2f}', ha='center', va='bottom')
        
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig
        
    def create_route_animation_data(self, path: List[str]):
        """Prepare data for route animation"""
        positions = []
        for node in path:
            pos = self.system.graph.nodes[node]['pos']
            positions.append((pos[0], pos[1]))
        return positions