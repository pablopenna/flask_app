/*comprobaciones de nombre de usuario y contraseña para el registro
de usuarios*/
/*La comprobaciones del umbral se hacen con las funciones en enviarUmbral.js*/
/*Si todas las comprobaciones son satisfactorias, envío datos
al servidor (en caso de estar en la página /register) para crear usuario */
/* Emplea funciones del script respuestasServidor.js para interpretar 
las respuesta recibida del servidor. */

/*Precisa de los scripts 
    ->comprobaciones_umbral.js:
        Comprobaciones del umbral del usuario a crear.
    ->respuestasServidor.js:
        Interpretar la respuesta recibida por el servidor.
*/

/*Comprobar nombre de usuario introducido.
Debe tener una longitud mayor de 4 caracteres 
y no puede tener caracteres especiales.*/
function comprobarNombre(name)
{
    name=String(name)
    if(name.length<4)
    {
        //Debe tener más de 4 carácteres de longitud
        return 1
    }
    else
    {
        //No se permiten caracteres especiales
        //Expresion regular con los carácteres espciales
        var spchars = /[ !@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/;
        //Busco cualquier caracter especial en el nombre
        var n = name.search(spchars);
        //Si n no es -1, quiere decir que hay carácteres especiales en el
        //nombre
        console.log("caracter especial encontrado en: "+ n);
        if(n!=-1)
        {
            //console.log("El nombre de usuario contiene carácteres especiales")
            return 2
        }
        else
        {
            //nombre correcto
            return 0
        }
    }
}

/*Comprobar campos constraseñas.
Debe de ser de al menos 4 caracteres de longitud.
También debe haber dos campos para introducir las contraseñas
y estas deben coincidir.*/
function comprobarContrasena(pass, passRep)
{
    pass=String(pass)
    passRep=String(passRep)
    console.log('pass: ' + pass)
    console.log('passRep: ' + passRep)
    if(pass.length<4)
    {
        //console.log("La contraseña debe ser de mas de 3 carácteres de longitud");
        return 1
    }
    if(pass==passRep)
    {
        //console.log('contraseñas coinciden!');
        return 0;
    }
    else
    {
        //console.log('contraseñas NO coinciden!');
        return 2;

    }
}


function mostrarComprobacionNombre(res1)
{
    if(res1==1)
    {
        mostrarAlerta("El nombre de usuario debe ser de al menos 4 carácteres de longitud");

    }
    else if(res1==2)
    {
        mostrarAlerta("El nombre de usuario contiene carácteres especiales")

    }
}

function mostrarComprobacionContrasenna(res2)
{
    if(res2==1)
    {
        mostrarAlerta("La contraseña debe ser de al menos 4 carácteres de longitud");
    }
    else if(res2==2)
    {
        mostrarAlerta('Las contraseñas NO coinciden!');
    }
}


//--------------------------


/*

REGISTRO

*/
//EN DESUSO.
//Se utilizaba cuando se empleaba un botón y no un form.
/*Comprobación específica para la página del registro (register.html).
Comprueba todos los campos.
Si están todos bien, llama a la función $.post() para
enviar datos al servidor.*/
function comprobarRegistro(name,pass,passRep,umbral)
{
    var res1=comprobarNombre(name);
    //muestro mensaje de resultado de comprobar nombre usuario
    mostrarComprobacionNombre(res1)

    var res2=comprobarContrasena(pass,passRep);
    //muestro mensaje de resultado de comprobar contraseña
    mostrarComprobacionContrasenna(res2)
    
    var res3=comprobarUmbral(umbral);
    //muestro mensaje de resultado de comprobar umbral
    mostrarComprobacionUmbral(res3)
    //Actualizo umbral, ya que comprobarUmbral() parsea
    //el umbral.P.ej: 12,12 -> 12.12
    var umbral=res3

    if(res1==0 && res2==0 && res3<=100)
    {
        //Datos a enviar
        var datos='username='+name+"&"+'password='+pass+"&"+'umbral='+umbral;
        //Hago el post a la misma direccion en la que estoy
        var url = window.location.href;
        //Envio datos al server.
        $.post(url,datos,function(e)
        {
            //respuestasServidor.js
            //mostrarRespuestaServidor(e)
            
            interpretarRespuestaServidor(e,
            interpretarRespuestaRegistro,
            mostrarMensajeRegistro);
        }      
        );
    }
}


//Funciones para interpretacion de la respuesta del server.
//Requeridos por la funcion interpretarRespuestaServidor()
//en respuestasServidor.js

/*  
Dado el número de retorno obtenido de la funcion
crear usuario del servidor, indicamos si el proceso
de crear el usuario se ha realizado con éxito.
    Codigos:
        #-> -1 : tipos de argumentos no válidos
        #-> -2 : tipo de umbral no válido
        #-> -3 : la longitud del usuario y la contraseña
        #no son superiores a 4 caracteres.
        #-> -4 : El nombre 'None' no está permitido.
        #-> -5 : El nombre de usuario ya existe.
        #-> -6 : No hay conexion con mongoDb
*/
function interpretarRespuestaRegistro(n)
{
    //n recibido es String
    n=parseInt(n)
    pasar=false;
    switch(n)
    {
        case 0:
            //msg="El usuario se ha creado satisfactoriamente."
            pasar = true;
            break;
        case -1:
            //msg="Tipos de datos de Usuario y/o contraseña no validos."
            break;
        case -2:
            //msg="tipo de dato de umbral no válido."
            break;
        case -3:
            //msg="la longitud del usuario y la contraseña no son superiores a 4 caracteres."
            break;
        case -4:
            //msg= "El nombre 'None' no está permitido."
            break;
        case -5:
            //msg= "El nombre de usuario ya existe."
            break;
        case -6:
            //msg= "No hay conexion con mongoDB."
            break;
    }
    console.log("DEBERIA PASAR: " + pasar);
    return pasar;
}


/*  
Dado el número de retorno obtenido de la funcion
crear usuario del servidor, mostramos mensaje al cliente.
    Codigos:
        #-> -1 : tipos de argumentos no válidos
        #-> -2 : tipo de umbral no válido
        #-> -3 : la longitud del usuario y la contraseña
        #no son superiores a 4 caracteres.
        #-> -4 : El nombre 'None' no está permitido.
        #-> -5 : El nombre de usuario ya existe.
        #-> -6 : No hay conexion con mongoDb
*/
function mostrarMensajeRegistro(n)
{
    var msg="placeholder"
    //n recibido es String
    n=parseInt(n)
    switch(n)
    {
        case 0:
            msg="El usuario se ha creado satisfactoriamente."
            break;
        case -1:
            msg="Tipos de datos de Usuario y/o contraseña no validos."
            break;
        case -2:
            msg="tipo de dato de umbral no válido."
            break;
        case -3:
            msg="la longitud del usuario y la contraseña no son superiores a 4 caracteres."
            break;
        case -4:
            msg= "El nombre 'None' no está permitido."
            break;
        case -5:
            msg= "El nombre de usuario ya existe."
            break;
        case -6:
            msg= "No hay conexion con mongoDB."
            break;
    }
    mostrarAlerta(msg)
    return msg
}

//----------------------------------------------

/*Similar a comrpobarRegistro(), pero en vez de un boton, empleando
un formulario. Aun así, debo recibir los datos para poder parsearlos.
Como argumento extra recibe selectForm que debe ser una cadena que
se pueda utilizar como selector en JQuery para seleccionar el formulario*/
function comprobarRegistroForm(selectForm)
{
    $(selectForm).submit(function(e)
    {
        //Obtengo en lista datos una lista de pares de datos
        //con nombre del campo y su valor
        //[{ name: "user", value: "test" },{ name: "pass", value: "1234" }]
        //listaDatos[0]['name'] ==> 'user'
        var listaDatos = $(selectForm).serializeArray();
        console.log("Los datos del form:");
        console.log(listaDatos);
        
        //Comprobaciones. Itero a través de listaDatos.
        //Dependiendo del valor obtenido en 'name', que 
        //indicará el campo que estamos tratando,
        //haremos una comprobación u otra.

        //Damos valores por defecto que no pasen las comprobaciones.
        var name = "";
        var pass = "";
        var passRep = "";
        var umbral = NaN;
        for(i in listaDatos)
        {
            var actual = listaDatos[i]['name'];
            console.log("Actual: " + actual );
            switch(actual)
            {
                case "username":
                    console.log("Se ha asignado name");
                    name = listaDatos[i]['value']
                    break;
                case "password":
                    console.log("Se ha asignado pass");
                    pass = listaDatos[i]['value']
                    break;
                case "passRep":
                    console.log("Se ha asignado passRep");
                    passRep = listaDatos[i]['value']
                    break;
                case "umbral":
                    console.log("Se ha asignado umbral");
                    umbral = listaDatos[i]['value']
                    break;
            }
        }
        console.log("user: " + name);
        console.log("pass: " + pass);
        console.log("passRep: " + passRep);
        console.log("umbral: " + umbral);
        
        var res1=comprobarNombre(name);
        //muestro mensaje de resultado de comprobar nombre usuario
        mostrarComprobacionNombre(res1)

        var res2=comprobarContrasena(pass,passRep);
        //muestro mensaje de resultado de comprobar contraseña
        mostrarComprobacionContrasenna(res2)
        
        var res3=comprobarUmbral(umbral);
        //muestro mensaje de resultado de comprobar umbral
        mostrarComprobacionUmbral(res3)
        //Actualizo umbral, ya que comprobarUmbral() parsea
        //el umbral.P.ej: 12,12 -> 12.12
        var umbral=res3

        if(res1==0 && res2==0 && res3<=100)
        {
            console.log('Enviar Campos...')
            //Datos a enviar. Los obtengo del form, aunque en principio
            //deberían ser iguales.
            //var datos = $(selectForm).serialize();
            //Lo hago a mano porque la variable umbral ha podido ser parseada.
            //Si obtengo los datos directamente con serialize() el umbral no es
            //tratado.
            var datos='username='+name+"&"+'password='+pass+"&"+'umbral='+umbral;
            //Hago el post a la misma direccion en la que estoy.
            //Mejor la obtengo del formulario
            //var url = window.location.href;
            var url = $(selectForm).attr('action');
            //Envio datos al server.
            console.log("url: " + url);
            console.log("datos: " + datos);
            $.post(url,datos,function(e)
            {
                //respuestasServidor.js
                interpretarRespuestaServidor(e,
                interpretarRespuestaRegistro,
                mostrarMensajeRegistro);
            }, 'json');

        }
        //Evitamos el comportamiento por defecto del form, de
        //forma que no envía por su cuenta el formulario al servidor
        e.preventDefault();
    });
}
