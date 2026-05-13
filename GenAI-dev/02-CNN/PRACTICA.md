### **Caso de Estudio: Modelo de Red Neuronal Convolucional para el Reconocimiento de Dígitos**
---

## **1. Business Case Discovery**

### **1.1 Contexto del Negocio y Antecedentes**  
Una importante compañía de envíos ha decidido modernizar su sistema de ruteo de correspondencia, paquetes y encomiendas. Actualmente, el proceso de clasificación se realiza de manera semi-automática y con intervención manual, lo que ocasiona demoras y errores en la entrega.  
El negocio ha identificado que el reconocimiento automático de los dígitos que componen el código postal en los paquetes puede agilizar el proceso y reducir costos operativos, mejorando la satisfacción del cliente.

### **1.2 Objetivo del Proyecto**  
El propósito es desarrollar un sistema de reconocimiento de dígitos basado en un modelo de red neuronal convolucional que:
- Identifique correctamente los dígitos del código postal en imágenes de paquetes.
- Automatice el ruteo y la clasificación en función del código postal.

### **1.4 Métricas de Éxito**  
- **Precisión (Accuracy):** Porcentaje de dígitos reconocidos correctamente en cada imagen.  
- **Tiempo de Inferencia:** Tiempo requerido para procesar cada imagen, clave para aplicaciones en tiempo real.  
- **Número de Parámetros:** Comparación de la eficiencia del modelo, evaluando la complejidad y capacidad de generalización.  

### **1.5 Desafíos y Consideraciones**  
- **Calidad y Variabilidad de las Imágenes:** Diferentes condiciones de iluminación, ángulos y ruido pueden dificultar la clasificación.  
- **Overfitting y Underfitting:** Balancear la complejidad del modelo para que no se adapte excesivamente a las muestras de entrenamiento.  

---

## **2. Data Processing**

### **2.1 Dataset para Entrenamiento**  
Para este caso de estudio, utilizaremos el dataset **MNIST** (Modified National Institute of Standards and Technology), que contiene **70,000 imágenes en escala de grises (28x28 píxeles) de dígitos manuscritos (0-9)**. Este conjunto de datos es ampliamente utilizado para tareas de clasificación de imágenes y servirá como base para entrenar nuestro modelo de reconocimiento de dígitos en códigos postales.  

Los alumnos podrán acceder a este dataset a través de bibliotecas como **TensorFlow/Keras (`tf.keras.datasets.mnist`)** o descargarlo desde plataformas como **Kaggle**.

### **2.2 Análisis Exploratorio y Visualización**  
Para comprender la naturaleza de los datos, el alumno deberá:

- Visualizar múltiples muestras de dígitos en diferentes formatos.
    - Agrupa imágenes por clase y observa si algunos dígitos están representados con mayor frecuencia que otros.

- Utilizar histogramas y diagramas de dispersión para analizar la distribución de las clases.
    - Utiliza histogramas para ver cuántas imágenes hay de cada número (0-9).
    - ¿Hay clases con más imágenes que otras? Si sí, esto podría afectar el entrenamiento del modelo.
    - Si hay desbalance, considera técnicas como oversampling o augmentation focalizado.

- Detectar posibles anomalías o sesgos en la distribución de imágenes.
    - Busca imágenes mal etiquetadas o con baja calidad (dígitos borrosos, con ruido o mal escritos).
    - Errores comunes:
        Imágenes corruptas (píxeles aleatorios).
        Dígitos mal centrados o rotados.
        Etiquetas incorrectas (ej: un "5" etiquetado como "6").
    - Piensa en estrategias para manejar estos datos: ¿Deben ser eliminados o corregidos?

### **2.3 Limpieza y Preprocesamiento de Imágenes**  

El dataset **MNIST** ya viene preprocesado en gran medida, pero es importante asegurarse de que los datos estén en el formato adecuado antes de entrenar la red neuronal.  

- **Redimensionamiento y Normalización:** No es necesario cambiar el tamaño de las imágenes, ya que todas tienen una resolución uniforme de **28x28 píxeles**. Sin embargo, los valores de los píxeles están en el rango **[0, 255]**, por lo que se debe normalizar dividiendo por **255** para escalarlos al rango **[0,1]**, lo que ayuda a estabilizar el entrenamiento del modelo.  

- **Aumento de Datos:** Aunque MNIST es un dataset bien equilibrado, agregar **data augmentation** puede mejorar la generalización del modelo. Se recomienda aplicar transformaciones como **rotaciones, traslaciones, zoom y cambios de brillo** para simular variaciones en la escritura de los dígitos y hacer el modelo más robusto.  

- **Conversión de Formatos:** Las imágenes están en escala de grises y se almacenan como matrices NumPy. Para que sean procesadas correctamente por una CNN en Keras/TensorFlow, es necesario asegurarse de que tengan la forma adecuada **(n_samples, 28, 28, 1)**, añadiendo una dimensión de canal (`reshape(-1, 28, 28, 1)`) si es necesario.

