# 📈 SalesPulse: E-Commerce Intelligence Dashboard

SalesPulse is a production-grade retail data analytics dashboard built with **Python**, **Streamlit**, **Pandas**, and **Plotly**. It demonstrates the **Data Pipeline Pattern**, high-performance memory caching via `@st.cache_data`, and interactive visual analytics.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│             Presentation Layer (Streamlit)             │
│   • Executive KPI Scorecards with Delta Indicators     │
│   • Multi-Dimensional Dynamic Filter Panel (Sidebar)   │
│   • Interactive Plotly Charts (Trend, Donut, Bars)     │
│   • Searchable Data Table with CSV Export              │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│              Caching & State Layer                     │
│   • @st.cache_data memoization of master transactions  │
│   • Sub-millisecond reactive slicing                   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│          Domain & Pipeline Engine (data_pipeline.py)   │
│   • Vectorized data transformations & feature engineering│
│   • Time-series resampling (Weekly / Monthly)          │
│   • Dimensional group-by aggregations (Pandas)         │
│   • Period-over-period delta growth calculations       │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart

1. **Install Dependencies**:
   ```bash
   pip install streamlit pandas plotly
   ```

2. **Run the Dashboard**:
   ```bash
   streamlit run app.py
   ```

3. **Open in Browser**:
   Navigate to `http://localhost:8501`.
