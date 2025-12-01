from colors import red, green, blue
from time import time, sleep
from threading import Thread, Lock, Event
from multiprocessing import Process, Manager
import os

def process_task_worker(task, result_queue):
    """Função executada por cada processo filho para processar uma tarefa"""
    task_id = task.get('id')
    tempo_exec = task.get('tempo_restante', 0)
    tempo_atribuicao = task.get('tempo_atribuicao')
    pid = os.getpid()
    
    print(f"  [PID {pid}] {red('PROCESSANDO')} Tarefa {task_id} por {tempo_exec}s...")
    
    # Simula o processamento da tarefa
    sleep(tempo_exec)
    
    tempo_conclusao = time()
    tempo_resposta = tempo_conclusao - tempo_atribuicao
    
    # Envia resultado de volta via queue
    result_queue.put({
        'task_id': task_id,
        'tempo_resposta': tempo_resposta,
        'pid': pid
    })
    
    print(f"  [PID {pid}] {green('FINALIZADO')} Tarefa {task_id}")


class Server(Thread):
    def __init__(self, id, max_capacity, task_manager=None): 
        super().__init__()
        self.id = id
        self.max_capacity = max_capacity
        self.capacity = 0  # Número de processos ativos
        self.tasks_to_do = []  # Fila de tarefas aguardando processamento
        self.active_processes = []  # Lista de processos em execução
        self.lock = Lock()
        self.stop_event = Event()
        self.daemon = True
        self.task_manager = task_manager
        
        # Queue para receber resultados dos processos filhos
        self.manager = Manager()
        self.result_queue = self.manager.Queue()

    def assign_task(self, task: dict):
        """Adiciona tarefa à fila do servidor e inicia processo imediatamente se possível"""
        with self.lock:
            task_id = task.get('id')
            if 'tempo_restante' not in task:
                task['tempo_restante'] = task.get('tempo_exec', 0)
                
            if task_id is not None:
                task['tempo_atribuicao'] = time()
                self.tasks_to_do.append(task)
                return True
            return False

    def get_server_status(self):
        """Retorna status atual do servidor (considerando tarefas em fila + processos ativos)"""
        with self.lock:
            # Capacidade usada = processos rodando + tarefas na fila esperando iniciar
            total_load = self.capacity + len(self.tasks_to_do)
            return {
                'id': self.id,
                'current_capacity': total_load,
                'max_capacity': self.max_capacity,
                'is_full': total_load >= self.max_capacity
            }

    def start_task_process(self, task):
        """Inicia um novo processo para executar a tarefa"""
        process = Process(target=process_task_worker, args=(task, self.result_queue))
        process.start()
        
        with self.lock:
            self.active_processes.append({
                'process': process,
                'task_id': task.get('id'),
                'start_time': time()
            })
            self.capacity += 1
        
        print(f"Servidor {self.id}: {blue('INICIOU PROCESSO')} para Tarefa {task.get('id')} (Processos ativos: {self.capacity}/{self.max_capacity})")

    def check_completed_processes(self):
        """Verifica processos finalizados e coleta resultados"""
        # Processa resultados da queue
        while not self.result_queue.empty():
            result = self.result_queue.get()
            
            if self.task_manager:
                self.task_manager.register_completion(
                    result['task_id'], 
                    result['tempo_resposta']
                )
        
        # Remove processos finalizados da lista
        with self.lock:
            finished = []
            for proc_info in self.active_processes:
                if not proc_info['process'].is_alive():
                    proc_info['process'].join()  # Limpa o processo
                    finished.append(proc_info)
                    self.capacity -= 1
                    print(f"Servidor {self.id}: {green('PROCESSO ENCERRADO')} Tarefa {proc_info['task_id']} (Processos ativos: {self.capacity}/{self.max_capacity})")
            
            # Remove da lista
            for proc_info in finished:
                self.active_processes.remove(proc_info)

    def run(self):
        """Loop principal do servidor"""
        print(f"Servidor {self.id}: {blue('INICIADO')} - Capacidade: {self.max_capacity} processos simultâneos")
        
        while not self.stop_event.is_set():
            # Verifica e limpa processos finalizados
            self.check_completed_processes()
            
            # Inicia novos processos se houver tarefas e capacidade disponível
            with self.lock:
                while self.tasks_to_do and self.capacity < self.max_capacity:
                    task = self.tasks_to_do.pop(0)
                    # Libera o lock antes de iniciar o processo para evitar deadlock
                    self.lock.release()
                    self.start_task_process(task)
                    self.lock.acquire()
            
            sleep(0.05)  # Pequeno intervalo para não sobrecarregar CPU
        
        # Aguarda todos os processos terminarem no encerramento
        print(f"Servidor {self.id}: Aguardando processos finalizarem...")
        with self.lock:
            processes_to_wait = list(self.active_processes)
        
        for proc_info in processes_to_wait:
            proc_info['process'].join()
        
        print(f"Servidor {self.id}: {red('ENCERRADO')}")

    def stop(self):
        """Sinaliza encerramento do servidor"""
        self.stop_event.set()