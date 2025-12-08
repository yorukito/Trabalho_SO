from multiprocessing import Process, Manager
from threading import Thread, Lock, Event
from colors import red, green, blue
from time import time, sleep

def process_task_worker(server_id, task, result_queue, manager_start_time): 
    """Execute task processing in isolated child process"""
    
    task_id = task.get('id')
    execution_time_slice = task.get('tempo_restante', 0)
    assignment_time = task.get('tempo_atribuicao')
    
    server_log_prefix = f"Servidor {server_id}"
    elapsed_time = time() - manager_start_time

    print(f"[{elapsed_time:.2f}] [{server_log_prefix}] {red('PROCESSANDO SLICE')} | Tarefa {task_id} | Duração: {execution_time_slice:.2f}s")
    
    # Simulate task execution time
    sleep(execution_time_slice)
    
    completion_time = time()
    response_time = completion_time - assignment_time
    
    # Send completion result back to server
    result_queue.put({
        'task_id': task_id,
        'tempo_resposta': response_time,
    })
    
    elapsed_time = time() - manager_start_time
    print(f"[{elapsed_time:.2f}] [{server_log_prefix}] {green('SLICE CONCLUÍDO')} | Tarefa {task_id}")


class Server(Thread):
    def __init__(self, id, max_capacity, task_manager=None): 
        super().__init__()
        
        # Server configuration
        self.id = id
        self.max_capacity = max_capacity 
        self.capacity = 0
        
        # Task management
        self.tasks_to_do = []
        self.active_processes = []
        
        # Thread synchronization
        self.lock = Lock()
        self.stop_event = Event()
        self.daemon = True
        
        # Inter-process communication
        self.task_manager = task_manager
        self.manager = Manager() 
        self.result_queue = self.manager.Queue() 

    def assign_task(self, task: dict):
        """Add task to server queue (thread-safe)"""
        
        with self.lock: 
            task_id = task.get('id')
            
            if self.capacity < self.max_capacity:
                if task_id is not None:
                    task['tempo_atribuicao'] = time() 
                    self.tasks_to_do.append(task)
                    self.capacity += 1 
                    return True
            return False
    
    def get_server_status(self):
        """Return current server capacity and availability"""
        
        with self.lock:
            total_load = self.capacity
            return {
                'id': self.id,
                'current_capacity': total_load,
                'max_capacity': self.max_capacity,
                'is_full': total_load >= self.max_capacity
            }

    def start_task_process(self, task):
        """Create and launch child process for task execution"""
        
        manager_start_time = self.task_manager.start_time if self.task_manager else time()
        
        # Spawn isolated process
        process = Process(target=process_task_worker, args=(self.id, task, self.result_queue, manager_start_time))
        process.start()
        
        # Track active process
        with self.lock:
            self.active_processes.append({
                'process': process,
                'task_id': task.get('id'),
                'start_time': time()
            })
            
        elapsed_time = time() - manager_start_time 
        print(f"[{elapsed_time:.2f}] Servidor {self.id}: {blue('-> PROCESSO INICIADO')} para Tarefa {task.get('id')} (Cap. {self.capacity}/{self.max_capacity})")

    def check_completed_processes(self):
        """Collect results from finished processes and free capacity"""
        
        # Process completion results from child processes
        while not self.result_queue.empty():
            result = self.result_queue.get()
            
            # Forward result to task manager
            if self.task_manager:
                self.task_manager.register_completion(
                    result['task_id'], 
                    result['tempo_resposta']
                )
        
        manager_start_time = self.task_manager.start_time if self.task_manager else time()

        # Check and clean up finished processes
        with self.lock: 
            finished = []
            for process_info in self.active_processes:
                if not process_info['process'].is_alive():
                    process_info['process'].join() 
                    finished.append(process_info)
                    
                    self.capacity -= 1 
                    
                    elapsed_time = time() - manager_start_time 
                    print(f"[{elapsed_time:.2f}] Servidor {self.id}: {green('<- PROCESSO ENCERRADO')} | Tarefa {process_info['task_id']} (Cap. {self.capacity}/{self.max_capacity})")
            
            # Remove finished processes from tracking
            for process_info in finished:
                self.active_processes.remove(process_info)

    def run(self):
        """Main server thread loop"""
        
        manager_start_time = self.task_manager.start_time if self.task_manager else time()
        elapsed_time = time() - manager_start_time
        print(f"[{elapsed_time:.2f}] Servidor {self.id}: {blue('INICIADO')} - Capacidade: {self.max_capacity} processos simultâneos")
        
        while not self.stop_event.is_set(): 
            # Check for completed tasks
            self.check_completed_processes() 
            
            # Process queued tasks if capacity available
            with self.lock: 
                while self.tasks_to_do and self.capacity <= self.max_capacity:
                    task = self.tasks_to_do.pop(0) 
                    
                    # Release lock during process creation to allow concurrent access
                    self.lock.release()
                    self.start_task_process(task)
                    self.lock.acquire()
            
            sleep(0.05) 
        
        # Shutdown sequence
        elapsed_time = time() - manager_start_time
        print(f"[{elapsed_time:.2f}] Servidor {self.id}: Aguardando processos finalizarem...")
        
        # Wait for all active processes to complete
        with self.lock:
            processes_to_wait = list(self.active_processes)
        
        for process_info in processes_to_wait:
            process_info['process'].join()
        
        elapsed_time = time() - manager_start_time
        print(f"[{elapsed_time:.2f}] Servidor {self.id}: {red('ENCERRADO')}")

    def stop(self):
        """Signal server thread to shutdown"""
        
        self.stop_event.set()