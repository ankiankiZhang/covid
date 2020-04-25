# -*- coding: utf-8 -*-
"""code.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1NXZHE10R9oXeaP7BbdZiel43LtvBeuG7
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('time_series_covid19_confirmed_US.csv')

df_by_state = df.groupby("Province_State").sum()

df_by_state_clean = df_by_state.sort_values(by = '4/23/20', ).drop(['UID', 'code3', 'FIPS', 'Lat', 'Long_'], axis = 1)

df = pd.DataFrame({
   'NY': df_by_state_clean.iloc[-1],
   'NJ': df_by_state_clean.iloc[-2],
   'MA': df_by_state_clean.iloc[-3],
   })
lines = df.plot.line()

date = df_by_state_clean.columns
df_by_state_clean = df_by_state_clean.transpose()
#df_by_state_clean['date'] = date 
df_by_state_clean

def root_mean_squared_log_error(y_true, y_pred, smooth=1):
  return np.sqrt((1 / len(y_true)) * np.sum((np.log(y_true + smooth) - np.log(y_pred + smooth)) ** 2))

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, LSTM, Dense, Activation, Dropout
from sklearn.model_selection import train_test_split
from sklearn.model_selection import TimeSeriesSplit

def by_state(state,data):
  return data[state]

def clean_zeros(data):
  return data[data != 0]

data_ny = by_state('New York', df_by_state_clean)
data_ny = clean_zeros(data_ny)

#train test split
train_ny,test_ny= train_test_split(data_ny,test_size=0.2, random_state=42,shuffle=False)

from pandas import DataFrame

test_ny.values

def difference(dataset, interval = 1):
  diff = []
  for i in range(interval, len(dataset)):
    value = dataset[i] - dataset[i - interval]
    diff.append(value)
  return np.array(diff)

def inverse_diff(orginal_data, prediction):
  length = len(prediction)
  return prediction + orginal_data[-length:]

#build input data
def supervised_train_set(data,back_step):
     df = DataFrame()
     x = data
     length = x.shape[0]
     df['t'] = [x[i] for i in range(x.shape[0])]
     x=df['t'].values
     cols=list()
     for i in range(1, back_step+1):
       df['t+1'] = df['t'].shift(i)
       cols.append(df['t+1'])
     agg = pd.concat(cols,axis=1)
     agg.fillna(0, inplace = True)
     y=agg.values
     x = x.reshape(x.shape[0],1)
     len_X = length-back_step-2
     X=np.zeros((len_X,back_step,1))
     Y=np.zeros((len_X,back_step))
     for i in range(len_X):
        X[i] = x[i:i+back_step]
        Y[i] = y[i]

     return X,Y

back_step = 1
train = difference(train_ny)
test = difference(test_ny)
print(train.shape)
#trainX, trainY = supervised_train_set(train, back_step)
#testX, testY = supervised_train_set(test, back_step)

print(trainX.shape)
print(trainY.shape)
print(testX.shape)
print(testY.shape)

from sklearn.preprocessing import MinMaxScaler

def scale(train, test):
  scaler = MinMaxScaler(feature_range=(-1,1))
  shape_train = train.shape
  shape_test = test.shape
  train = train.reshape(train.shape[0],train.shape[1])
  scaler.fit(train)
  train_scaled = scaler.transform(train)
  train_scaled = train_scaled.reshape(shape_train)
  test = test.reshape(test.shape[0],test.shape[1])
  test_scaled = scaler.transform(test)
  test_scaled = test_scaled.reshape(shape_test)
  return scaler, train_scaled, test_scaled

def invert_scale(scaler, X, value):
  new_row = [x for x in X] + [value]
  array = np.array(new_row)
  array = array.reshape(1, len(array))
  inverted = scaler.inverse_transform(array)
  return inverted[0,-1]

scalerX, trainX_scaled, testX_scaled = scale(trainX, testX)
scalerY, trainY_scaled, testY_scaled = scale(trainY, testY)

print(trainX_scaled.shape)

from keras import optimizers
from sklearn.metrics import mean_squared_error
from keras.models import load_model
from keras.optimizers import adam
from tensorflow.keras.optimizers import Adam

def fit_lstm_model(trainX,trainY,testX,testY,batch_size, epochs, verbose, input_shape=(back_step,1)):
    model = Sequential()
    model.add(LSTM(64,activation='relu',return_sequences=True, input_shape=input_shape))
    model.add(LSTM(32, activation='relu'))
    model.add(Dense(back_step))
    myOptimizer = Adam(lr=0.01, beta_1=0.9, beta_2=0.999, epsilon=0.01, decay=0.0)
    model.compile(loss='mean_squared_error', optimizer=myOptimizer)
    model.fit(trainX, trainY, epochs=epochs,validation_data=(testX,testY), batch_size=batch_size, verbose=verbose)
    return model

lstm_model = fit_lstm_model(trainX_scaled,trainY_scaled,testX_scaled,testY_scaled,batch_size=1, epochs=1000, verbose = 1, input_shape=(back_step,1))

pred = lstm_model.predict(testX_scaled, batch_size = 1)

x_input = testX_scaled
index = testX.shape[0]
result = test_ny[-index:].copy()
for i in range(1,9):
  pred = lstm_model.predict(x_input, batch_size = 1) 
  inverted = scalerX.inverse_transform(pred)
  result = result + inverted.sum(axis = 1)
  print(result[-1])
  pred = pred.reshape(pred.shape[0],pred.shape[1] ,1)
  x_input = pred

test_ny

