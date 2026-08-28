# Experiment Report: fullfact1_new

## Experiment Overview

| Property | Value |
| --- | --- |
| **Experiment ID** | 942cf2c2-0d3b-48c6-ae6c-091616fc0f6c |
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

- **Design ID**: d786185a-7ccd-4621-8645-d5d443001b9e
- **Design Type**: full_factorial
- **Total Runs**: 4
- **Randomization**: False

| Run ID | Run Number | T | conc_base |
| --- | --- | --- | --- |
| 247ad4db-57e5-4d6a-bb11-b10dbcb308f1 | 1 | 20.0 | 1.0 |
| 40c42c34-3798-4b8a-90b2-f8cb73428049 | 2 | 20.0 | 2.0 |
| 3bae9d97-1ddb-4086-8c84-acb026a2a7ef | 3 | 60.0 | 1.0 |
| 3c1d0c77-a69e-4077-be58-72b63c43e171 | 4 | 60.0 | 2.0 |

## Experimental Results

- **Results ID**: res_6f8882d0
- **Completeness**: complete
- **Recorded Entries**: 4

| Run Reference | resa | Status |
| --- | --- | --- |
| 247ad4db-57e5-4d6a-bb11-b10dbcb308f1 | 10 | complete |
| 40c42c34-3798-4b8a-90b2-f8cb73428049 | 2 | complete |
| 3bae9d97-1ddb-4086-8c84-acb026a2a7ef | 5 | complete |
| 3c1d0c77-a69e-4077-be58-72b63c43e171 | 3 | complete |

## Statistical Analysis

- **Analysis ID**: ana_46f50bc9
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
