import time         # pegar o tempo de execusao

class Server:
    def __init__(self, id, capacity):
        self.id = id
        self.capacity = capacity
        self.memory = []
        self.tasks_to_do = {}

    # uso definido -> quickfit

    # passa a task para a lista a ser feita
    def assign_task(self, task):
        # verificar a capacidade do servidor
        # buscar por um que tenha vaga e preencher ele depois procurar outro
        pass

    # retorna a task a ser executada
    def get_task(self):
        pass


    def do_task(self):
        # tira a task do servidor
        pass
    

