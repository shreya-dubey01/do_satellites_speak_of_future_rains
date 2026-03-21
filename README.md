# do_satellites_speak_of_future_rains
Implements a Gradient Boosted (XGBoost) pipeline to estimate ground-level PM2.5 using INSAT-3DS Satellite AOD and ERA5 Reanalysis data, subject to data availability.

Key Features

    Spatial Scalability: Designed to generalize across the "North-South Urban Divide" using Lat/Lon coordinates rather than city-specific IDs.

    Dual-Mode Inference: Includes a Physical model (R2≈0.61) for data-void regions and an Operational model (R2≈0.92) for sensor-enabled nowcasting.
