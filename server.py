from multiprocessing import Process, Manager
from threading import Thread, Lock, Event
from colors import red, green, blue
from time import time, sleep
<<<<<<< HEAD

def process_task_worker(server_id, task, result_queue, manager_start_time): 
=======
from threading import Thread, Lock, Event
from multiprocessing import Process, Manager

def process_task_worker(server_id, task, result_queue): 
>>>>>>> 752b6ce25be7851fcb68102b0a836be99d81e7d8
    """Função executada por cada processo filho para processar uma tarefa"""
    task_id = task.get('id')
    tempo_exec_slice = task.get('tempo_restante', 0)
    tempo_atribuicao = task.get('tempo_atribuicao')
    
    server_log_prefix = f"Servidor {server_id}"
<<<<<<< HEAD
    tempo_corrido = time() - manager_start_time

    print(f"[{tempo_corrido:.2f}] [{server_log_prefix}] {red('PROCESSANDO SLICE')} | Tarefa {task_id} | Duração: {tempo_exec_slice:.2f}s")
=======

    print(f"  [{server_log_prefix}] {red('PROCESSANDO SLICE')} | Tarefa {task_id} | Duração: {tempo_exec_slice:.2f}s")
>>>>>>> 752b6ce25be7851fcb68102b0a836be99d81e7d8
    
    # Simula o tempo de processamento do 'slice'
    sleep(tempo_exec_slice)
    
    tempo_conclusao = time()
    tempo_resposta = tempo_conclusao - tempo_atribuicao
    
    # Coloca o resultado da conclusão na fila de resultados
    result_queue.put({
        'task_id': task_id,
        'tempo_resposta': tempo_resposta,
    })
    
<<<<<<< HEAD
    tempo_corrido = time() - manager_start_time
    print(f"[{tempo_corrido:.2f}] [{server_log_prefix}] {green('SLICE CONCLUÍDO')} | Tarefa {task_id}")
=======
    print(f"  [{server_log_prefix}] {green('SLICE CONCLUÍDO')} | Tarefa {task_id}")
>>>>>>> 752b6ce25be7851fcb68102b0a836be99d81e7d8


class Server(Thread):
    def __init__(self, id, max_capacity, task_manager=None): 
        super().__init__()
        self.id = id
        self.max_capacity = max_capacity 
<<<<<<< HEAD
        self.capacity = 0
        self.tasks_to_do = []
        self.active_processes = []
        self.lock = Lock()
        self.stop_event = Event()
        self.daemon = True
        
        self.task_manager = task_manager
        self.manager = Manager() 
        self.result_queue = self.manager.Queue() 

    def assign_task(self, task: dict):
        """Adiciona tarefa à fila local do servidor (thread-safe) e atualiza capacidade imediatamente."""
        with self.lock: 
=======
        self.capacity = 0               # Capacidade atualmente ocupada
        self.tasks_to_do = []           # Fila local de tarefas (slices) a serem processadas
        self.active_processes = []      # Lista de Processos ativos
        self.lock = Lock()              # Lock de Thread para proteger o acesso a dados compartilhados
        self.stop_event = Event()       # Evento para sinalizar o encerramento da Thread
        self.daemon = True              # Define a Thread como daemon (encerra com o programa principal)
        
        self.task_manager = task_manager
        self.manager = Manager() # Gerenciador para objetos compartilhados entre Processos
        self.result_queue = self.manager.Queue() # Fila de resultados para comunicação entre Processos e Thread do Servidor

    def assign_task(self, task: dict):
        """Adiciona tarefa à fila local do servidor (thread-safe) e atualiza capacidade imediatamente."""
        with self.lock: # Protege o acesso a self.capacity e self.tasks_to_do
>>>>>>> 752b6ce25be7851fcb68102b0a836be99d81e7d8
            task_id = task.get('id')
            
            if self.capacity < self.max_capacity:
                if task_id is not None:
                    task['tempo_atribuicao'] = time() 
                    self.tasks_to_do.append(task)
                    
                    self.capacity += 1 
                    
                    return True
            return False
    
    def get_server_status(self):
        """Retorna status atual: capacidade ocupada e disponibilidade"""
        with self.lock:
            total_load = self.capacity
            return {
                'id': self.id,
                'current_capacity': total_load,
                'max_capacity': self.max_capacity,
                'is_full': total_load >= self.max_capacity
            }

    def start_task_process(self, task):
        """Cria e inicia um processo filho para executar a tarefa"""
<<<<<<< HEAD
        manager_start_time = self.task_manager.start_time if self.task_manager else time()
        
        # Passa manager_start_time como argumento para o processo filho
        process = Process(target=process_task_worker, args=(self.id, task, self.result_queue, manager_start_time))
=======
        # Cria um Processo que executa process_task_worker
        process = Process(target=process_task_worker, args=(self.id, task, self.result_queue))
