import csv

file = open('Cartelera20251.csv', 'r')

reader = csv.DictReader(file)

headers = reader.fieldnames

dict_materias_multiple_tipo = {}

dict_sesiones_mult_prof = {}

i = 1

for row in reader:
    

    materia = row['Materia']
    tipo = row['Tipo horario (franja)']
    
    if materia not in dict_materias_multiple_tipo:
        dict_materias_multiple_tipo[materia] = [tipo]
    else:
        list_tipos = dict_materias_multiple_tipo[materia]
        if tipo not in list_tipos:
            list_tipos.append(tipo)
            
    prof = row['Profesor(es)']
    
    if '|' in prof:
        nivel_materia = int(materia[5])
        if nivel_materia < 4:
            prof_list = prof.split('|')
            nrc = row['NRC']
            id = f'{nrc}-{i}'
            i += 1
            dict_sesiones_mult_prof[id] = (prof_list, materia)
        
    
    


for materia in dict_materias_multiple_tipo:
    list_tipos = dict_materias_multiple_tipo[materia]
    if len(list_tipos)>1:
        tipos = ''
        for tipo in list_tipos:
            tipos += tipo + ', '
        tipos = tipos.rstrip(', ')  # Remove the last ', '
        print('-------------')
        print(f'Materia: {materia}')
        print(f'Tipos: {tipos}')

for sesion in dict_sesiones_mult_prof:
    prof_list, materia = dict_sesiones_mult_prof[sesion]
    nrc_sesion = sesion.split('-')[0]
    print('-------------')
    print(f'NRC: {nrc_sesion}')
    print(f'Materia: {materia}')
    print(f'Profs:')
    for prof in prof_list:
        print(prof)

# Close the file
file.close()




