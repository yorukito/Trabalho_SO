import json
import os

if __name__ == '__main__':
    # Checks if the tasks.json file exists in the current
    if os.path.exists('tasks.json'):
        
        # Opens the tasks.json file and reads it
        with open('tasks.json', 'r') as file:
            
            # Gets the json file and loads it into a python dictionary
            tasks = json.load(file)
                        
            # Sorts the json file info by capacity and priority, reversely sorted
            sorted_by_capacity = sorted(tasks['servidores'], key=lambda x: x['capacidade'], reverse=True)
            sorted_by_priority = sorted(tasks['requisicoes'], key=lambda x: x['prioridade'], reverse=True)
            sorted_by_time = sorted(tasks['requisicoes'], key=lambda x: x['tempo_exec'])
            
            # Returns a list dictionaries of servidores sorted by capacity
            print(sorted_by_capacity)
            
            # Print the servidores from tasks.json
            for id in tasks['servidores']:
                print("id:", id['id'])
                print("capacidade:", id['capacidade'])
                print()
            
            # Print the requisicoes of tasks.json
            for request in tasks['requisicoes']:
                print("id:", request['id'])
                print("tipo:", request['tipo'])
                print("prioridade:", request['prioridade'])
                print("tempo_exec:", request['tempo_exec'])
                print("temp_chegada:", request['temp_chegada'])
                print()
                
    else:
        print("File not found")
