from dataclasses import dataclass

@dataclass
class YearProjection:
    year: int
    cm_revenue: float
    eso_revenue: float
    fr_arb_revenue: float
    bm_revenue: float
    network_costs: float
    degradation_cost: float

    @property
    def net(self):
        return (self.cm_revenue + self.eso_revenue + self.fr_arb_revenue +
                self.bm_revenue - self.network_costs - self.degradation_cost)

def project_10_years(
    start_year: int,
    capacity_kw: float,
    cm_price: float,
    eso_revenue_year1: float,
    fr_arb_year1: float,
    bm_year1: float,
    network_costs_year1: float,
    soh0: float = 100.0,
):
    projections = []
    soh = soh0
    cm = capacity_kw * cm_price
    eso = eso_revenue_year1
    frarb = fr_arb_year1
    bm = bm_year1
    netcost = network_costs_year1

    for i in range(10):
        year = start_year + i
        degradation_cost = max(0, (100 - soh) * 50)
        proj = YearProjection(
            year=year,
            cm_revenue=cm,
            eso_revenue=eso,
            fr_arb_revenue=frarb,
            bm_revenue=bm,
            network_costs=netcost,
            degradation_cost=degradation_cost,
        )
        projections.append(proj)
        cm *= 1.01
        eso *= 1.01
        frarb *= 1.01
        bm *= 1.01
        netcost *= 1.005
        soh -= 2
    return projections
