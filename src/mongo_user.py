# -*- coding: utf-8 -*-
"""
Clase encargada de guardar y consultar los usuarios
almacenados en MongoDB.

Estructura de los documentos almacenando usuarios en MongoDB
Campos:
    -> username: nombre de usuario
    -> password: hash de la contraseña
    -> session_id: valor que almacenaremos temporalmente como
    id de la sesion (cookie) del usuario. Tendrá un valor por defecto
    que indicara que no hay sesion abierta (-1).
    En lugar de eso, mantendré una variable (diccionario?) durante tiempo
    de ejecucion (similiar a listaGlobalNumero) donde mantendré los paresde
    valores de usuario y el valor de su cookie para la sesión actual
    -> umbral: Si se obtiene un numero aleatorio superior al umbral,se le
    notificara al usuario.

"""
#Para generacion de cookies
#base64
import base64
#para hashes
from passlib.hash import pbkdf2_sha256
#para numeros aleatorios
import random
#para manejo de fechas
import date_handler
#Para comprobar si un objeto es un numero de cualq tipo
from numbers import Number
#Herencia de la clase base para trabajar con MongoDB
from mongo_base import MongoBasic
#logging
import logging
from log_handler import setup_log, setStreamMode

class UserManager(MongoBasic):
    
    #Variables de clase, ya que estas deben ser comunes para todas la instancias
    #Diccionario que contiene los pares de cookie y usuario correspondiente
    listaSesiones=dict()
    #Contiene los pares de cookies y fecha de caducidad.     
    listaCaducidad=dict()

    #Contructor
    def __init__(self, coleccionUsuarios="usuariosFlask", debug=False):
        MongoBasic.__init__(self, coleccionUsuarios, 1024, debug)

        self.campoUsername="username"
        self.campoPassword="password"
        #self.campoSession="session_id"
        self.campoUmbral="umbral"
        #Debug
        self.debug=True
        #Las cookies caducan despus de que pase le tiempo indicado 
        #por tiempoCaducidad (contiene escapcio de tiempo en ms, 
        #p.ej. 30 minutos) sin ser utilizadas.
        self.tiempoCaducidad=date_handler.minToMs(30)
        #
        #Al ser diccionarios, las variables de la instancia
        #referenciarán a las de la clase, por lo que al modificar
        #las listas de la instancia realmente estaré modificando las 
        #de la clase
        self.listaSesiones = UserManager.listaSesiones
        self.listaCaducidad = UserManager.listaCaducidad


    """
     _                _          ___     _                            _   
    | |    ___   __ _(_)_ __    ( _ )   | |    ___   __ _  ___  _   _| |_ 
    | |   / _ \ / _` | | '_ \   / _ \/\ | |   / _ \ / _` |/ _ \| | | | __|
    | |__| (_) | (_| | | | | | | (_>  < | |__| (_) | (_| | (_) | |_| | |_ 
    |_____\___/ \__, |_|_| |_|  \___/\/ |_____\___/ \__, |\___/ \__,_|\__|
                |___/                               |___/                 
    """

    #Login.
    #Verifica si el usuario indicado existe.
    #De ser así, devuelve el valor de la cookie para la 
    #sesion actual del usuario.
    #Si el usuario indicado no existe, o la contraseña es
    #incorrecta, devolveremos -1.
    def login(self, userId, userPass):
        #COMPROBACIONES DATOS
        #compruebao tipos de datos
        if not isinstance(userId, str) or not isinstance(userPass, str):
            if self.debug:
                logging.debug("El usuario y la contraseña deben ser strings!")
            return -1
        #compruebo longitud nbombre y pass
        if len(userId) < 4 or len(userPass) < 4:
            if self.debug:
                logging.debug("El usuario y la contraseña deben" + \
                "ser de al menos 4 chars de longitud!")
            return -1

        #REALIZO OPERACIONES PARA LOGIN
        #comprobamos que el nombre del usuario existe
        if self.checkUserName(userId):
            #Existe usuario.
            #Ahora comprobamos contraseña
            correctPass = self.checkPassword(userId, userPass)

            if correctPass:
                #Usuario y contraseña correctos.
                #Añado el valor de la cookie y el usuario al
                #que corresponde.
                cookie=self.genCookieVal(userId)
                entrada={cookie : userId}
                self.listaSesiones.update(entrada)
                #Consultando la cookie en este diccionario, nos
                #devolverá el usuario al que pertenece la cookie
                #---
                #Añado también la información de caducidad de la cookie
                #Será la fecha actual + tiempoCaducidad.
                #Es decir, si tiempoCaducidad son 30 minutos,
                #caducidad contendrá la fecha de dentro de 30 minutos.
                caducidad=date_handler.getDatetimeMs() + self.tiempoCaducidad
                entrada2={cookie : caducidad}
                self.listaCaducidad.update(entrada2)
                if self.debug:
                    logging.debug("MONGO_USER:")
                    logging.debug("Sesion iniciada. Id: " + str(cookie))
                    logging.debug("Caducidad Sesion:")
                    fechaAct=date_handler.getDatetimeMs()
                    logging.debug("Tiempo Actual: " + str(fechaAct))
                    logging.debug("conversion: " + \
                    str(date_handler.msToDatetime(fechaAct)))
                    cadcook=self.listaCaducidad[cookie]
                    logging.debug("Caducidad Cookie: " + str(cadcook))
                    logging.debug("conversion: " + \
                    str(date_handler.msToDatetime(cadcook)))
                return cookie

            else:
                if self.debug:
                    logging.debug("Contraseña incorrecta!")
                return -1
        else:
            if self.debug:
                logging.debug("No existe el usuario: " + userId)
            return -1
    #Logout.
    #Devuelve 0 si se ha salido de la sesión correctamente
    #Devuelve -1 si la sesiónde la que se ha intentado salir
    #no existía.
    def logout(self, cookieVal):
        if self.debug:
            logging.debug("MongoUser - logout()")
            logging.debug("clase :" + str(self.__class__.__name__))
            logging.debug("mostrando listas:")
            logging.debug(self.listaSesiones)
            logging.debug(self.listaCaducidad)
        try:
            del self.listaSesiones[cookieVal]
            del self.listaCaducidad[cookieVal]
            if self.debug:
                logging.debug("Se ha salido de la sesion " + cookieVal)
            return 0
        except KeyError as e:
            if self.debug:
                logging.info("Se ha intentado salir de una sesion que no existe: "\
                + str(cookieVal))
            return -1

    """
      ____                _          ___     ____       _      _       
     / ___|_ __ ___  __ _| |_ ___   ( _ )   |  _ \  ___| | ___| |_ ___ 
    | |   | '__/ _ \/ _` | __/ _ \  / _ \/\ | | | |/ _ \ |/ _ \ __/ _ \
    | |___| | |  __/ (_| | ||  __/ | (_>  < | |_| |  __/ |  __/ ||  __/
     \____|_|  \___|\__,_|\__\___|  \___/\/ |____/ \___|_|\___|\__\___

     _   _                   
    | | | |___  ___ _ __ ___ 
    | | | / __|/ _ \ '__/ __|
    | |_| \__ \  __/ |  \__ \
     \___/|___/\___|_|  |___/
                     
    """
    #Crea un usuario con los parámetros especificados.
    #El valor 101 para umbral significa que el usuario no quiere
    #notificaciones para umbrales.
    #Valores de retorno:
    #
    #->  0 : Creación de usuario correcta
    #-> -1 : tipos de argumentos no válidos
    #-> -2 : tipo de umbral no válido
    #-> -3 : la longitud del usuario y la contraseña
    #no son superiores a 4 caracteres.
    #-> -4 : El nombre 'None' no está permitido.
    #-> -5 : El nombre de usuario ya existe.
    #-> -6 : No hay conexion con mongoDb
    def createUser(self, userId, userPass, umbral=101):
        #COMPROBACIONES DATOS
        #compruebo tipos de datos
        if not isinstance(userId, str) or not isinstance(userPass, str):
            if self.debug:
                logging.debug("El usuario y la contraseña deben ser strings!")
            return -1
        if not isinstance(umbral, Number):
            if self.debug:
                logging.debug("El umbral debe ser un número!")
            return -2
        #CREAR USUARIO    
        #compruebo longitud nombre y pass
        if len(userId) < 4 or len(userPass) < 4:
            if self.debug:
                logging.debug("El usuario y la contraseña deben" + \
                "ser de al menos 4 chars de longitud!")
            return -3
        #Nombre 'None' no permitido, ya que si accedemos a 
        #la aplicación sin haber hecho login, el nombre de 
        #usuario actual figurará como 'None'.
        #if userId=="None":
        if userId.lower()=="none":
            if self.debug:
                logging.debug("MongoUser - createUser()")
                logging.debug("El nombre de usuario 'None' no esta permitido.")
            return -4
                
        #comprobamos que el nombre del usuario existe
        if self.checkUserName(userId):
            #Existe usuario. Aborto misión.
            if self.debug:
                logging.debug("MongoUser - createUser()")
                logging.debug("El usuario ya existe")
            #Salimos con código de error.
            return -5
        else:
            #generamos has de la contraseña, que sera lo que guardemos.
            hashPass = pbkdf2_sha256.hash(userPass)
            #generamos los datos del usuario a almacenar
            datos = {self.campoUsername : userId , \
            self.campoPassword : hashPass, \
            self.campoUmbral : umbral}
            #escribimos datos de usuario en MongoDB
            res=self.escribir(datos)
            #Si no hay conexion con Mongo, res sera 'None'
            if res == None:
                if self.debug:
                    logging.debug("MongoUser - createUser() - escribir()")
                    logging.debug("La escritura retorna None.")
                    logging.debug("No hay conexion?")
                return -6
            #Retornamos 0 en caso de escciribir los datos satisfactoriamente
            return res

    #Borrar Usuario.
    #Verifica si el usuario indicado existe.
    #Si el usuario indicado no existe, o la contraseña es
    #incorrecta, devolveremos -1.
    def deleteUser(self, userId, userPass, force=False):
        
        #COMPROBACIONES DE LO DATOS
        #compruebo tipos de datos
        if not isinstance(userId, str) or not isinstance(userPass, str):
            if self.debug:
                logging.debug("El usuario y la contraseña deben ser strings!")
            return -1
        #compruebo longitud nombre y pass
        if len(userId) < 1 or len(userPass) < 1:
            if self.debug:
                logging.debug("El usuario y la contraseña deben" + \
                "ser de al menos 1 char de longitud!")
            return -1

        #BORRAR USUARIO
        #comprobamos que el nombre del usuario existe
        res=self.checkUserName(userId)
        if res:
            #Existe usuario.
            #Ahora comprobamos contraseña
            correctPass = self.checkPassword(userId, userPass)
            if correctPass or force:
                if force and not correctPass:
                    logging.warning("Forzando borrado de cuenta!")
                #Usuario y contraseña correctos.
                #Procedo a borrar el usuario
                condicion={self.campoUsername : userId}
                res=self.borrar(condicion)
                return res

            else:
                if self.debug:
                    logging.debug("Contraseña incorrecta!")
                return -1
        else:
            if self.debug:
                logging.debug("No existe el usuario: " + userId)
            return -1

    """
      ____            _    _           
     / ___|___   ___ | | _(_) ___  ___ 
    | |   / _ \ / _ \| |/ / |/ _ \/ __|
    | |__| (_) | (_) |   <| |  __/\__ \
     \____\___/ \___/|_|\_\_|\___||___/
                                        
    """
    #Genera valor "aleatorio" para una cookie.
    def genCookieVal(self, userId):
        repetir=True
        while repetir:
            #La cookie consistirá en el nombre de usuario seguido de un
            #número aleatorio entre 0 y 1000000.
            #Todo ello será codificado en base64
            sufijo = random.randint(0,1000000)
            cookiePre=str(userId)+str(sufijo)
            #DEBUG
            if self.debug:
                logging.debug("Cookie sin codificar: " + str(cookiePre))
            cookie=base64.b64encode(cookiePre)
            #HAY QUE COMPROBAR SI YA EXISTE ESE VALOR EN LISTASESIONES
            #Si ya existe, generop de nuevo la clave
            #SI no (lo normal), salgo y retorono la cookie
            if not (cookie in self.listaSesiones):
                repetir=False
        #retorno la cookie
        return cookie
    
    #CONSULTAR USUARIO
    #Se nos dará el valor de una cookie y se devolverá
    #a qué usuario pertenece.
    #Si no pertenece, devuelvo None
    def getCookieUserName(self, sessionId):
        try:
            sessionId=str(sessionId)
            return self.listaSesiones[sessionId]
        except KeyError:
            return None
    
    #-------------------------
    #-------CADUCIDAD---------
    #-------------------------

    #Refrescar uso de la cookie. Restrasamos su
    #fecha de caducidad.
    def refreshCookie(self, cookieVal):
        if self.debug:
            logging.debug("MongoUser - refreshCookie()")
            logging.debug("Actualizando caducidad cookie - " + str(cookieVal))
            logging.debug("Antes: " + str(self.listaCaducidad))

        if cookieVal in self.listaCaducidad:
            #Actualiza la fecha para dentro de tiempoCaducidad minutos
            caducidad=date_handler.getDatetimeMs() + self.tiempoCaducidad
            self.listaCaducidad[cookieVal]=caducidad

        if self.debug:
            logging.debug("Despues: " + str(self.listaCaducidad))
    

    #Recorre la lista de todas las cookies y borra las que hayan caducado
    def deleteExpiredCookies(self):
        #Si encuentro una cookie a borrar, borrare la entrada
        #en los diccionarios cuya clave sea ese valor de cookie
        #mediante el método logout(). Al hacer esto, cambiare el tamaño
        #de los diccionario listaCaducidad  mientras itero por él.
        #Esto producirá un error de ejecución.
        #Para evitarlo, crearé una copia del diccionario y utilizaré
        #las claves de esta copia para iterar a través del original
        for value in self.listaCaducidad.copy():
            #Si el tiempo actual es mayor que la fecha
            #de caducidad, significa que ha caducado la cookie
            fechaAct=date_handler.getDatetimeMs()
            cadTemp=self.listaCaducidad[value]
            #DEBUG
            if self.debug:
                logging.debug("MongoUser - deleteExpiredCookies()")
                logging.debug("Fecha act: " + str(fechaAct))
                logging.debug("tipo: " + str(type(fechaAct)))
                logging.debug("Fecha cad: " + str(cadTemp))
                logging.debug("tipo: " + str(type(cadTemp)))

            if fechaAct >= cadTemp:
                if self.debug:
                    logging.debug("La cookie con valor " + str(value) \
                    + " ha caducado.")

                #Si ha caducado, realizo un logout().
                #Esto borrará el valor de la cookie
                #de listaSesiones y listaCaducidad
                self.logout(value)

    #Se comprueba solo si la cookie del usuario especificado ha caducado,
    #en lugar de recorrer la lista de todas las sesiones
    #Devuelvo True si borro la cookie
    #Devuelvo False si la cookie no ha caducado
    def deleteExpiredCookie(self, sessionId):
        #OBtengo fecha de caducidad para la sesion indicada
        try:
            cadTemp=self.listaCaducidad[sessionId]
        except KeyError:
            #Si no existe la cookie no ha caducado,
            #devuelvo False ya que no he borrado nada
            return False
        #Obtengo fecha actual para comparar
        fechaAct=date_handler.getDatetimeMs()
        #DEBUG
        if self.debug:
            logging.debug("MongoUser - deleteExpiredCookie()")
            logging.debug("Fecha act: " + str(fechaAct))
            logging.debug("Fecha cad: " + str(cadTemp))

        #Comparo fechas. Si la actual es mayor que la de caducidad, borro
        #la cookie de session.
        if fechaAct >= cadTemp:
            if self.debug:
                nombre = self.getCookieUserName(sessionId)
                logging.debug("La cookie del usuario " + nombre 
                + " ha caducado.")
            #Elimino cookie
            self.logout(sessionId)
            #Devuelvo True si borro la cookie
            return True
        #Devuelvo False si la cookie no ha caducado
        return False


    #Se llamará a una función cuando se registre el uso de una cookie.
    #Se borrarán las cookies que han caducado y acto seguido, si no
    #ha caducado la cookie empleada, se prologará su fecha de caducidad.
    def checkCookieStatus(self, cookieVal):
        if self.debug:
            logging.debug("Comprobando caducidad de cookie.")
        #self.deleteExpiredCookies()
        sehaborrado = self.deleteExpiredCookie(cookieVal)
        #Si se ha borrado, no actualizo
        if not sehaborrado:
            if self.debug:
                logging.debug("Actualizando caducidad de la cookie - " 
                + str(cookieVal))
            self.refreshCookie(cookieVal)

        #Indico si se ha borrado la cookie o no
        return sehaborrado
                
    
    """
     __  __ _              _                        
    |  \/  (_)___  ___ ___| | __ _ _ __   ___  ___  
    | |\/| | / __|/ __/ _ \ |/ _` | '_ \ / _ \/ _ \ 
    | |  | | \__ \ (_|  __/ | (_| | | | |  __/ (_) |
    |_|  |_|_|___/\___\___|_|\__,_|_| |_|\___|\___/ 
    """
    #EXISTE USUARIO
    #Dado el nombre de un usuario comprueba si existe en la base de
    #datos de MongoDB.
    #Devuelve True si existe ese Nombre de Usuario,
    #False en caso contrario
    def checkUserName(self, userId):
        condicion={self.campoUsername : userId}
        if self.debug:
            logging.debug(condicion)
        res=self.leerCondicion(condicion)
        #Si no hay conexion a la base de datos MongoDB,
        #leerCondicion retorna None. Por lo que si este es el
        #caso, retornamos None.
        if res==None:
            if self.debug:
                logging.debug("MongoUser - checkuserName()")
                logging.debug("La búsqueda retorna None.")
                logging.debug("No hay conexion?")
            return None
        #DEBUG
        if self.debug:
            logging.debug("Con user: " + str(userId))
            logging.debug("Se ha encontrado el usuario: ")
            for doc in res:
                logging.debug(doc)
            #muy importante
            res.rewind()
        #Si se ha encontrado usuario. res.count() sera > 0.
        #return res.count() > 0
        #Mejor deulevo res de forma que pueda obtener los datos del usuario.
        #Seguiré pudiendo utilizar este resultado en un if
        if res.count()>0:
            return res
        else:
            return None
    
    #COMPROBAR CONTRASEÑA
    #dado usuario y contraseña, se comprueba si la contraseña aportada
    #es correcta
    def checkPassword(self, userId, userPass):
        #No utilizo checkUsername porque necesito leer
        #la contraseña del suario encontrado.
        condicion={self.campoUsername : userId}
        res=self.leerCondicion(condicion, userId)
        #Si no hay conexion a la base de datos MongoDB,
        #leerCondicion retorna None. Por lo que si este es el
        #caso, retornamos False (lo equivalente a que la contraseña
        #no sea correcta).
        if res==None:
            if self.debug:
                logging.debug("MongoUser - checkPassword()")
                logging.debug("La búsqueda retorna None.")
                logging.debug("No hay conexion?")
            return False
        #Si se ha encontrado usuario. res.count() sera > 0.
        if res.count() > 0:
            #Ahora comprobamos contraseña
            #Obtenemos el has de la contraseña iterando por el resultado.
            #Si lo hacemos de otra manera, p.ej. res[0]["pass"]
            #nos devolverá u'pass' en lugar de pass
            hashPass=None
            for doc in res:
                hashPass=doc[self.campoPassword]
            
            #Comparamos la contraseña introducida con el
            #hash de la contraseña verdadera
            correctPass = pbkdf2_sha256.verify(userPass , hashPass)
            #DEBUG
            if self.debug:
                logging.debug("hash pass buena: " + str(hashPass))
                logging.debug("pass introducida: " + str(userPass))
                logging.debug("Coinciden? : " + str(correctPass))
            return correctPass
        #Si no existe el usuario, retorno False
        else:
            return False
        

    #Modificar valor umbral para un usuario
    #Dado un usuario y un valor para el umbral, asignaremos ese
    #umbral al usuario. El umbral debe estar comprendido entre 0 y 100.
    def modUmbral(self, userId, umbral):
        #COMPROBACION TIPOS
        #nombre usuario valido
        if not ( isinstance(userId, str) and len(userId)>0 ):
            if self.debug:
                logging.debug("modUmbral : Tipo y/o longitud"
                + "de usuario no válido.")
            return -1
        #umbral valido
        if not ( isinstance(umbral, Number) and umbral >=-100 \
        and umbral <=100 ):
            if self.debug:
                logging.debug("modUmbral : Tipo y/o valor de umbral no válido."+ \
                "El valor del umbral debe estar comprendido entre -100 y 100.")
            return -1
        
        #MODIFICACION UMBRAL
        res = self.checkUserName(userId)
        if res:
            #Existe usuario. Procedo a modificar el umbral.
            #creo la asignacion y la condicion
            condicion={self.campoUsername : userId}
            asignacion={ self.campoUmbral : umbral }
            #Actualizo valor en MongoDB
            res = self.actualizar(condicion, asignacion)
            return res
        else:
            if self.debug:
                logging.debug("No se ha encontrado el usuario: " + str(userId))
            return -1
            

    #OBTENER UMBRAL
    #Dado un usuario, devuelve su umbral. 101 es el valor por defecto si 
    #el usuario no ha especificado ninguno.
    #valores de retorno:
    #-> 102: El usuario es 'None'. Es el valor que se obtiene cuando no se ha
    #iniciado sesión
    #-> 103: Indica que el nombre de usuario recibido no es válido, ya sea por tipo
    #(no string) o longitud.
    #-> 104: El usuario indicado no se ha encontrado en la base de datos.
    def getUmbral(self, userId):
        #COMPROBACION TIPOS
        #nombre usuario valido
        if userId == None:
            if self.debug:
                logging.debug("getUmbral() : Usuario 'None'. Inicia sesión.")
            return 102
        #nombre usuario valido
        if not ( isinstance(userId, str) and len(userId)>0 ):
            if self.debug:
                logging.debug("getUmbral() : Tipo y/o longitud" 
                + "de usuario no válido.")
            return 103

        #DEVOLVER UMBRAL
        #busco usuario indicado
        res = self.checkUserName(userId)
        if res:
            #Existe usuario. Procedo a leer el umbral.
            #
            #Nos quedamos con el umbral del ultimo usuario devuelto.
            #Aunque sólo debería devolverse uno.
            #Utilizo el for porque si no,
            #con res[0]['umbral'] me devuelve los datos con basura.
            for doc in res:
                umbral=doc['umbral']
            return umbral
        else:
            if self.debug:
                logging.debug("getUmbral() : No se ha encontrado el usuario: "
                + str(userId))
            return 104

            
