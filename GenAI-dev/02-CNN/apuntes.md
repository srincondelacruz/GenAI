# Apuntes — CNN con Quick Draw

---

## Label Encoding

Las redes neuronales no entienden texto. No puede procesar `"smiley face"` directamente, necesita un número para saber qué clase es cada imagen.

| Texto | Número |
|-------|--------|
| `smiley face` | 0 |
| `face` | 1 |
| `flower` | 2 |
| `star` | 3 |
| `sun` | 4 |
| `cloud` | 5 |

Más adelante cuando el modelo prediga `2`, nosotros sabemos que significa `flower`. Por eso guardamos el diccionario `{0: 'smiley face', 1: 'face', ...}` — para traducir de vuelta el número al nombre en la interfaz web.

---

## Categorical Crossentropy

Es la **función de pérdida** que usamos para entrenar el modelo.

Durante el entrenamiento, el modelo predice una probabilidad para cada clase:

```
[0.05, 0.02, 0.80, 0.03, 0.08, 0.02]  → predice "flower" con 80% de confianza
```

La etiqueta real en one-hot es:
```
[0,    0,    1,    0,    0,    0   ]   → era "flower"
```

`categorical_crossentropy` mide cuánto se equivoca comparando esas dos distribuciones. Cuanto más cerca esté la predicción de la etiqueta real, menor es el error. El modelo aprende ajustando sus pesos para minimizar ese error en cada batch.

Se llama **categórica** porque hay más de 2 clases. Si solo hubiera 2 clases usaríamos `binary_crossentropy`.

---

## One-Hot Encoding

Convierte la etiqueta numérica en un vector binario de longitud igual al número de clases:

```
2  →  [0, 0, 1, 0, 0, 0]
```

Es necesario para usar `categorical_crossentropy`. Primero hacemos **label encoding** (número entero por clase) y luego **one-hot encoding** (vector binario).

---

## Preprocesamiento de imágenes

Tres transformaciones obligatorias antes de entrenar:

1. **Reshape** a `(n, 28, 28, 1)` — añadimos la dimensión de canal para que Keras interprete las imágenes como tensores. Las CNN esperan esta forma aunque las imágenes sean en escala de grises.
2. **Normalización** dividiendo entre 255 — escala los píxeles de `[0, 255]` a `[0, 1]`. Estabiliza el gradiente durante el entrenamiento.
3. **One-hot encoding** — convierte las etiquetas enteras a vectores binarios de longitud 6.

---

## Data Augmentation

Técnica para **generar variaciones artificiales** de las imágenes existentes durante el entrenamiento.

En lugar de tener siempre la misma imagen de una estrella, el modelo ve cada vez una versión ligeramente diferente:

```
Original  →  rotada 8°  →  desplazada  →  con zoom
   ★              ★              ★              ★
```

**¿Por qué hacerlo?**
Porque en la vida real nadie dibuja dos veces exactamente igual. Si el modelo solo ve dibujos perfectamente centrados y rectos, fallará cuando alguien dibuje una estrella inclinada o más grande.

**Transformaciones aplicadas:**
- `rotation_range=10` → rota hasta ±10 grados
- `width/height_shift_range=0.1` → desplaza hasta un 10% horizontal/vertical
- `zoom_range=0.1` → acerca o aleja hasta un 10%

**Importante:** no duplica el dataset en disco. El dataset original nunca se toca — `X_train` sigue siendo el mismo. El `ImageDataGenerator` actúa como una capa intermedia que en cada batch coge las imágenes originales, les aplica las transformaciones al vuelo y las pasa al modelo. Cuando el entrenamiento termina, esas imágenes modificadas desaparecen. Es como una forma de generar datos ficticios sin ensuciar el dataset.

---

## Arquitectura CNN — Explicación por capas

El modelo tiene **468.582 parámetros** en total.

### Bloque 1 — Extracción de rasgos básicos
```
conv2d        (None, 28, 28, 32)   320 params
conv2d_1      (None, 28, 28, 32)   9,248 params
max_pooling2d (None, 14, 14, 32)   0 params
dropout       (None, 14, 14, 32)   0 params
```

Las dos `Conv2D` con 32 filtros buscan rasgos simples: bordes, curvas, esquinas. La imagen sigue siendo 28×28 pero ahora tiene 32 "versiones", cada una detectando un rasgo distinto. El `MaxPooling` la reduce a la mitad (14×14) quedándose solo con lo más relevante. El `Dropout` apaga el 25% de neuronas aleatoriamente para evitar sobreajuste.

### Bloque 2 — Rasgos más complejos
```
conv2d_2      (None, 14, 14, 64)   18,496 params
conv2d_3      (None, 14, 14, 64)   36,928 params
max_pooling2d (None, 7, 7, 64)     0 params
dropout       (None, 7, 7, 64)     0 params
```

Ahora 64 filtros sobre imágenes ya reducidas. Combina los rasgos del bloque anterior para detectar formas más complejas: "círculo con puntos" → cara, "líneas que se cruzan" → estrella. Otro `MaxPooling` deja la imagen en 7×7.

### Clasificador
```
flatten       (None, 3136)         0 params
dense         (None, 128)          401,536 params  ← 85% de los parámetros
dense_1       (None, 6)            774 params
```

