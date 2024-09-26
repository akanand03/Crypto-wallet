
# Crypto Price Tracker
<img width="1680" alt="Screenshot 2024-09-26 at 2 40 06 PM" src="https://github.com/user-attachments/assets/ba9ce9da-b9b8-4bb4-89d0-ff3b83b71e35">



---

## 📊 Project Overview
Aimed at predicting cryptocurrency prices using historical data for enhanced market insights.

### Why Cryptocurrency?
- 📈 Maximize Profits in Volatile Markets
- 📉 Risk Management
- 💡 Strategic Investment
- 🌐 24/7 Market Dynamics

---

## 🔍 01 - Introduction
Dataset focused on **OPEN, CLOSE, HIGH, LOW** values of Bitcoin.

---

## 🛠️ 02 - Preprocessing
Missing values handled using multiple imputation techniques:

1. **Mean**: Filled with average values.
2. **Median**: Replaced with median values.
3. **Mode**: Used the most frequent value.
4. **Interpolation**: Estimated via linear predictions.
5. **Constant**: Applied a fixed value (50,000).
6. **Grouped Imputation**: Replaced using group-based averages.

---

## 📏 03 - SSE Evaluation
Evaluated methods using **Sum of Squared Errors (SSE)**:
- **Interpolation** yielded the lowest SSE, indicating higher accuracy.

---

## 🌐 04 - Frontend
Developed a Flask-based interactive web interface for tracking.
<img width="1680" alt="Screenshot 2024-09-26 at 2 40 29 PM" src="https://github.com/user-attachments/assets/1f32d214-02e2-44a1-8139-a21409271704">
<img width="1680" alt="Screenshot 2024-09-26 at 2 40 57 PM" src="https://github.com/user-attachments/assets/a26f71f2-fdc1-44cd-a814-2bfcdb75a1d0">
<img width="1680" alt="Screenshot 2024-09-26 at 2 41 16 PM" src="https://github.com/user-attachments/assets/9ce20a30-f950-4af5-b7e1-e0ae2dbfa9fe">

---

