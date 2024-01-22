import numpy as np
import multiprocessing
from multiprocessing import Pool
import time
import sys

def producto(c,a,b,m,n,K):
	for i in range(m):
		for j in range(n):
			for k in range(K):
				c[i*n+j]=c[i*n+j]+a[i*K+k]*b[k*n+j]
	return c

def validador(c_res,prod):
	err = 0
	for i in range(len(c_res)):
		err = err+abs(c_res[i]-prod[i])
	return err

#PARALELIZAR i EN i->j->k (cada thread calcula ciertas filas)
def calcular_filas(c,a,b,m,n,K,inicial,final):
	for i in range(inicial,final):
		for j in range(n):
			for k in range(K):
				c[i*n+j]=c[i*n+j]+a[i*K+k]*b[k*n+j]
	return

#PARALELIZAR j EN j->i->k (cada thread calcula ciertas columnas)
def calcular_cols(c,a,b,m,n,K,inicial,final):
	for j in range(inicial,final):
		for i in range(m):
			for k in range(K):
				c[i*n+j]=c[i*n+j]+a[i*K+k]*b[k*n+j]
	return

#PARALELIZAR i EN k->j->i (cada thread calcula ciertas filas de una única columna)
def calcular_filas_col(c,a,b,m,n,K,inicial,final,j,k):
	for i in range(inicial,final):
		c[i*n+j]=c[i*n+j]+a[i*K+k]*b[k*n+j]
	print('a')
	return

#--------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	#Generamos las matrices (aleatorias)

	m, K, n = 500, 500, 500
	
	#Introducir dimensiones por el terminal
 	#m = int(sys.argv[1])
	#K = int(sys.argv[2])
	#n = int(sys.argv[3])

	C = np.random.rand(m,n)
	A = np.random.rand(m,K)
	B = np.random.rand(K,n)

	#Dimensiones de las matrices
	#m=len(A)
	#K=len(A[0])
	#n=len(B[0])

	#'Flatteneamos' las matrices
	a = A.flatten()
	b = B.flatten()
	c0 = C.flatten()
	c = multiprocessing.Array('d', m*n, lock=False)

	c[:]=c0
#--------------------------------------------------------------------------------------------------------------------------
	#CALCULO SECUENCIAL
	tiempo_inicial_secuencial = time.time()
	prod = producto(c,a,b,m,n,K)
	tiempo_final_secuencial = time.time()
	tiempo_total_secuencial = tiempo_final_secuencial-tiempo_inicial_secuencial

	#Mostramos por pantalla el tiempo
	print("Tiempo calculo secuencial: "+str(tiempo_total_secuencial))
#--------------------------------------------------------------------------------------------------------------------------
	#PREPARATIVOS PARA EL CALCULO PARALELO
	#Numero de threads
	nthreads=multiprocessing.cpu_count()	#Para las distintas pruebas se ha ido dividiendo entre sus divisores enteros

	#Numero minimo de filas/columnas que va a calcular cada thread
	filas_thread = m//nthreads
	cols_thread = n//nthreads

	#Numero de threads que van a tener que calcular una fila/columna mas
	filas_sobran = m%nthreads
	cols_sobran = n%nthreads

	#Inicializamos a 0 la fila/columna inicial
	fila_inicial = 0
	col_inicial = 0
