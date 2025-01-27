# Estructura a Seguir

## Logica a seguir

### PASOS ANTES DE RECIBIR EL QUERY

- Usuario sube el documento
- Se escanea en busca de informacion que se le pueda proporcionar al LLM para que pueda realizar consultas sobre este
- Se hace un preprocesamiento del documento en caso de que lo requiera usando el LLM

### SE RECIBE LA QUEERY DEL USUARIO

- Comienza la idea de SKELETON OF THOGHT, se le pide al LLM que rompa la query del usuario en tareas simples atomicas
- Es posible que se considere proveer al LLM de algunas estructuras de reportes completos para que entienda correctamente
que es lo que se deseea
- Por cada una de las tareas atomicas, se le pide al LLM que genere el codigo correspondiente en python ya sea usando Pandas u
otra libreria para este fin
- Se parsea la respuesta del LLM para obtener el codigo correspondiente
- Se ejecuta el codigo en cuestion y se le vuelve a enviar al LLM para que genere una respuesta a dicha tarea atomica
- Se unen todas las respuestas de las tareas atomicas y se le pide al LLM que genere una respuesta final basandose en todos esos
datos

### LUEGO DE TENER LA RESPUESTA DEL LLM

- Luego de obtener la respuesta del LLM se cosidera por cada aspecto si una grafica o tabla podria ayudar a un mejor entendimiento del
punto en cuestion
- En dependencia de la respuesta del LLM se genera un codigo altair para generar las graficas o tablas para los resultados
- Se renderiza todo el contenido en una web usando streamlit

## LLM a utilizar

Para la eleccion del modelo de lenguaje a utilizar nos basamos en la premisa de que el autor no posee una capacidad de computo suficiente como para ejecutar localmente ningun modelo de lenguaje que tenga unos resultados lo suficientemente bueno que indiquen que pudieran servir para este objetivo. Dicho esto y dado que el objetivo de la presente investigacion se basa en los modelos opensources se va a utilizar una API gratuita que provee la pagina groq.com, con dicha API podremos acceder a una gran variedad de modelos opensources que nos permitira contrastar resultados entre distintos modelos y asi analizar cual de estos seria una mejor opcion para la generacion de reportes automatizados de esta forma.

Entre los modelos que ofrece la interfaz de Groq se encuntran gemma2-9b-it desarrollado por Google, varios de la familia LLama, desarrollados por Meta, tambien conocida por Facebook, y Mixtral-8x7b desarrollado por Mixtral AI, los cuales son los modelos opensource que mayor capacidades han mostrados hasta la fecha segun varios test. Entre estos el mejores resultados ha mostrado es el modelo mas reciente de la familia LLama, el modelo llama-3.3-70b-versatile.

## Interfaz Grafica del Usuario

Para la interfaz grafica que se le mostrara al usuario utilizaremos las facilidades que os brinda streamlit, una libreria que ha recibido un aumento significativos de usuria por la facilidades que esta brinda para la creacion de una interfaz web con bastante calidad usuando unas pocas lineas de codigo. Esta ademas posee una gran comunidad que le agrega funcionalidades constantemente en dependencia de la demanda y utilizacion actual de la misma. Aprovechando esta caracteristicas como por ejemplo una interfaz de chat que permite realizar un chatbot como las primeras versiones de chatgpt, asi como la posibilidad de renderizar codigo altair en los mismos elementos lo que nos facilitaria la idea de mostrar los resultados finales al usuario en cuestion

## Informacion que se puede proporcionar al LLM

### Informacion del Documento

Cuando recibimos el documento, empezamos a analizar los valores para que el LLM entienda de que datos nos estamos refiriendo y en consecuencia podemos generar el código necesario para poder realizar las consultas sobre estos, para ello vamos a recolectar y darle al LLM información de los siguientes aspectos:

- Nombre de las columnas
- Tipos de las columnas
- Valores mínimos y máximos por columnas
- Cantidad de valores únicos por columnas
- Valores faltantes por columnas
- Ejemplos de filas representativas

### Preprocesado del Documento

El preprocesado se realizará mediante el LLM si es necesario.

**Tipos de Preprocesamiento:**

- **Limpieza de Datos:** Corrección de errores, eliminación de duplicados, manejo de valores faltantes.
- **Normalización:** Ajuste de escalas y formatos de datos.
- **Transformación:** Creación de nuevas variables o modificación de las existentes.

## Como generar el reporte

Para generar el reporte lo mas certero posible no podremos simplemente pedirle al LLM que nos responda a la pregunta del usuario en cuestion, ya que esta dara una respuesta totalmente creativa dado que no le estamos proporcionando los datos del documento al LLM. Por lo tanto, vamos a tener que generar paso a paso junto con el llm, o ir giando al LLM para que este vaya generando codigo python capaz de acceder a los datos para que la respuesta del LLM tenga una ase respaldada. Tengase en cuenta tambien que los datos pueden ser de gran tamaño, por lo que no se le puede proveer al LLM de todos los datos en cuestion, dicho esto se nos abren dos posibles soluciones:

- Usar RAG, con una base de vectores y embbeding podremos hacer que el LLM solo tenga acceso a los datos que se encuentren en el espacio  de los embedidngs mas cercanos a la pregunta del usuario, pero esto no seria lo ideal ya que para cosultas generales como por ejemplo como se comportaron las ventas mensuales, es necesario acceder a todos los datos

- Usar un modelo de LLM de generacion de codigo capaz de acceder a los datos del documento, esto nos permitiria generar el reporte de una manera mas eficiente y con menos errores, aprovechando las capacidades de generacion de codigo de los LLM podriamos proveerle a este la estructura de los datos y ciertas reglas o comportamientos que debe seguir a la hora de generar el codigo para acceder a los datos que le sean necesarios para la respuesta.

Siguiendo esta ultima idea necesitamos descomponer el problema en tareas que nos permita seguir esos pasos.

Lo primero que necesitamos es que el modelo interprete la query del usuario y que establezca un esqueleto del reporte a generar con informacion que nos permita saber en cada seccion que datos se van a presentar y de que se va a hablar.

Luego, por cada seccion del esqueleto generado anteriormente necesitaos que el modelo genere la seccion, para ello dividimos la generacion en partes.

- primero se le pide que datos necesita para formular una respuesta (O una seccion en este caso) lo mejor posible, y si no cuenta con esos datos que genere un codigo python que permita acceder a estos datos en cuestion.
- una vez se tengan esos datos se le pregunta sobre la necesidad de incluir graficos, tablas u otras facilidades que posea altair para mejorar la presentacion de la informacion. En caso de que sea positivo que genere el codigo para esto
- una vez se tenga la informacion necesaria se le pide que genere la seccion con la informacion que se le haya proporcionado

QUe hacemos despues de que hayamos generado todas las secciones del reporte?
