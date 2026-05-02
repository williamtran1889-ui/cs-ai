import os
import keras
from keras import layers
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, regularizers
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from flax.nnx import optimizer
from warnings import filters
import os, pathlib
from keras.utils import image_dataset_from_directory

keras.utils.set_random_seed(0)
np.random.seed(0)
Batch_size = 64
Epochs = 50
L2_Reg = 1e-4
test_size = 0.2

#loading the data

def load_har_uci_dataset(base_path):
  x_train = np.loadtxt(os.path.join(base_path, "train", "X_train.txt"))
  x_test = np.loadtxt(os.path.join(base_path, "test", "X_test.txt"))

  y_train = np.loadtxt(os.path.join(base_path, "train", "y_train.txt")).astype(int) - 1
  y_test = np.loadtxt(os.path.join(base_path, "test", "y_test.txt")).astype(int) - 1

#HAR has 561 features, treated as 1 timestep
  x_train = x_train.reshape((x_train.shape[0], 1, x_train.shape[1]))
  x_test = x_test.reshape((x_test.shape[0], 1, x_test.shape[1]))

  return x_train, y_train, x_test, y_test


#Setting correct path

har_base_path = "UCI HAR Dataset"
print("Files in HAR folder:", os.listdir(har_base_path))

#load data
x_train, y_train, x_test, y_test = load_har_uci_dataset(har_base_path)

print("Train shape:", x_train.shape)
print("Test shape:", x_test.shape)

#Standardize features

scaler = StandardScaler()

x_train_2d = x_train.reshape(-1, x_train.shape[-1])
x_test_2d = x_test.reshape(-1, x_test.shape[-1])

scaler.fit(x_train_2d)

x_train = scaler.transform(x_train_2d).reshape(x_train.shape)
x_test = scaler.transform(x_test_2d).reshape(x_test.shape)

num_classes = len(np.unique(y_train))
timesteps = x_train.shape[1]
num_features = x_train.shape[2]

print("Timesteps:", timesteps)
print("Features:", num_features)
print("Classes:", num_classes)



#Building LSTM Model
def build_lstm():
  inputs = keras.Input(shape=(timesteps, num_features))

  x = layers.LSTM(64, return_sequences = True)(inputs)
  x = layers.Dropout(0.5)(x)

  x = layers.LSTM(64)(x)
  x = layers.Dropout(0.5)(x)

  x = layers.Dense(64, activation = "relu")(x)
  x = layers.Dropout(0.5)(x)

  outputs = layers.Dense(num_classes, activation = "softmax")(x)

  model = keras.Model(inputs, outputs)
  model.compile(
      optimizer = keras.optimizers.Adam(),
      loss = "sparse_categorical_crossentropy",
      metrics = ["accuracy"]
  )
  return model


#Buidling a CNN model
def build_cnn():
  inputs = keras.Input(shape=(timesteps, num_features)) # Corrected keras.Inputs to keras.Input

  x = layers.Conv1D(64, 1, activation = "relu")(inputs) # Corrected indentation and used 'inputs' variable
  x = layers.Conv1D(128, 1, activation = "relu")(x)
  x = layers.Flatten()(x)

  x = layers.Dense(128, activation = "relu")(x)
  x = layers.Dropout(0.5)(x)

  outputs = layers.Dense(num_classes, activation = "softmax")(x)

  model = keras.Model(inputs, outputs)
  model.compile(
      optimizer = keras.optimizers.Adam(),
      loss = "sparse_categorical_crossentropy",
      metrics = ["accuracy"]
  )
  return model


  #Train LSTM
lstm_model = build_lstm()
print("\nTraining LSTM...")
history_lstm = lstm_model.fit(
    x_train, y_train,
    epochs = 30,
    batch_size = 32,
    validation_split = 0.1,
    verbose = 1
)

#Train CNN

cnn_model = build_cnn()
print("\nTraining CNN...")
history_cnn = cnn_model.fit(
    x_train, y_train,
    epochs=30,
    batch_size=32,
    validation_split=0.1,
    verbose=1
)


#evaluating both models
def evaluate(model, name):
  print(f"\n===== {name} Evaluation =====")
  loss, acc = model.evaluate(x_test, y_test, verbose = 0)
  print(f"{name} Accuracy: {acc:.4f}")

  y_pred = np.argmax(model.predict(x_test), axis = 1)

  print("\nClassification Report:")
  print(classification_report(y_test, y_pred))

  print("\nConfusion Matrix:")
  print(confusion_matrix(y_test, y_pred))

  evaluate(lstm_model, "LSTM")
  evaluate(cnn_model, "CNN")
