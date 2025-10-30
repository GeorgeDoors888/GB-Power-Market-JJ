def analyze_generation_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze generation patterns and calculate metrics including GW/GWh patterns"""
    # Convert MW to GW for clarity
    df["generation_gw"] = df["generation_mw"] / 1000

    # Calculate hourly energy in GWh
    df["energy_gwh"] = df["generation_gw"] * 1  # Since data is hourly

    # Weekly statistics
    weekly_stats = (
        df.resample("W", on="timestamp")
        .agg(
            {
                "generation_gw": ["min", "mean", "max", "std"],
                "energy_gwh": "sum",  # Total weekly energy
            }
        )
        .reset_index()
    )

    # Detect periods of zero generation
    zero_gen = df[df["generation_gw"] == 0].copy()
    zero_periods = []

    if not zero_gen.empty:
        zero_gen["period_start"] = zero_gen["timestamp"].diff() > pd.Timedelta(hours=1)
        period_starts = zero_gen[zero_gen["period_start"]]["timestamp"]
        period_ends = zero_gen[zero_gen["timestamp"].diff(-1) < -pd.Timedelta(hours=1)][
            "timestamp"
        ]

        for start, end in zip(period_starts, period_ends):
            period = {
                "start": start,
                "end": end,
                "duration_hours": (end - start).total_seconds() / 3600,
                "period": f"{start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}",
            }
            zero_periods.append(period)

    return {"weekly_stats": weekly_stats, "zero_periods": zero_periods}