### **2.4 División de Datos: Entrenamiento, Validación y Test**  
- Dividir el dataset en tres conjuntos: entrenamiento (70%), validación (15%) y prueba (15%).  
- Garantizar que cada conjunto mantenga la misma distribución de clases para evitar sesgos en la evaluación. 

---

## **3. Model Planning**

### **3.1 Definición del Problema y Enfoque**  
- **Tipo de Problema:** Clasificación de imágenes, donde cada imagen representa un dígito del 0 al 9.  
- **Objetivo:** Lograr una alta precisión en la identificación de dígitos, minimizando errores que puedan afectar el ruteo de paquetes.

### **3.2 Propuesta de trabajo**
El objetivo es construir una CNN funcional para clasificación de dígitos y dejarla lista para ser evaluada con el dataset MNIST.

### **3.3 Criterios de entrenamiento**
- Preparar correctamente los datos para que tengan la forma adecuada para una CNN.
- Entrenar el modelo con un flujo claro de train/validación/test.
- Monitorizar métricas durante el entrenamiento para detectar sobreajuste o underfitting.

### **3.4 Función de pérdida y evaluación**
- **Función de pérdida:** usar entropía cruzada categórica (`categorical_crossentropy`) o su variante equivalente según la codificación de etiquetas.
- **Evaluación:** medir precisión y loss, y analizar la matriz de confusión y ejemplos de error.

---

## **4. Model Building and Selection**

### **4.1 Construcción y entrenamiento**
El alumno deberá implementar la CNN y entrenarla sobre MNIST, cuidando el preprocesado, la validación y la estabilidad del aprendizaje.

### **4.2 Validación y análisis**
- **Número de épocas y batch size:** comenzar con valores moderados y observar la evolución de loss y accuracy.
- **Monitoreo de métricas:** revisar el comportamiento en entrenamiento y validación.
- **Early Stopping:** usarlo si el entrenamiento empieza a degradar la validación.

### **4.3 Selección del modelo final**
Seleccionar la configuración que mejor generalice y documentar por qué se eligió.

---

## **5. Presentación de Resultados**

### **5.1 Análisis Cuantitativo de las Métricas**  
El alumno deberá presentar los resultados obtenidos en función de:
- **Precisión (Accuracy):** Porcentaje de dígitos correctamente clasificados.  
- **Loss y Entropía Cruzada:** Evolución durante el entrenamiento y validación.  
- **Comportamiento del modelo:** resultados en train, validación y test.

### **5.2 Visualización de Resultados**  
- **Curvas de Entrenamiento y Validación:** Graficar la evolución de la pérdida y precisión a lo largo de las épocas para detectar sobreajuste o convergencia inadecuada.
- **Matriz de Confusión:** Visualizar la distribución de aciertos y errores entre las 10 clases para identificar dígitos que podrían confundirse.
- **Análisis de Errores:** Mostrar ejemplos de imágenes mal clasificadas e investigar las posibles causas (calidad de imagen, ambigüedad, etc.).

### **5.3 Comparativa y Reflexión Crítica**  
- Discutir si el modelo generaliza bien o si muestra sobreajuste.
- Analizar el equilibrio entre precisión, robustez y coste de inferencia.
- Proponer posibles mejoras futuras de forma razonada.

---

## **6. Deployment**

### **6.1 Serialización y Almacenamiento del Modelo**  
- **Guardado del Modelo:** El alumno deberá guardar el modelo final en un formato adecuado (por ejemplo, `.h5` o `.keras`) para facilitar su reutilización.

### **6.2 Desarrollo de una API para Inferencia**  
- **Implementación de un Servicio Web:** Crear un endpoint (por ejemplo, utilizando Flask o FastAPI) que reciba imágenes de paquetes y devuelva la predicción del dígito.  
- **Pequeña interfaz:** proponer un front sencillo para subir imágenes y mostrar la predicción, por ejemplo con **Streamlit** o una alternativa similar. Aquí podéis ser creativos e inventaros casos de uso posibles y aplicaciones útiles.
- **Optimización para Producción:** Asegurarse de que el servicio se ejecute de manera eficiente y sea fácil de desplegar.

### **6.3 Pruebas y Validación en Entorno Real**  
- **Pruebas de Integración:** Realizar pruebas con imágenes reales de paquetes para evaluar la robustez del modelo en condiciones operativas.

---

### **Conclusión**  
La problemática del reconocimiento de dígitos en códigos postales no solo refuerza el conocimiento en redes neuronales convolucionales, sino que también invita a explorar la importancia de la experimentación, la validación y la integración del sistema en un flujo de trabajo productivo. Se espera que cada alumno justifique sus elecciones, documente su proceso y proponga mejoras basadas en sus hallazgos experimentales.