#--------------------------------------------------------------------------------------------------------------------------
	#CALCULO EN PARALELO 1: POR FILAS
	#Empezamos a contar el tiempo paralelo
	tiempo_inicial_paralelo1 = time.time()

	#Asignamos a cada thread su trabajo
	processes = []
	for i in range(nthreads):
		if (i<filas_sobran):#Threads que tienen que calcular una fila mas
			p = multiprocessing.Process(target=calcular_filas,args=(c,a,b,m,n,K,fila_inicial,fila_inicial+filas_thread+1))
			processes.append(p)
			p.start()
			fila_inicial = fila_inicial+filas_thread+1
		else:#Threads que NO tienen que calcular una fila mas
			p = multiprocessing.Process(target=calcular_filas,args=(c,a,b,m,n,K,fila_inicial,fila_inicial+filas_thread))
			processes.append(p)
			p.start()
			fila_inicial = fila_inicial+filas_thread

	for p in processes:
		p.join()

	#Dejamos de contar el tiempo paralelo
	tiempo_final_paralelo1 = time.time()
	tiempo_total_paralelo1 = tiempo_final_paralelo1-tiempo_inicial_paralelo1

	#Mostramos por pantalla si el resultado es correcto y el tiempo
	print("Validador 1 (0 si coinciden las matrices): "+str(validador(c,prod)))
	print("Tiempo calculo paralelo 1: "+str(tiempo_total_paralelo1))
#--------------------------------------------------------------------------------------------------------------------------
	#CALCULO EN PARALELO 2: POR COLUMNAS
	c[:]=c0

	#Empezamos a contar el tiempo paralelo
	tiempo_inicial_paralelo2 = time.time()

	#Asignamos a cada thread su trabajo
	processes = []
	for j in range(nthreads):
		if (j<cols_sobran):#Threads que tienen que calcular una columna mas
			p = multiprocessing.Process(target=calcular_cols,args=(c,a,b,m,n,K,col_inicial,col_inicial+cols_thread+1))
			processes.append(p)
			p.start()
			col_inicial = col_inicial+cols_thread+1
		else:#Threads que NO tienen que calcular una columna mas
			p = multiprocessing.Process(target=calcular_cols,args=(c,a,b,m,n,K,col_inicial,col_inicial+cols_thread))
			processes.append(p)
			p.start()
			col_inicial = col_inicial+cols_thread

	for p in processes:
		p.join()

	#Dejamos de contar el tiempo paralelo
	tiempo_final_paralelo2 = time.time()
	tiempo_total_paralelo2 = tiempo_final_paralelo2-tiempo_inicial_paralelo2

	#Mostramos por pantalla si el resultado es correcto y el tiempo
	print("Validador 2 (0 si coinciden las matrices): "+str(validador(c,prod)))
	print("Tiempo calculo paralelo 2: "+str(tiempo_total_paralelo2))
	
#--------------------------------------------------------------------------------------------------------------------------
	'''
	#CALCULO EN PARALELO 3:
	#Este funciona muy lento al tener que inicializar muchos procesos. Un producto de una matriz 10x3 por una 3x10 ha llegado a tardar 11 segundos
	c[:]=c0

	#Empezamos a contar el tiempo paralelo
	tiempo_inicial_paralelo3 = time.time()

	for k in range(K):
		for j in range(n):
			fila_inicial=0
			for i in range(nthreads):
				if (i<filas_sobran):#Threads que tienen que calcular una fila mas
					p = multiprocessing.Process(target=calcular_filas_col,args=(c,a,b,m,n,K,fila_inicial,fila_inicial+filas_thread+1,j,k))
					processes.append(p)
					p.start()
					fila_inicial = fila_inicial+filas_thread+1
				else:#Threads que NO tienen que calcular una fila mas
					p = multiprocessing.Process(target=calcular_filas_col,args=(c,a,b,m,n,K,fila_inicial,fila_inicial+filas_thread,j,k))
					processes.append(p)
					p.start()
					fila_inicial = fila_inicial+filas_thread

			for p in processes:
				p.join()

	#Dejamos de contar el tiempo paralelo
	tiempo_final_paralelo3 = time.time()
	tiempo_total_paralelo3 = tiempo_final_paralelo3-tiempo_inicial_paralelo3

	print("Validador 3 (0 si coinciden las matrices): "+str(validador(c,prod)))
	print("Tiempo calculo paralelo 3: "+str(tiempo_total_paralelo3))
	'''
