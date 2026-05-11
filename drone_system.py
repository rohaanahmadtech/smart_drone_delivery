import networkx as nx
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set
from enum import Enum
import math

class WeatherCondition(Enum):
    CLEAR = 1.0
    LIGHT_RAIN = 1.3
    HEAVY_RAIN = 1.8
    WINDY = 1.5
    STORM = 2.5

@dataclass
class Point:
    lat: float
    lng: float
    name: str = ""
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate Euclidean distance (simplified for demo)"""
        return math.sqrt((self.lat - other.lat)**2 + (self.lng - other.lng)**2)

@dataclass
class NoFlyZone:
    center: Point
    radius: float  # in km
    name: str

class SmartDroneSystem:
    def __init__(self):
        self.graph = nx.Graph()
        self.weather_conditions = {}
        self.no_fly_zones = []
        self.charging_stations = set()
        
    def add_location(self, point: Point, is_charging_station: bool = False):
        """Add a location node to the graph"""
        self.graph.add_node(point.name, pos=(point.lat, point.lng), point=point)
        if is_charging_station:
            self.charging_stations.add(point.name)
            
    def add_route(self, from_point: Point, to_point: Point, base_cost: float = None):
        """Add a route between two points with calculated cost"""
        if base_cost is None:
            base_cost = from_point.distance_to(to_point)
            
        # Apply weather factor
        weather_factor = self._get_weather_factor(from_point, to_point)
        
        # Check if route crosses no-fly zone
        if self._crosses_no_fly_zone(from_point, to_point):
            return False  # Route blocked
            
        final_cost = base_cost * weather_factor
        self.graph.add_edge(from_point.name, to_point.name, weight=final_cost, 
                           distance=base_cost, weather_factor=weather_factor)
        return True
        
    def _get_weather_factor(self, from_point: Point, to_point: Point) -> float:
        """Get weather factor for the route"""
        # Average weather between two points
        midpoint = Point((from_point.lat + to_point.lat)/2, 
                        (from_point.lng + to_point.lng)/2)
        weather = self.weather_conditions.get(midpoint.name, WeatherCondition.CLEAR)
        return weather.value
        
    def _crosses_no_fly_zone(self, from_point: Point, to_point: Point) -> bool:
        """Check if route crosses any no-fly zone"""
        for zone in self.no_fly_zones:
            if self._line_intersects_circle(from_point, to_point, zone):
                return True
        return False
        
    def _line_intersects_circle(self, p1: Point, p2: Point, zone: NoFlyZone) -> bool:
        """Check if line segment intersects a circle"""
        # Simplified circle-line intersection
        center = zone.center
        radius = zone.radius
        
        # Distance from center to line
        x1, y1 = p1.lat, p1.lng
        x2, y2 = p2.lat, p2.lng
        x0, y0 = center.lat, center.lng
        
        # Calculate closest point on line segment to circle center
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            dist = math.sqrt((x0 - x1)**2 + (y0 - y1)**2)
            return dist <= radius
            
        t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        dist = math.sqrt((closest_x - x0)**2 + (closest_y - y0)**2)
        return dist <= radius
        
    def set_weather(self, point: Point, condition: WeatherCondition):
        """Set weather condition at a location"""
        self.weather_conditions[point.name] = condition
        
    def add_no_fly_zone(self, zone: NoFlyZone):
        """Add a no-fly zone"""
        self.no_fly_zones.append(zone)
        
    def find_shortest_path(self, start: str, end: str) -> Tuple[List[str], float]:
        """Dijkstra algorithm for shortest path"""
        try:
            path = nx.dijkstra_path(self.graph, start, end, weight='weight')
            cost = nx.dijkstra_path_length(self.graph, start, end, weight='weight')
            return path, cost
        except nx.NetworkXNoPath:
            return [], float('inf')
            
    def optimize_delivery_network(self) -> List[Tuple[str, str]]:
        """Minimum Spanning Tree for network optimization"""
        mst = nx.minimum_spanning_tree(self.graph, weight='weight')
        return list(mst.edges())
        
    def explore_area(self, start: str, method: str = 'dfs') -> List[str]:
        """DFS/BFS area exploration"""
        if method == 'dfs':
            return list(nx.dfs_preorder_nodes(self.graph, start))
        else:
            return list(nx.bfs_tree(self.graph, start))
            
    def find_charging_station_path(self, start: str) -> Tuple[List[str], float]:
        """Find nearest charging station"""
        nearest = None
        min_cost = float('inf')
        best_path = []
        
        for station in self.charging_stations:
            path, cost = self.find_shortest_path(start, station)
            if cost < min_cost and path:
                min_cost = cost
                best_path = path
                nearest = station
                
        return best_path, min_cost
        
    def get_route_details(self, path: List[str]) -> Dict:
        """Get detailed information about a route"""
        total_distance = 0
        total_weather_factor = 0
        segments = []
        
        for i in range(len(path)-1):
            edge_data = self.graph.get_edge_data(path[i], path[i+1])
            if edge_data:
                total_distance += edge_data['distance']
                total_weather_factor += edge_data['weather_factor']
                segments.append({
                    'from': path[i],
                    'to': path[i+1],
                    'distance': edge_data['distance'],
                    'weather_factor': edge_data['weather_factor'],
                    'cost': edge_data['weight']
                })
                
        return {
            'path': path,
            'total_distance': total_distance,
            'total_cost': total_distance * (total_weather_factor / len(segments)) if segments else 0,
            'segments': segments,
            'num_stops': len(path)
        }