import sys
import json
import psutil

from master import TaskManager
from server import Server


def capture_utilization():
    """Measure CPU usage over 1 second interval"""
    
    cpu_usage_percentage = psutil.cpu_percent(interval=1) 
    return cpu_usage_percentage


if __name__ == '__main__':
    
    # Get scheduling algorithm from command line
    scheduling_algorithm = sys.argv[1]
    
    # Validate algorithm selection
    if scheduling_algorithm in ['rr', 'sjf', 'priority']:
        
        # Load configuration from JSON
        with open('tasks.json', 'r') as file:
            data = json.load(file)
        
        # Initialize servers
        servers = []
        for server_data in data["servidores"]:
            server = Server(server_data['id'], server_data['capacidade'])
            servers.append(server)
        
        requests = data['requisicoes']
        
        # Execute scheduling algorithm
        task_manager = TaskManager(scheduling_algorithm, servers, requests)
        task_manager.start()
        task_manager.join()

        # Calculate and display metrics
        cpu_utilization = capture_utilization()
        task_manager.calculate_metrics(cpu_utilization)