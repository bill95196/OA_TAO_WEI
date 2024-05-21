import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error


if __name__ == '__main__':
    # Load and Prepare Data
    timeseries_data = pd.read_excel('../data/Assignment 3 - timeseries_data.xlsx')

    # Fill missing values with the mean of each column
    means = timeseries_data.mean(numeric_only=True)
    timeseries_data.fillna(means, inplace=True)

    # Feature Engineering
    timeseries_data['weekday'] = timeseries_data['DATETIME'].dt.weekday
    timeseries_data['hour'] = timeseries_data['DATETIME'].dt.hour
    timeseries_data['month'] = timeseries_data['DATETIME'].dt.month
    timeseries_data['day'] = timeseries_data['DATETIME'].dt.day
    timeseries_data['PEAKTYPE'] = timeseries_data['PEAKTYPE'].map({'OFFPEAK': 0, 'WEPEAK': 1, 'WDPEAK': 2})
  

    # Model Training and Evaluation
    X = timeseries_data.drop(['HB_NORTH (RTLMP)', 'PEAKTYPE', 'MONTH', 'DATETIME', 'MARKETDAY'], axis=1)
    y = timeseries_data['HB_NORTH (RTLMP)']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print(f'RMSE: {mean_squared_error(y_test, y_pred, squared=False)}')  # RMSE

    # Prediction and Visualization of Predicted Results
    timeseries_data['pred'] = model.predict(X)
    plt.figure(figsize=(14, 7))
    plt.plot(timeseries_data['DATETIME'], timeseries_data['HB_NORTH (RTLMP)'], label='RTLMP')
    plt.plot(timeseries_data['DATETIME'], timeseries_data['pred'], label='Prediction')
    plt.title('Comparison of Actual vs Predicted RTLMP Over Time')
    plt.xlabel('Date')
    plt.ylabel('RTLMP ($/MWh)')
    plt.legend()
    plt.show()