>>>>>>> 752b6ce25be7851fcb68102b0a836be99d81e7d8
        process.start()
        
        with self.lock:
            self.active_processes.append({
                'process': process,
                'task_id': task.get('id'),
                'start_time': time()
            })
<<<<<<< HEAD
            
        tempo_corrido = time() - manager_start_time 
        print(f"[{tempo_corrido:.2f}] Servidor {self.id}: {blue('-> PROCESSO INICIADO')} para Tarefa {task.get('id')} (Cap. {self.capacity}/{self.max_capacity})")
=======
        
        print(f"Servidor {self.id}: {blue('-> PROCESSO INICIADO')} para Tarefa {task.get('id')} (Cap. {self.capacity}/{self.max_capacity})")
>>>>>>> 752b6ce25be7851fcb68102b0a836be99d81e7d8

    def check_completed_processes(self):
        """Verifica processos finalizados, coleta resultados e libera capacidade"""
        # Processa resultados na fila (MultiProcess -> Server Thread)
        while not self.result_queue.empty():
            result = self.result_queue.get()
            # Envia resultado para o TaskManager (se existir)
            if self.task_manager:
                self.task_manager.register_completion(
                    result['task_id'], 
                    result['tempo_resposta']
                )
        
<<<<<<< HEAD
        manager_start_time = self.task_manager.start_time if self.task_manager else time()

        with self.lock: 
=======
        with self.lock: # Protege o acesso à lista de processos ativos e self.capacity
>>>>>>> 752b6ce25be7851fcb68102b0a836be99d81e7d8
            finished = []
            for proc_info in self.active_processes:
                # Verifica se o Processo terminou
                if not proc_info['process'].is_alive():
<<<<<<< HEAD
                    proc_info['process'].join() 
                    finished.append(proc_info)
                    
                    self.capacity -= 1 
                    
                    tempo_corrido = time() - manager_start_time 
                    print(f"[{tempo_corrido:.2f}] Servidor {self.id}: {green('<- PROCESSO ENCERRADO')} | Tarefa {proc_info['task_id']} (Cap. {self.capacity}/{self.max_capacity})")
=======
                    proc_info['process'].join() # Aguarda a terminação completa
                    finished.append(proc_info)
                    
                    self.capacity -= 1 # Libera uma unidade de capacidade
                    
                    print(f"Servidor {self.id}: {green('<- PROCESSO ENCERRADO')} | Tarefa {proc_info['task_id']} (Cap. {self.capacity}/{self.max_capacity})")
>>>>>>> 752b6ce25be7851fcb68102b0a836be99d81e7d8
            
            # Remove os Processos finalizados da lista de ativos
            for proc_info in finished:
                self.active_processes.remove(proc_info)

    def run(self):
        """Loop principal da thread do servidor"""
<<<<<<< HEAD
        manager_start_time = self.task_manager.start_time if self.task_manager else time()
        tempo_corrido = time() - manager_start_time
        print(f"[{tempo_corrido:.2f}] Servidor {self.id}: {blue('INICIADO')} - Capacidade: {self.max_capacity} processos simultâneos")
        
        while not self.stop_event.is_set(): 
            self.check_completed_processes() 
            
            with self.lock: 
                while self.tasks_to_do and self.capacity <= self.max_capacity:
                    task = self.tasks_to_do.pop(0) 
=======
        print(f"Servidor {self.id}: {blue('INICIADO')} - Capacidade: {self.max_capacity} processos simultâneos")
        
        while not self.stop_event.is_set(): # Continua rodando até o evento de parada ser ativado
            self.check_completed_processes() # Verifica e gerencia processos finalizados
            
            with self.lock: # Tenta iniciar novas tarefas da fila local
                while self.tasks_to_do and self.capacity <= self.max_capacity:
                    task = self.tasks_to_do.pop(0) # Pega a próxima tarefa
>>>>>>> 752b6ce25be7851fcb68102b0a836be99d81e7d8
                    
                    # Libera e readquire o lock para permitir que outras Threads interajam
                    self.lock.release()
                    self.start_task_process(task)
                    self.lock.acquire()
            
<<<<<<< HEAD
            sleep(0.05) 
        
        tempo_corrido = time() - manager_start_time
        print(f"[{tempo_corrido:.2f}] Servidor {self.id}: Aguardando processos finalizarem...")
        
=======
            sleep(0.05) # Pequena pausa para evitar consumo excessivo de CPU
        
        print(f"Servidor {self.id}: Aguardando processos finalizarem...")
>>>>>>> 752b6ce25be7851fcb68102b0a836be99d81e7d8
        # Encerramento: Aguarda todos os processos ativos terminarem
        with self.lock:
            processes_to_wait = list(self.active_processes)
        
        for proc_info in processes_to_wait:
            proc_info['process'].join()
        
        tempo_corrido = time() - manager_start_time
        print(f"[{tempo_corrido:.2f}] Servidor {self.id}: {red('ENCERRADO')}")

    def stop(self):
        """Sinaliza encerramento da thread do servidor"""
        self.stop_event.set()