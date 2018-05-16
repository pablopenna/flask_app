# -*- coding: utf-8 -*-
"""
Clase encargada de guardar y consultar los usuarios registrados
mediante OAuht almacenados en MongoDB.

Estructura de los documentos almacenando usuarios en MongoDB
Campos:
    -> username: nombre de usuario
    -> email: email del usuario (opcional).
    -> id: identificador único del usuario.
    -> provider: Entidad de la que he obtenido los datos (Google).
    -> umbral: Si se obtiene un numero aleatorio
        superior al umbral,se le
        notificara al usuario.

Hereda de la clase de guardar los usarios en MongoDB ya que muchas
de las operaciones a realizar son similares o iguales.

IMPORTANTE: Reconsiderar si en vez de heredar de UserManager es preferible que
heredo de MongoBasic, de forma que parte de su funcionalidad se la relegue a
User Manager, ya que él ya la tiene implementada y de forma que se tengan los
datos de usuarios en el mismo sitio.
"""
from numbers import Number
from mongo_user import UserManager
import date_handler

class OAuthUserManager(UserManager):
    
    #Constructor
    #Recibiré una instancia de UserManager, de forma que en vez de tener listas
    #de sesión locales, trabajaré con las de la instancia de UserManager
    #recibida como parámetro, de forma que tendré toda la información de las
    #sesiones unificada.
    def __init__(self, coleccionUsuariosOauth="usuariosOauth", mongoUserManager=None, debug=False):
    #def __init__(self, coleccionUsuariosOauth):
        #Igual que el de el padre pero cambiando la coleccion empleada
        #UserManager.__init__(self,coleccionUsuariosOauth,debug)
        UserManager.__init__(self,coleccionUsuariosOauth,debug)
        #Añadimos los campos que no tenia el padre
        #En el dicc recibido, puede ser la entrada ['iss']
        # The ID Token contains a set of claims about the authentication
        # session, including an identifier for the user (sub), the identifier
        # for the identity provider who issued the token (iss), and the
        # identifier of the client for which this token was created (aud).
        #Obtener el proveedor del campo 'iss'
        self.campoProveedor="provider"
        self.campoEmail="email"
        self.campoName="name"
        #
        #SOBRESCRIBO el campo 'username' por el campo id,
        #ya que en mongo_user se empleaba este campo como
        #clave primaria y en esta clase empleare la id como
        #clave primaria, como si fuera el nombre de usuario.
        #
        #El campo campoUsername se emplea en funciones como
        #modUmbral para cambiar el umbral del usuario. Como esas
        #funciones no necesito cambiarlas, sobrescribiré el campo
        #de forma que se utilice el id para buscar el usuario y no
        #el username.
        self.campoUsername="id"
        #Los campos que siguen igual son los de password (no se
        #utiliza) y el de umbral.

        #trabajaré con las listas de sesiones de la instancia de UserManager
        #recibida como parámetro, de forma que tendré toda la información de las
        #sesiones unificada.
        self.mongoUserManager=mongoUserManager

        #debug
        self.debug=debug


    """
     _                _          ___     _                            _   
    | |    ___   __ _(_)_ __    ( _ )   | |    ___   __ _  ___  _   _| |_ 
    | |   / _ \ / _` | | '_ \   / _ \/\ | |   / _ \ / _` |/ _ \| | | | __|
    | |__| (_) | (_| | | | | | | (_>  < | |__| (_) | (_| | (_) | |_| | |_ 
    |_____\___/ \__, |_|_| |_|  \___/\/ |_____\___/ \__, |\___/ \__,_|\__|
                |___/                               |___/                 
    """
    #Login.
    #El usuario se identificará por su id única aportada
    #por el proveedor.
    #Verifica si el usuario indicado existe.
    #De ser así, devuelve el valor de la cookie para la 
    #sesion actual del usuario.
    #Si el usuario indicado no existe, devolveremos -1.
    #Solo indicamos el nombre de usuario ya que 
    #la autenticación ya se ha realizado mediante OAuth
    def login(self, userId):
        #COMPROBACION DE DATOS
        if not isinstance(userId, str):
            if self.debug:
                print "El usuario debe ser una cadena!"
            return -2
    
        #LOGIN
        res=self.checkUserName(userId)
        if res:
            #existe usuario.
            #genero cookie sesion.
            cookie=self.genCookieVal(userId)
            #Añado a la lista de sesiones de OAuth
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
                print "MONGO_OAUTH: "
                print "Sesion iniciada. Id: " + str(cookie)
                print "Caducidad Sesion:"
                fechaAct=date_handler.getDatetimeMs()
                print "Tiempo Actual: " + str(fechaAct)
                print "conversion: " + \
                str(date_handler.msToDatetime(fechaAct))
                cadcook=self.listaCaducidad[cookie]
                print "Caducidad Cookie: " + str(cadcook)
                print "conversion: " + \
                str(date_handler.msToDatetime(cadcook))
            return cookie
        else:
            print "MONGO_OAUTH:"
            print "No existe el usuario con el que se ha intentado iniciar sesión."
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
    
    #Si al hacer login, obtenemos como resultado -1, indicando que el usuario no
    #existe. En el caso de OAuth, indica que esa cuenta no esta registrada en la
    #apliación, por lo que debemos registrarla y asignarle un umbral.
    #
    #Se devuelve 'la id del usuario creado' en caso de creación satisfactoria,
    #-1 si no se pudo crear usuario (ya existia) y -2 si los datos 
    #introducidos no tiene tipos válidos.
    def createUser(self, userProvider, userId, userMail, userName, userUmbral):
        #Compruebo Datos
        if not isinstance(userProvider, str):
            if self.debug:
                print "MONGOOAUTH - createUser():"
                print "El proveedor debe ser tipo string!"
            return -2
        if not isinstance(userId, str):
            if self.debug:
                print "MONGOOAUTH - createUser():"
                print "La id del usuario debe ser tipo string!"
            return -2
        if not isinstance(userMail, str):
            if self.debug:
                print "MONGOOAUTH - createUser():"
                print "El email del usuario debe ser tipo string!"
            return -2
        if not isinstance(userName, str):
            if self.debug:
                print "MONGOOAUTH - createUser():"
                print "El nombre del usuario debe ser tipo string!"
            return -2
        if not isinstance(userUmbral, Number):
            if self.debug:
                print "MONGOOAUTH - createUser():"
                print "El umbral debe ser tipo Number !"
            return -2

        #Crear usuario
        res=self.checkUserName(userId)
        if res:
            #Usuario ya registrado
            if self.debug:
                print "MONGOOAUTH - createUser():"
                print "El usuario ya existe!"
            return -1
        else:
            #Usuario no existe, lo creamos
            datos = {self.campoProveedor : userProvider, \
            self.campoUsername : userId, \
            self.campoEmail : userMail, \
            self.campoName : userName, \
            self.campoUmbral : userUmbral}
            #escribimos
            res=self.escribir(datos)
            #---
            if self.debug:
                print "MONGOOAUTH- createuser()"
                print "created:"
                print res
            #---
            #return res
            return userId



    """
      ____            _    _           
     / ___|___   ___ | | _(_) ___  ___ 
    | |   / _ \ / _ \| |/ / |/ _ \/ __|
    | |__| (_) | (_) |   <| |  __/\__ \
     \____\___/ \___/|_|\_\_|\___||___/
                                        
    """

    """
     __  __ _              _                        
    |  \/  (_)___  ___ ___| | __ _ _ __   ___  ___  
    | |\/| | / __|/ __/ _ \ |/ _` | '_ \ / _ \/ _ \ 
    | |  | | \__ \ (_|  __/ | (_| | | | |  __/ (_) |
    |_|  |_|_|___/\___\___|_|\__,_|_| |_|\___|\___/ 
    """

    #@OVERRIDE
    #EXISTE USUARIO, ie. ¿ESTA REGISTRADO?. No cambio el nombre para hacer override, de
    #forma que cuando ejecute funciones heredadas del padre y estas
    #llamen a la funcion checkUserName, se ejecute esta funcion y 
    #no la original del padre.
    #Dado el id de un usuario comprueba si existe en la base de
    #datos de MongoDB.
    #Devuelve True si existe ese Id de Usuario,
    #False en caso contrario
    def checkUserName(self, userId):
        condicion={self.campoUsername : userId}
        """
        if self.debug:
            print condicion
        """
        res=self.leerCondicion(condicion)
        #DEBUG
        if self.debug:
            print "MongoOauth - Con Id: " + str(userId)
            print "Se ha encontrado el usuario: "
            print "COLECCION: " +str(self.coleccion)
            for doc in res:
                print doc
            #muy importante
            res.rewind()
        #Si se ha encontrado usuario. res.count() sera > 0.
        if res.count() > 0:
            return res
        else:
            return None


    #GETTERS
    #Dado el id obtener nombre, email o proveedor.
    def getUserData(self, userId ,data):
        #Formato de argumentos
        userId=str(userId)
        data=str(data)

        #Obtenemos el diccionario con los datos del usuario.
        #Consultamos MongoDB utilizando la funcion checkUsername
        res = self.checkUserName(userId)
        #SI existe el usuario, buscamos los datos
        if res:
            for doc in res:
                val = doc[data]

                #DEBUG
                if self.debug:
                    print "MONGOOAUTH - getUserData"
                    print "CAMPO: " + str(data)
                    print "VALOR: " + str(val)

                return val
        else:
            return None
    #envolvedores
    """
    self.campoProveedor="provider"
    self.campoEmail="email"
    self.campoName="name"
    """
    def getUserName(self, userId):
        return self.getUserData(userId, self.campoName)
    def getUserMail(self, userId):
        return self.getUserData(userId, self.campoEmail)
    def getUserProvider(self, userId):
        return self.getUserData(userId, self.campoProveedor)
        
    
                                                 
if __name__ == "__main__":
    u = OAuthUserManager()
    print "db: " + str(u.client)
    print "coleccion: " + u.coleccion
    u.leer()
    yes=raw_input("Borrar todo?")
    if yes == "Y":
        todo=dict()
        u.borrar(todo)

