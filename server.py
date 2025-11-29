from time import sleep         # pegar o tempo de execusao
from threading import Thread

class Server(Thread):
    def __init__(self, id, max_capacity):
        super().__init__()
        self.id = id
        self.max_capacity = max_capacity
        self.capacity = 0
        self.tasks_to_do = {}

    def assign_task(self, task: dict):
        if self.capacity < self.max_capacity:
            task_id = task.get('id') 
            task_exec = task.get('tempo_exec')
            if task_id is not None:
                if 'tempo_servico' in task and 'tempo_restante' not in task:
                    task['tempo_restante'] = task['tempo_servico']
                    
                # Armazena o dicionário da tarefa inteira
                self.tasks_to_do[task_id, task_exec] = task
                self.capacity += 1
                print(f"Servidor {self.id}: Tarefa {task_id} atribuída.")
                print(f"Capacidade atual: {self.capacity}/{self.max_capacity}")
            else:
                print("Tarefa não pode ser atribuída: ID da tarefa não encontrado.")
        else:
            print(f"Servidor {self.id} (Capacidade Máxima: {self.max_capacity}) está cheio.")


    # retorna a task a ser executada
    def get_task(self):
        pass


    def do_task(self, task_id, tempo_executado=None):
        if task_id in self.tasks_to_do:
            task = self.tasks_to_do[task_id]
            
            if tempo_executado is not None:
                tempo_gasto = min(tempo_executado, task.get('tempo_restante', 0))
            else:
                tempo_gasto = task.get('tempo_restante', 0)
                
            if tempo_gasto > 0:
                print(f"Servidor {self.id}: Executando Tarefa {task_id} por {tempo_gasto} segundo(s)...")
                sleep(tempo_gasto) 
                task['tempo_restante'] -= tempo_gasto
                print(f"Servidor {self.id}: Tempo restante para Tarefa {task_id}: {task['tempo_restante']}s.")
            
            if task.get('tempo_restante', 0) <= 0:
                task_concluida = self.tasks_to_do.pop(task_id)
                self.capacity -= 1
                print(f"Servidor {self.id}: Tarefa {task_id} **CONCLUÍDA** e removida. Capacidade liberada.")
                return task_concluida
            else:
                return None
            
        return None


    def run(self):
        tasks_to_execute = list(self.tasks_to_do.keys())
        
        if not tasks_to_execute:
            print(f"Servidor {self.id}: Nenhuma tarefa para executar.")
            return
            
        print(f"Servidor {self.id} (Capacidade {self.max_capacity}): INICIANDO, {len(tasks_to_execute)} tarefas.")
            
        for task_info in tasks_to_execute:
            task_id, tempo_exec = task_info
            
            print(f"Servidor {self.id}: Executando Tarefa {task_id} por {tempo_exec} segundo(s)...")
            
            sleep(tempo_exec) 
            
            print(f"Servidor {self.id}: Tarefa {task_id} **CONCLUÍDA**.")

        print(f"Servidor {self.id}: Todas as tarefas finalizadas.")
            