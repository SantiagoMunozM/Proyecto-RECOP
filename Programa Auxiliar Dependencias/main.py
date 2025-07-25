import csv

with open('Cartelera20251.csv', 'r') as file:
    reader = csv.DictReader(file)
    dependencias = set()
    
    for row in reader:
        materia = row['Materia']
        dependencia = materia[:4]
        dependencias.add(dependencia)

print(dependencias)
        