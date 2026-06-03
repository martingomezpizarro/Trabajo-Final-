# Reporte de Filtros de Kalman

| Variable | ARIMA | Exógena | AIC | BIC | RMSE in-sample | Ljung-Box p-val |
|----------|-------|---------|-----|-----|----------------|-----------------|
| SE - Nivel (Mill. ARS) | (4, 0, 4) | Superavit primario | 2013.5 | 2064.6 | 0.00 | 0.2180 |
| PBI Nominal | (4, 1, 4) | EMAE | 2793.9 | 2846.4 | 0.00 | 0.7920 |
| PBI Constante | (4, 1, 4) | EMAE | 1639.4 | 1692.0 | 0.00 | 0.9083 |
| PBI USD | (4, 1, 4) | EMAE | 1785.3 | 1837.9 | 0.00 | 0.8386 |
| Total Cuenta Corriente | (4, 1, 1) | Saldo Comercial | 1157.1 | 1198.0 | 0.00 | 0.0207 |
| Total Cuenta Financiera | (1, 1, 4) | Saldo Comercial | 1163.3 | 1204.2 | 0.00 | 0.5716 |
| Deuda Externa Bruta Total | (4, 2, 0) | Reservas/PBI | 1529.1 | 1566.6 | 0.00 | 0.7794 |
| Vencimientos USD 1 anio | (0, 1, 4) | -- | 1373.2 | 1406.5 | 0.00 | 0.4542 |
| Vencimientos USD 2 anios | (0, 1, 4) | -- | 1379.0 | 1412.3 | 0.00 | 0.9466 |

---
*Estimado con `SARIMAX` de statsmodels, que utiliza el filtro de Kalman para la estimación de máxima verosimilitud.*