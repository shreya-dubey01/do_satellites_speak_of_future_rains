The repository essentially compares two XGBoost models trained with a difference of 1 feature and how it affects their performance and real world application.

<H2> Model A: The Mechanistic Physical Model (R2≈0.62) </H2>  

- Purpose: Diagnostic and Generalizable Inference.
- Features: lat', 'lon', 'temp', 'blh', 'sp', 'wind_spd', 'rh', 'AOD',
    'hour_sin', 'hour_cos', 'is_weekend', 'month_sin', 'month_cos',
    'ventilation_index', 'inversion_strength', 'rh_aod_interaction',
    'wind_spd_3h_avg', 'blh_3h_avg', 'rh_3h_avg'
- Logic: This model is "History Blind." it identifies the exact atmospheric conditions (humidity, boundary layer height, satellite AOD) that cause PM2.5​ to exist.
- It can be used for "Zero-Shot" estimation in cities where no ground sensor has ever been installed, as it relies on universal physics rather than local persistence.
- High complexity. Because weather patterns are noisy, XGBoost builds a massive, intricate forest of trees to find the signal.

<H2> Model B: The Persistence Nowcasting Model (R2≈0.92) </H2>

- Purpose: Real-time Public Health Alerts.
- Features: lat', 'lon', 'temp', 'blh', 'sp', 'wind_spd', 'rh', 'AOD',
    'hour_sin', 'hour_cos', 'is_weekend', 'month_sin', 'month_cos',
    'ventilation_index', 'inversion_strength', 'rh_aod_interaction',
    'wind_spd_3h_avg', 'blh_3h_avg', 'rh_3h_avg', <b> 'pm25_lag1' </b>
- Logic: This model uses "Temporal Persistence." It knows that if it was smoky 60 minutes ago, it is likely smoky now. It uses the weather/satellite data as Correction Factors to the baseline.
- Extremely high accuracy for short-term (1-hour) forecasting.
- Low complexity. The "Lag" feature is so powerful that the trees are shallow and highly efficient, leading to a smaller size.

<b>Note on Model Architecture:</b> While Model B (with Lag) achieves higher accuracy (R2=0.92), it results in a significantly smaller serialized footprint compared to the Physical Model A (R2=0.61). This is due to the high mutual information between temporal lags and the target, allowing for lower tree complexity and higher information density per leaf node.
