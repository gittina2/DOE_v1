# Experiment Report: fullfact_leardinew

## Experiment Overview

| Property | Value |
| --- | --- |
| **Experiment ID** | b727a64a-efde-4dc1-b8a4-0260ca2c254c |
| **Name** | fullfact_leardinew |
| **Design Type** | full_factorial |
| **Description** | N/A |
| **Schema Version** | 1.1 |
| **Current Workflow Step** | analysis_created |

## Factors & Responses

### Experimental Factors

| Factor Name | Type | Unit | Bounds / Levels |
| --- | --- | --- | --- |
| A | continuous | g | [9.0, 11.0] |
| B | continuous | g | [3.6, 4.4] |
| C | continuous | g | [9.0, 11.0] |

### Response Variables

| Response Name | Type | Unit |
| --- | --- | --- |
| viscosity | continuous | N/A |

## Experimental Design

- **Design ID**: 0ee6c384-f434-4b5e-97f3-79e556ea4584
- **Design Type**: full_factorial
- **Total Runs**: 8
- **Randomization**: False

| Run ID | Run Number | A | B | C |
| --- | --- | --- | --- | --- |
| 3692bd49-100a-4e9b-9294-443e661c8590 | 1 | 9.0 | 3.6 | 9.0 |
| d895216a-1416-4e2b-93ae-b0aeecf5cbcd | 2 | 9.0 | 3.6 | 11.0 |
| 7d5118c7-b33d-4ecc-97bd-09e599f88213 | 3 | 9.0 | 4.4 | 9.0 |
| deb2dc5d-f7da-4c4b-bd90-317e6938d8ec | 4 | 9.0 | 4.4 | 11.0 |
| 528cec49-b7a4-4e67-adb4-6040eb6bb299 | 5 | 11.0 | 3.6 | 9.0 |
| 90c72e1d-a95a-40dd-ae34-b2cfa52f8c16 | 6 | 11.0 | 3.6 | 11.0 |
| 5b709b8c-5524-4507-9f9c-0306b187e28e | 7 | 11.0 | 4.4 | 9.0 |
| 54503402-ab39-4bd0-9364-ca6b6c01f550 | 8 | 11.0 | 4.4 | 11.0 |

## Experimental Results

- **Results ID**: res_22ef41a9
- **Completeness**: complete
- **Recorded Entries**: 8

| Run Reference | viscosity | Status |
| --- | --- | --- |
| 3692bd49-100a-4e9b-9294-443e661c8590 | 51.8 | complete |
| d895216a-1416-4e2b-93ae-b0aeecf5cbcd | 50.2 | complete |
| 7d5118c7-b33d-4ecc-97bd-09e599f88213 | 51 | complete |
| deb2dc5d-f7da-4c4b-bd90-317e6938d8ec | 52 | complete |
| 528cec49-b7a4-4e67-adb4-6040eb6bb299 | 51.6 | complete |
| 90c72e1d-a95a-40dd-ae34-b2cfa52f8c16 | 46.6 | complete |
| 5b709b8c-5524-4507-9f9c-0306b187e28e | 42.4 | complete |
| 54503402-ab39-4bd0-9364-ca6b6c01f550 | 50 | complete |

## Statistical Analysis

- **Analysis ID**: ana_62150c84
- **Model Type**: interaction
- **R²**: 0.839208
- **Adjusted R²**: 0.0

### Coefficients

| Term | Estimate | P-Value |
| --- | --- | --- |
| Intercept | 49.45 | 0.016089 |
| A | -1.8 | 0.38642 |
| B | -0.6 | 0.7151 |
| C | 0.25 | 0.874334 |
| A:B | -0.85 | 0.619826 |
| A:C | 0.4 | 0.802837 |
| B:C | 1.9 | 0.370452 |

### ANOVA Table

| Source | Sum of Squares (SS) | DF | Mean Square (MS) | F-Value | P-Value |
| --- | --- | --- | --- | --- | --- |
| Model | 65.24 | 6 | 10.873333 | 0.869867 | 0.675148 |
| Residuals | 12.5 | 1 | 12.5 | N/A | N/A |
| Total | 77.74 | 7 | N/A | N/A | N/A |
