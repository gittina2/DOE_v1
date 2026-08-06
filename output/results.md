# Experiment Report: fullfact1

## Experiment Overview

| Property | Value |
| --- | --- |
| **Experiment ID** | f4f659ac-14da-4aa6-8e4b-093b7499a1b7 |
| **Name** | fullfact1 |
| **Design Type** | full_factorial |
| **Description** | N/A |
| **Schema Version** | 1.0 |
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

- **Design ID**: 980b413b-5793-4074-9803-73536a67f759
- **Design Type**: full_factorial
- **Total Runs**: 4
- **Randomization**: False

| Run ID | Run Number | T | conc_base |
| --- | --- | --- | --- |
| d3a46762-ca01-48bc-9250-cc8b5b8577cd | 1 | 20.0 | 1.0 |
| dbb61fe3-9497-4dba-8332-38568a9d0892 | 2 | 20.0 | 2.0 |
| 5e81c244-aef7-4af9-82df-917cd68f28a6 | 3 | 60.0 | 1.0 |
| 3c15e7a0-6699-4800-a2c0-4e4bcd5af3c2 | 4 | 60.0 | 2.0 |

## Experimental Results

- **Results ID**: res_4a3b8922
- **Completeness**: complete
- **Recorded Entries**: 4

| Run Reference | resa | Status |
| --- | --- | --- |
| d3a46762-ca01-48bc-9250-cc8b5b8577cd | 10 | complete |
| dbb61fe3-9497-4dba-8332-38568a9d0892 | 2 | complete |
| 5e81c244-aef7-4af9-82df-917cd68f28a6 | 5 | complete |
| 3c15e7a0-6699-4800-a2c0-4e4bcd5af3c2 | 3 | complete |

## Statistical Analysis

- **Analysis ID**: ana_71822844
- **Model Type**: linear
- **R²**: 0.763158
- **Adjusted R²**: 0.289474

### Coefficients

| Term | Estimate | P-Value |
| --- | --- | --- |
| Intercept | 14.5 | 0.235109 |
| T | -0.05 | 0.625666 |
| conc_base | -5.0 | 0.344042 |

### ANOVA Table

| Source | Sum of Squares (SS) | DF | Mean Square (MS) | F-Value | P-Value |
| --- | --- | --- | --- | --- | --- |
| Model | 29.0 | 2 | 14.5 | 1.611111 | 0.486664 |
| Residuals | 9.0 | 1 | 9.0 | N/A | N/A |
| Total | 38.0 | 3 | N/A | N/A | N/A |