`Flatten` convierte la matriz 7×7×64 en un vector de 3136 números. La capa `Dense(128)` aprende combinaciones de todos esos rasgos. La última `Dense(6)` con `softmax` da la probabilidad de cada una de las 6 categorías.

**¿Por qué `Dense(128)` tiene el 85% de los parámetros?**
Porque conecta 3136 neuronas con 128, y eso son 3136×128 = 401.408 pesos. Las convoluciones son mucho más eficientes porque comparten pesos entre posiciones de la imagen.

### BatchNormalization
Aparece después de cada `Conv2D` y de la `Dense(128)`. Normaliza las activaciones entre capas, lo que acelera la convergencia y permite usar tasas de aprendizaje más altas sin que el entrenamiento se desestabilice.

### Parámetros entrenables vs no entrenables
- **467.942 entrenables** — pesos que el modelo ajusta durante el entrenamiento
- **640 no entrenables** — parámetros de `BatchNormalization` que solo normalizan, no aprenden

---

## Callbacks de entrenamiento

### EarlyStopping
Detiene el entrenamiento si `val_accuracy` no mejora en 10 épocas consecutivas y restaura los pesos del mejor epoch (`restore_best_weights=True`). Evita entrenar de más y ahorra tiempo.

### ReduceLROnPlateau
Reduce la tasa de aprendizaje a la mitad si `val_loss` no mejora en 5 épocas. Ayuda a "afinar" el modelo en fases tardías del entrenamiento sin necesidad de ajustar la LR manualmente.

---

## Cómo sabemos que el modelo generaliza bien

Comparando la accuracy en los tres splits. Si el modelo **sobreajusta** (memoriza en lugar de aprender), los números divergen mucho:

```
Train:      98%   ← aprende hasta el ruido
Validación: 80%   ← no sabe generalizar
Test:       79%   ← confirma que falla fuera del train
```

En nuestro modelo los números están muy cerca:

```
Train:      94.52%
Val:        93.61%   ← solo 0.9% menos
Test:       93.54%   ← casi idéntico a val
```

Una diferencia train→test de **~1%** indica que lo que aprendió en train le sirve igual de bien para imágenes que nunca ha visto. Eso es generalizar.

Las técnicas que lo consiguen:
- **Dropout** — apaga neuronas aleatoriamente, evita que el modelo dependa de caminos concretos
- **BatchNormalization** — estabiliza el aprendizaje época a época
- **Data augmentation** — el modelo nunca ve la misma imagen dos veces exactamente igual
- **EarlyStopping** — paró en época 40, antes de que empezara a memorizar

---

## Análisis de errores

Una vez evaluado el modelo, conviene mirar **qué ejemplos falla**, no solo cuántos.

El proceso es:
1. Comparar predicciones (`y_pred_int`) con etiquetas reales (`y_test_int`) y localizar los índices donde no coinciden.
2. Contar cuántos errores hay sobre el total del test set.
3. Visualizar una muestra aleatoria de esos errores mostrando para cada imagen: etiqueta real, lo que predijo el modelo y la confianza con la que se equivocó.

**¿Para qué sirve?**
Las métricas (accuracy, F1) dicen *cuánto* falla. El análisis de errores dice *por qué* falla. Ver el dibujo real que el modelo confundió permite distinguir entre:
- **Error razonable**: un `smiley face` sin sonrisa visible que parece un `face` — el modelo no tiene la culpa.
- **Error extraño**: una `star` clasificada como `cloud` — podría indicar un problema en los datos o en el modelo.

En nuestro caso, la mayoría de errores son `smiley face` ↔ `face` porque ambas categorías comparten la misma forma base (círculo + dos ojos) y la única diferencia, la boca, puede ser muy sutil en dibujos de 28×28 píxeles.

---

## Warmup del modelo Sequential

Un modelo `Sequential` en Keras es **perezoso**: no construye el grafo de cómputo interno hasta que procesa datos reales por primera vez.

Cuando guardas y cargas el modelo con `.keras`, la arquitectura y los pesos se restauran, pero el grafo de conexiones entre capas no se materializa hasta que el modelo recibe una entrada concreta. Hasta ese momento, `model.input` y `model.inputs` no tienen tensor definido.

Esto es un problema cuando quieres crear un modelo intermedio para extraer activaciones:

```python
# Falla si el modelo no ha sido llamado antes
activation_model = tf.keras.Model(
    inputs=model.inputs,
    outputs=[pool_layers[0].output, pool_layers[1].output]
)
```

La solución es hacer un **warmup** — pasar un array de ceros (el contenido no importa, solo la forma) antes de crear el modelo intermedio:

```python
model.predict(np.zeros((1, 28, 28, 1), dtype="float32"), verbose=0)
```

Esto fuerza una pasada completa, construye todos los tensores internos, y a partir de ese momento `model.inputs` devuelve el tensor de entrada real.

**¿Por qué no pasa con la API Funcional?**
Con `tf.keras.Model(inputs=..., outputs=...)` defines el grafo explícitamente desde el principio, por lo que los tensores siempre están definidos. Es una particularidad exclusiva de `Sequential`.