if __name__ == "__main__":

    #Funcion privada para parsear strings a numeros
    def num(s):
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return None
    #----------------------------------------------
    #log
    setup_log()
    setStreamMode(logging.DEBUG)

    u = UserManager(debug=True)
    #u.deleteUser("test", "test")
    """
    logging.debug("Crear:")
    userr = raw_input("user: ")
    passs = raw_input("pass: ")
    u.createUser(userr, passs)
    umbrall = raw_input("umbral: ")
    umbrall=num(umbrall)
    res=u.modUmbral(userr, umbrall)
    logging.debug("modUmbral : " + str(res))
    """
    u.leer()

    logging.debug("Login:")
    userr = raw_input("user: ")
    passs = raw_input("pass: ")
    u.login(userr,passs)
    
    debug_str = raw_input("Borrar cuenta?[Y\N]: ")
    debug_str2 = raw_input("Forzar?[Y\N]: ")

    if debug_str == "Y" or debug_str == "y":
        debug = True
    else:
        debug = False
    if debug_str2 == "Y" or debug_str == "y":
        forzar = True
    else:
        forzar = False
    if debug:
        u.deleteUser(userr,passs,forzar)
    
    """
    u.leer()
    userr = raw_input("user: ")
    umbrall = raw_input("umbral: ")
    umbrall=num(umbrall)
    #userr = 123
    #umbrall = 12L
    res=u.modUmbral(userr, umbrall)
    logging.debug("modUmbral : " + str(res))
    """
    u.endConn()
