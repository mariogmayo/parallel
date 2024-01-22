import random
import time
import multiprocessing
import mpi4py
mpi4py.rc.initialize = False # do not initialize MPI automatically
mpi4py.rc.finalize = False # do not finalize MPI automatically
from mpi4py import MPI # import the 'MPI' module

#IMPORTANTE: PARA EJECUTAR, DESDE EL TERMINAL (O MOBAXTERM) MOVERNOS AL DIRECTORIO DONDE ESTÉ EL .PY Y EJECUTAR LA LINEA
# mpiexec -n 5 python -m mpi4py busqueda_tesoro.py
#ASI SIMULAMOS EL ESTAR USANDO CINCO NODOS DIFERENTES, 4 JUGADORES Y 1 MASTER

#Generar el tablero y situar a los jugadores y al tesoro
def generar_juego(m,n):
	#Primer cuadrante - J1
	j1_x=random.randint(0,n//2-1)
	j1_y=random.randint(0,m//2-1)
	j1=j1_x+j1_y*n

	#Segundo cuadrante - J2
	j2_x=random.randint(n//2,n-1)
	j2_y=random.randint(0,m//2-1)
	j2=j2_x+j2_y*n

	#Tercer cuadrante - J3
	j3_x=random.randint(0,n//2-1)
	j3_y=random.randint(m//2,m-1)
	j3=j3_x+j3_y*n

	#Cuarto cuadrante - J4
	j4_x=random.randint(n//2,n-1)
	j4_y=random.randint(m//2,m-1)
	j4=j4_x+j4_y*n

	#Tesoro
	tesoro=random.randint(0,n*m-1)
	while tesoro==j1 or tesoro==j2 or tesoro==j3 or tesoro==j4:#Nos aseguramos de que el tesoro
		#no este en la misma casilla que un jugador
		tesoro=random.randint(0,n*m-1)

	return [tesoro,j1,j2,j3,j4]

#Moverse a una casilla adyacente (si es posible no pisada, si no aleatoria)
def movimiento(m,n,x,pisadas):

	direcciones=[-1,1,-n,n]# izquierda,derecha,arriba y abajo

	random.shuffle(direcciones)#ordenamos aleatoriamente las direcciones
	dir1=0 #Direccion principal: sera una QUE NO HAYAMOS PISADO (si existe, si no se quedara en 0)
	dir2=0 #Direccion secundaria: sera una A LA QUE ES FISICAMENTE POSIBLE MOVERSE (NO BORDES), por si hemos pisado todas las de alrededor
	i=0

	#Bucle para movernos: comprobamos si hay alguna casilla adyacente que no hayamos pisado ya. Si la encontramos, la guardamos en dir1 y salimos 
	#					  del bucle. Si no, guardamos una direccion aleatoria en dir2 y salimos del bucle (i==4) 
	while i!=4 and (dir1 not in direcciones):
		direccion=direcciones[i]

		if direcciones[i]==-1 and x%n!=0:# Sale direccion izquierda y no estamos en el borde
			dir2=direcciones[i]
			if x-1 not in pisadas:# No hemos pisado la casilla de la izquierda aun
				dir1=direcciones[i]
		elif direcciones[i]==1 and x%n!=n-1:# Sale direccion derecha y no estamos en el borde
			dir2=direcciones[i]
			if x+1 not in pisadas:# No hemos pisado la casilla de la derecha aun
				dir1=direcciones[i]
		elif direcciones[i]==-n and x//n!=0:# Sale direccion arriba y no estamos en el borde
			dir2=direcciones[i]
			if x-n not in pisadas:# No hemos pisado la casilla de arriba aun
				dir1=direcciones[i]
		elif direcciones[i]==n and x//n!=m-1:# Sale direccion abajo y no estamos en el borde
			dir2=direcciones[i]
			if x+n not in pisadas:# No hemos pisado la casilla de la izquierda aun
				dir1=direcciones[i]
		i=i+1

	if dir1==0:#Si hemos salido del bucle y dir1 es 0, significa que no hemos encontrado una direccion que no hemos pisado asi que vamos en una aleatoria
		x=x+dir2
	else:#Si no, significa que hemos encontrado una direccion que no hemos pisado luego nos movemos a esa y añadimos la casilla a la lista de pisadas
		x=x+dir1
		pisadas.append(x)

	return x

MPI.Init()
mpi_id=MPI.COMM_WORLD.Get_rank()
num_procs=MPI.COMM_WORLD.Get_size()

#Variable para saber si se ha acabado la partida
fin_juego=0

#PREPARATIVOS DEL JUEGO

#El nodo master genera las posiciones iniciales de los jugadores y del tesoro
if mpi_id == 0:
	#Dimensiones del tablero (primero solo las conoce el master, luego las enviara a cada jugador)
	m=100
	n=100
	pos=generar_juego(m,n)
else:
	#El resto de nodos inicializan algunas variables que usaran luego
	pisadas=[]
	pos=''
	m=''
	n=''
MPI.COMM_WORLD.Barrier()#Los jugadores esperan a que el master acabe los preparativos

#Se reparte a cada jugador las dimensiones del tablero y su posicion inicial (el nodo master lo que obtiene es la posicion del tesoro)
m = MPI.COMM_WORLD.bcast(m,root=0)
n = MPI.COMM_WORLD.bcast(n,root=0)
pos = MPI.COMM_WORLD.scatter(pos, root=0)


#Los miembros de la pareja comparten sus posiciones
for i in range(1,4,2):
	if mpi_id==i:
		pisadas.append(pos)
		MPI.COMM_WORLD.send(pos,dest=i+1,tag=42)
		pos_comp=MPI.COMM_WORLD.recv(source=i+1,tag=42)
		pisadas.append(pos_comp)
		#print("Soy el jugador "+str(mpi_id)+" y he recibido de mi compañero la posicion "+str(pos_comp)+".")
	elif mpi_id==i+1:
		pisadas.append(pos)
		pos_comp=MPI.COMM_WORLD.recv(source=i,tag=42)
		pisadas.append(pos_comp)
		MPI.COMM_WORLD.send(pos,dest=i,tag=42)
		#print("Soy el jugador "+str(mpi_id)+" y he recibido de mi compañero la posicion "+str(pos_comp)+".")
MPI.COMM_WORLD.Barrier()#Se espera a que todos los nodos lleguen aqui para comenzar con los turnos

#LISTOS PARA EMPEZAR A JUGAR

while fin_juego==0:
	#Cada miembro de la pareja se mueve y le dice a su compañero donde se ha movido
	for i in range(1,4,2):
		if mpi_id==i+1:#J2 y J4
			pos=movimiento(m,n,pos,pisadas)#J2/J4 se mueve
			MPI.COMM_WORLD.send(pos,dest=i,tag=42)#J2/J4 envia su nueva posicion a J1/J3
			pos_comp=MPI.COMM_WORLD.recv(source=i,tag=42)#J2/J4 recibe la nueva posición de J1/J3
			pisadas.append(pos_comp)#J2/J4 anota la nueva posicion del compañero J1/J3
		elif mpi_id==i:
			pos_comp=MPI.COMM_WORLD.recv(source=i+1,tag=42)#J2/J4 recibe la nueva posición de J1/J3
			pisadas.append(pos_comp)#J1/J3 anota la nueva posicion del compañero J2/J4
			pos=movimiento(m,n,pos,pisadas)#J1/J3 se mueve
			MPI.COMM_WORLD.send(pos,dest=i+1,tag=42)#J1/J3 envia su nueva posicion a J2/J4
	MPI.COMM_WORLD.Barrier()#Se espera a que todos los jugadores terminen de moverse

	#El nodo master recoge las posiciones de los jugadores
	posiciones = MPI.COMM_WORLD.gather(pos,root=0)
	
	if mpi_id == 0:
		#Muestra por pantalla las posiciones de los jugadores para poder seguir visualmente la partida
		print(posiciones)
		#Comprueba si algun jugador ha encontrado el tesoro
		for i in range(1,5):
			if posiciones[i]==pos:
				print("EL JUGADOR "+str(i)+" HA ENCONTRADO EL TESORO")
				fin_juego=i#Si se ha encontrado el tesoro, se guarda quien ha sido en fin_juego para salir del bucle y para recordar al ganador

	MPI.COMM_WORLD.Barrier()#Los jugadores esperan a que el master acabe la comprobacion
	#Se comunica si ha acabado el juego (y el ganador en caso afirmativo) a los jugadores
	fin_juego=MPI.COMM_WORLD.bcast(fin_juego,root=0)

MPI.Finalize()