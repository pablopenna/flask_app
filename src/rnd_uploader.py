# -*- coding: UTF-8 -*-

"""
Esta clase se encargara de subir
los números aleatorios y su fecha 
tanto a la base de datos MySQL local
como a Beebotte cada dos minutos
"""

#Process para crear procesos. la variable enable deberá ser
#del tipo Value para que su valor se comparta entre procesos
from multiprocessing import Process, Value
#Hilos en vez de procesos
from threading import Thread
#para esperar los dos minutos
import time
#librerias propias para trabajar con las bases de datos
import sql_rnd
import beebotte_rnd
import mongo_rnd
#libreria propia para extraer un numero aleatorio de la web
import web_fetcher.rnd_fetcher
#libreria propia para trabajar con las fechas
import date_handler
#Clase encargada de crear SSE y
#enviarlos a los suscriptores.
from sse_handler import SSEHandler


class RndUploader:

    #Esta clase tiene un único atributo que es enable y
    #se inicializa como True. Miestras tenga este valor
    #se seguiran subiendo datos cada 2 minutos.
    #cuando se cambie su valor a Flase parara.
    def __init__(self, flaskApp, handSQL, handBee, handMongo,\
    tiempoSleep = 120, debug = False,handSSE=None):
        #self.__enable -> __enable es privado gracias a '__'
        #para acceder al valor de enable utilizaremos
        #self.__enable.value
        self.__enable=Value('b', True)
        #modo debug
        self.__debug=debug
        #tiempo a esperar entre inserciones
        self.__tiempo = tiempoSleep
        #Creo instancias PRIVADAS de las clases a utilizar
        #para obtener los  numeros aleatorios
        self.__RndGen = web_fetcher.rnd_fetcher.Rnd_fetcher()
        #manejar BBDD
        #self.__SQLHand = sql_rnd.SQLHandler(flaskApp)
        #self.__BeeHand = beebotte_rnd.BeeHandler()
        self.__SQLHand = handSQL
        self.__BeeHand = handBee
        #MongoClient opened before fork. Create MongoClient only after forking.
        #See PyMongo's documentation for details:
        #http://api.mongodb.org/python/current/faq.html#is-pymongo-fork-safe
        #No es seguro que esta clase reciba la instancia de MongoDB del main
        #Por lo que creare en esta clase mi propia instancia de MongoHandler
        #Esto no debería importar ya que aunque sean dos instancias distintas
        #leerán de la misma base de datos.
        #La instancia en esta clase se dedicará principalmente a escribir y la
        #que está en el main a leer.
        #
        #Debo crearla una vez dentro del subproceso creado, es decir,
        #dentro de la función upload que es la que ejecuta el proceso.
        #UPDATE: ya no es necesario, ya que ahora rnd_uploader crea un hilo 
        #en vez de un proceso, por lo que comparten memoria y no hace fork()
        #de esta instancia recibida de MongoHandler.
        self.__MongoHand= handMongo
        #self.__MongoHand= mongo_rnd.MongoHandler()

        #Manejador de SSE
        self.__SSEHand = handSSE

        #inicio proceso para subir los datos a las BBDD
        self.lanzar()
    
    #Devuelve el manejador de MySQL
    def getSQLHandler(self):
        return self.__SQLHand

    #Devuelve el manejador de Beebotte
    def getBeeHandler(self):
        return self.__BeeHand

    #Devuelve el manejador de MongoDB
    def getMongoHandler(self):
        return self.__MongoHand

    #Subira un número aleatorio cada 2 min
    def upload(self):
        #MongoClient opened before fork. Create MongoClient only after forking.
        #See PyMongo's documentation for details:
        #http://api.mongodb.org/python/current/faq.html#is-pymongo-fork-safe
        #No es seguro que esta clase reciba la instancia de MongoDB del main
        #Por lo que creare en esta clase mi propia instancia de MongoHandler
        #Esto no debería importar ya que aunque sean dos instancias distintas
        #leerán de la misma base de datos.
        #La instancia en esta clase se dedicará principalmente a escribir y la
        #que está en el main a leer.
        #
        #Debo crearla una vez dentro del subproceso creado, es decir,
        #dentro de la función upload que es la que ejecuta el proceso.
        #UPDATE: Ya no es necesario, porque la funcion upload() se 
        #lanza mediante un hilo  y no un proceso, por lo que ya no
        #se realiza ningún fork() que es sobre lo que va este aviso.
        #self.__MongoHand= mongo_rnd.MongoHandler()

        while self.__enable.value:

            #obtenemos numero aleatorio a insertar
            rnd = self.__RndGen.get_web_rnd()

            if self.__debug:
                print "num aleatorio a escribir: " + str(rnd)

            """
            #BORRA ESTO!-----------------------------
            #Este trozo de codigo sirve para que esta
            #clase no suba numeros.
            print "PELIGRO: BORRA ESTO!!! rnd-uploader.upload() line-70"
            self.__enable.value = False
            self.__SQLHand.readDataDB()
            self.__BeeHand.readRandom()
            self.__MongoHand.readRandom()
            #BORRA ESTO!-----------------------------
            """

            if self.__debug:
                print "rnd_uploader - Las listas en rnd_uploader: "
                print "BeeHandler : " + str(self.__BeeHand.listaGlobalNumero)
                print "SQLHandler : " + str(self.__SQLHand.listaGlobalNumero)
                print "MongoHandler : " + str(self.__MongoHand.listaGlobalNumero)

            #Escribir
            if(self.__enable.value):
                
                #La funcion de obtener numeros aleatorios
                #devuelve -1 en caso de no haber podido conectar
                #con la web de donde obtenemos los numeros aleatorios.
                #En este caso, rnd sera = a -1, por lo que no guardaremos
                #este valor en las BDs.
                if rnd > -1:
                    #escribo en Beebotte. 0 si bien. 1 si mal.
                    #resBee = self.__BeeHand.writeRandom(rnd, self.__debug)
                    #solo necesario para la BD local, ya que Beebotte
                    #almacena automaticamente la fecha
                    fecha = str(date_handler.getDatetimeMs())
                    #escribo en MongoDB. 0 si bien. 1 si mal.
                    #resMongo = self.__MongoHand.writeRandom(rnd, fecha)
                    #escribo en MySQL. 0 si bien. 1 si mal.
                    #resSQL = self.__SQLHand.writeDataDB(rnd, fecha, self.__debug)
                    #---
                    #envio SSE (notificación a los clientes con
                    #el número obtenido)
                    resBee=0
                    resMongo=1
                    resSQL=0
                    msg = "NUM.ALE. : " + str(rnd)
                    if resBee == 0:
                        msg += "#BD. : Beebotte"
                    if resMongo == 0:
                        msg += "#BD. : MongoDB"
                    if resSQL == 0:
                        msg += "#BD. : MySQL"
                    res = self.__SSEHand.createSSE(str(msg))
                    #if self.__debug:
                    if True:
                        print "rnd_uploader - ENVIANDO SSE: " + str(msg)
                        print res
                
                #ACTUALIZO LOS DATOS EN LAS LISTAS LOCALES 
                #DE LOS MANEJADORES
                self.__SQLHand.readDataDB()
                self.__BeeHand.readRandom()
                self.__MongoHand.readRandom()
                
                if self.__debug:
                    print "Tablas MySQL:"
                    print self.__SQLHand.listaGlobalFecha
                    print self.__SQLHand.listaGlobalNumero
                    print "Tablas Bee:"
                    print self.__BeeHand.listaGlobalFecha
                    print self.__BeeHand.listaGlobalNumero
                    print "Tablas Mongo:"
                    print self.__MongoHand.listaGlobalFecha
                    print self.__MongoHand.listaGlobalNumero

                #esperar entre escrituras
                try:
                    time.sleep(self.__tiempo)
                except:
                    if self.__debug:
                        print "Uploader.upload(): sleep interrumpido!"

        print "Uploader.upload(): saliendo..."
    

    #Función que genera un proceso que ejecuta la función
    #upload() de esta misma clase en segundo plano.
    def lanzar(self):
        #proceso que será el uploader.
        #si solo pasamos un parametro como argumento (args),
        #tendremos que poner una coma detras de el, que es la
        #forma de decir que es una tupla de un solo elemento.
        #Sin esta coma (',') la creación del proceso falla
        #self.proceso = Process(target=self.upload, args=(self.__debug,) )
        #self.proceso = Process(target=self.upload)
        self.proceso = Thread(target=self.upload)
        #inicio proceso
        print "Soy un hilo (RndUploader.upload())."
        self.proceso.start()
        #proceso.join()

    #Marca y espera que los procesos en segundo plano terminen su ejecución.
    def finalizar(self):
        self.__enable.value=False
        if self.__debug:
            print "Bandera activada para finalizar: " + str(self.__enable.value)
            print "Esperando para acabar"
        self.proceso.join()
        if self.__debug:
            print "el proceso ya ha acabado"

if __name__ == '__main__':
    print "Has ejecutado rnd_uploader.py"
    #clase = RndUploader(10, True)
    #clase.__enable.value=False
    #clase.finalizar()
