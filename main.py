# rodar como python main.py 'tipo_de_arquitetura'

import sys              # pegar qual arquitetura vai rodar
import os               # pegar a utilizacao da cpu
import json             # pegar a quantidade dos servidores
import psutil         # pegar o uso de memoria

from threading import Thread

from master import Arquiteture
from server import Server

arquiteture = sys.argv[1]


def capture_utilization():
    pass

if __name__ == '__main__':
    if arquiteture in ['rr', 'sjf', 'priority']: 
        
        # crair uma thread
        if arquiteture == 'rr':
            print('rr')
            Arquiteture.rounding_robing()
        
        elif arquiteture == 'sjf':
            print('sjf')
            Arquiteture.sjf()  

        elif arquiteture == 'priority':
            print('priority')
            Arquiteture.priority()
        
        # loop (for) para criar os servidores

        # tread para pegar a utilizacao dos componentes
        capture_utilization()


