# Experiment Report: fullfact1_new

## Experiment Overview

| Property | Value |
| --- | --- |
| **Experiment ID** | 82b6cb2c-043f-4027-850a-e0f807abc67f |
| **Name** | fullfact1_new |
| **Design Type** | full_factorial |
| **Description** | N/A |
| **Schema Version** | 1.1 |
| **Current Workflow Step** | analysis_created |

## Factors & Responses

### Experimental Factors

| Factor Name | Type | Unit | Bounds / Levels |
| --- | --- | --- | --- |
| T | continuous | C | [20.0, 60.0] |
| conc_base | continuous | N/A | [1.0, 2.0] |

### Response Variables

| Response Name | Type | Unit |
| --- | --- | --- |
| resa | continuous | N/A |

## Experimental Design

- **Design ID**: 9a9ee39d-346b-46cc-ba07-ff52fc34c159
- **Design Type**: full_factorial
- **Total Runs**: 4
- **Randomization**: False

| Run ID | Run Number | T | conc_base |
| --- | --- | --- | --- |
| 1f02320c-0f4a-485d-b629-18b1e611b96f | 1 | 20.0 | 1.0 |
| 2b159816-fd40-45d4-ac3c-be61f604fe11 | 2 | 20.0 | 2.0 |
| 1c8de4a9-af8a-4952-b8ef-a08f4fc170d9 | 3 | 60.0 | 1.0 |
| c9c1de28-41b3-4665-9f88-5d0d7346f961 | 4 | 60.0 | 2.0 |

## Experimental Results

- **Results ID**: res_c504907a
- **Completeness**: complete
- **Recorded Entries**: 4

| Run Reference | resa | Status |
| --- | --- | --- |
| 1f02320c-0f4a-485d-b629-18b1e611b96f | 10 | complete |
| 2b159816-fd40-45d4-ac3c-be61f604fe11 | 2 | complete |
| 1c8de4a9-af8a-4952-b8ef-a08f4fc170d9 | 5 | complete |
| c9c1de28-41b3-4665-9f88-5d0d7346f961 | 3 | complete |

## Statistical Analysis

- **Analysis ID**: ana_18e28299
- **Model Type**: linear
- **R²**: 0.763158
- **Adjusted R²**: 0.289474

### Coefficients

| Term | Estimate | P-Value |
| --- | --- | --- |
| Intercept | 5.0 | 0.185547 |
| T | -1.0 | 0.625666 |
| conc_base | -2.5 | 0.344042 |

### ANOVA Table

| Source | Sum of Squares (SS) | DF | Mean Square (MS) | F-Value | P-Value |
| --- | --- | --- | --- | --- | --- |
| Model | 29.0 | 2 | 14.5 | 1.611111 | 0.486664 |
| Residuals | 9.0 | 1 | 9.0 | N/A | N/A |
| Total | 38.0 | 3 | N/A | N/A | N/A |
