# Project Limitations (Review 1 Scope Boundary)

This document explicitly outlines the technical boundaries and limitations of the **45% Review 1 Prototype** of the Multi-Location Balancing Recommender.

## 1. Scope & Technical Limitations
1. **Synthetic Data**: The prototype uses python-generated synthetic datasets (`data_generator.py`) to demonstrate supply chain scenarios reproducibly without relying on proprietary enterprise data.
2. **No Real ERP Integration**: Data is stored and manipulated via standard CSV files (`pandas`) rather than direct connections to SAP, Oracle, or Microsoft Dynamics ERP systems.
3. **Static Transport Matrix**: Transfer lead times and per-unit freight costs between locations are statically defined in `transfers.csv` rather than dynamically updated via live logistics APIs (e.g. FedEx, DHL, or GPS trackers).
4. **Deterministic Shortage Rules**: Shortages are evaluated on a 7-day rolling horizon using rule-based formulas rather than multi-echelon stochastic optimization models.
5. **Human Decision Support**: The system generates actionable decision recommendations and requires manual planner confirmation or override logging rather than automatically issuing purchase orders or logistics dispatch commands.

## 2. Planned Future Work (Post-Review 1)
- **55%+**: Advanced demand forecasting integration (ARIMA/Prophet).
- **65%+**: Multi-objective MILP linear optimization for complex network routing.
- **75%+**: Live streaming data pipelines and WebSockets integration.
- **85%+**: ERP REST API connectors (SAP/NetSuite).
- **90%+**: CO2 emissions modeling and carrier reliability analytics.
- **100%**: Enterprise production deployment with OAuth2 security.
