def estimate_soh(cycles, throughput_mwh, avg_soc=50, temp=20):
    cycle_loss = cycles * 0.02
    soc_penalty = max(0, (avg_soc - 50) * 0.005)
    temp_factor = 1 + max(0, (temp - 25) * 0.02)
    degradation = (cycle_loss + soc_penalty) * temp_factor
    soh = max(0, 100 - degradation)
    return soh
