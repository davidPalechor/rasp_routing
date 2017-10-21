# SCRIPT FOR READING/WRITING ON ROUTING TABLE
def write():
    with open('routing_table.txt', 'a') as text_file:
        for i in range(5):
            text_file.write('test \n')

def read(dir):
    with open('routing_table.txt', 'r') as text_file:
        for line in text_file:
            dir_list = line.split(',')
            if dir in dir_list[0]:
                return dir_list[:-1]
        return []